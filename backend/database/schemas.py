from pydantic import BaseModel, EmailStr
from typing import Optional, List

# Схемы для пользователя
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Optional[str] = "Не выбрано"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Схемы для чата
class ChatRequest(BaseModel):
    user_id: int
    user_message: str
    role_name: str

class ChatRequestOnlyMessage(BaseModel):
    user_message: str
    role_name: str

# Схема для настроения
class MoodSave(BaseModel):
    user_id: Optional[int] = None # Мы будем брать его из токена
    score: int
    note: Optional[str] = None
    stage: str # "before" или "after"