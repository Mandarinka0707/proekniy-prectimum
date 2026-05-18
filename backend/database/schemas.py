# database/schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from typing import List

class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72)
    preferred_role: Optional[str] = "Не выбрана"  # Добавьте это поле

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ChatRequestOnlyMessage(BaseModel):
    user_message: str = Field(..., min_length=1, max_length=5000)
    role_name: str
    chat_id: Optional[int] = None 

class ChatSessionCreate(BaseModel):
    title: str
    role: str

class ChatSessionOut(BaseModel):
    id: int
    title: str
    role: str
    created_at: datetime
    updated_at: Optional[datetime]

class ChatMessageOut(BaseModel):
    id: int
    session_id: int
    message: str
    is_user: bool
    created_at: datetime

class ChatHistoryOut(BaseModel):
    session: ChatSessionOut
    messages: List[ChatMessageOut]

class ChatMessageSave(BaseModel):
    message: str
    is_user: bool

class MoodSave(BaseModel):
    mood_value: str  # Радостно, Спокойно, Тревожно, Грустно

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    preferred_role: str
    created_at: datetime