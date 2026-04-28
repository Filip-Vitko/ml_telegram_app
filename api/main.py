import os
import httpx
import uvicorn

from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session

from database import (
    Conversation,
    Message,
    MessageCreate,
    create_db_and_tables,
    create_message,
    engine,
    get_or_create_conversation,
    get_session,
    list_conversations,
    list_messages_for_conversation,
)

LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://llm_service:8000")
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "12"))

SYSTEM_MESSAGE = (
    "You are a helpful assistant in a Telegram chat. Use the conversation history "
    "to answer naturally and consistently."
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield
    engine.dispose()


app = FastAPI(lifespan=lifespan)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=255)
    prompt: str = Field(min_length=1, max_length=10000)


class ChatResponse(BaseModel):
    conversation_id: int
    model: str
    response: str
    done: bool


def build_model_messages(history: list[Message], latest_prompt: str) -> list[dict[str, str]]:
    messages = [{"role": "system", "content": SYSTEM_MESSAGE}]
    messages.extend({"role": message.role, "content": message.content} for message in history)
    messages.append({"role": "user", "content": latest_prompt})
    return messages

async def get_first_available_model():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{LLM_SERVICE_URL}/models")
            resp.raise_for_status()
            data = resp.json()
            models = data.get("models", [])
            if not models:
                raise HTTPException(status_code=503, detail="No models available")
            return models[0]
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Failed to get models: {e}")

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/models")
async def get_models():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{LLM_SERVICE_URL}/models")
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Failed to get models: {e}")

@app.get("/conversations", response_model=list[Conversation])
def read_conversations(
    offset: int = 0,
    limit: int = Query(default=100, ge=1, le=100),
    session: Session = Depends(get_session),
):
    return list_conversations(session, offset=offset, limit=limit)


@app.get("/conversations/{conversation_id}/messages", response_model=list[Message])
def read_conversation_messages(
    conversation_id: int,
    offset: int = 0,
    limit: int = Query(default=100, ge=1, le=100),
    session: Session = Depends(get_session),
):
    return list_messages_for_conversation(
        session,
        conversation_id=conversation_id,
        offset=offset,
        limit=limit,
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, session: Session = Depends(get_session)):
    timeout = httpx.Timeout(connect=10.0, read=300.0, write=30.0, pool=10.0)
    conversation = get_or_create_conversation(session, request.user_id)
    history = list_messages_for_conversation(
        session,
        conversation_id=conversation.id,
        limit=MAX_HISTORY_MESSAGES,
    )
    model_messages = build_model_messages(history, request.prompt)

    model_name = await get_first_available_model()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{LLM_SERVICE_URL}/chat",
                json={
                    "model": model_name,
                    "messages": model_messages,
                }
            )
            resp.raise_for_status()
            result = resp.json()
            assistant_message = result.get("message", {})
            response_text = assistant_message.get("content", "").strip()

            create_message(
                MessageCreate(
                    conversation_id=conversation.id,
                    role="user",
                    content=request.prompt,
                ),
                session,
            )
            create_message(
                MessageCreate(
                    conversation_id=conversation.id,
                    role="assistant",
                    content=response_text,
                ),
                session,
            )

            return ChatResponse(
                conversation_id=conversation.id,
                model=model_name,
                response=response_text,
                done=result.get("done", False),
            )
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Failed to generate response: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)