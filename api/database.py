from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import Depends,FastAPI, HTTPException, Query
from sqlmodel import create_engine, Field, Session, select, SQLModel
from typing import Annotated, Literal, Optional
from zoneinfo import ZoneInfo

UTC = ZoneInfo("UTC")

class Conversation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    # TODO: summary: Optional[str] = None
    # TODO: last_message_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    title: Optional[str] = None

class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(index=True, foreign_key="conversation.id")
    role: Literal["system", "user", "assistant"]
    content: str
    # TODO: token_count
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

class ConversationCreate(SQLModel):
    user_id: str
    title: Optional[str] = None

class MessageCreate(SQLModel):
    conversation_id: int
    role: Literal["system", "user", "assistant"]
    content: str = Field(max_length=10000)

    
postgresql_url = "postgresql://postgres:postgres@db:5432/app_db"

engine = create_engine(postgresql_url)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield
    engine.dispose()

app = FastAPI(lifespan=lifespan)    

@app.post("/conversations", response_model=Conversation)
def create_conversation(data: ConversationCreate, session: SessionDep):
    conversation = Conversation.model_validate(data)
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return conversation  

@app.get("/conversations", response_model=list[Conversation])
def read_conversations(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
):
    conversations = session.exec(select(Conversation).order_by(Conversation.created_at.desc()).offset(offset).limit(limit)).all()
    return conversations

@app.post("/messages", response_model=Message)
def create_message(data: MessageCreate, session: SessionDep):
    conversation = session.get(Conversation, data.conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    message = Message.model_validate(data)
    session.add(message)
    session.commit()
    session.refresh(message)
    return message

@app.get("/conversations/{conversation_id}/messages", response_model=list[Message])
def read_conversation_messages(
    conversation_id: int,
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
):
    messages = session.exec(select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.asc()).offset(offset).limit(limit)).all()
    return messages