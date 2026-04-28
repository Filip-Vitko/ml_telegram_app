import os
from datetime import datetime
from typing import Literal, Optional
from zoneinfo import ZoneInfo
from enum import Enum

from sqlmodel import Field, Session, SQLModel, create_engine, select

UTC = ZoneInfo("UTC")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@db:5432/app_db",
)

class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

    @classmethod
    def from_str(cls, value: str) -> "MessageRole":
        if value.lower() == "system":
            return cls.SYSTEM
        elif value.lower() == "user":
            return cls.USER
        elif value.lower() == "assistant":
            return cls.ASSISTANT

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
    role: MessageRole
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

engine = create_engine(DATABASE_URL)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

def create_conversation(data: ConversationCreate, session: Session):
    conversation = Conversation.model_validate(data)
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return conversation

def list_conversations(session: Session, offset: int = 0, limit: int = 100):
    return session.exec(
        select(Conversation)
        .order_by(Conversation.created_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()

def get_latest_conversation_for_user(session: Session, user_id: str):
    return session.exec(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.created_at.desc())
    ).first()

def get_or_create_conversation(session: Session, user_id: str):
    conversation = get_latest_conversation_for_user(session, user_id)
    if conversation:
        return conversation
    return create_conversation(ConversationCreate(user_id=user_id), session)

def create_message(data: MessageCreate, session: Session):
    message = Message.model_validate(data)
    session.add(message)
    session.commit()
    session.refresh(message)
    return message

def list_messages_for_conversation(
    session: Session,
    conversation_id: int,
    offset: int = 0,
    limit: int = 100,
):
    return session.exec(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .offset(offset)
        .limit(limit)
    ).all()