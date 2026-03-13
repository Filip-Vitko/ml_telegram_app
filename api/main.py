import uvicorn
import os
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://llm_service:8000")

app = FastAPI()

class ChatRequest(BaseModel):
    prompt: str

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

@app.post("/chat")
async def chat(request: ChatRequest):
    timeout = httpx.Timeout(connect=10.0, read=300.0, write=30.0, pool=10.0)

    model_name = await get_first_available_model()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{LLM_SERVICE_URL}/generate",
                json={
                    "model": model_name,
                    "prompt": request.prompt,
                }
            )
            resp.raise_for_status()
            result = resp.json()

            return {
                "model": model_name,
                "response": result.get("response", ""),
                "done": result.get("done", False),
            }
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Failed to generate response: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)