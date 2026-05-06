from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, JSON
import datetime
# Используем относительный импорт, чтобы не запутаться в папках
from .database import Base 

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)
    preferred_role = Column(String, default="Не выбрано")

class Prompt(Base):
    __tablename__ = "prompts"
    id = Column(Integer, primary_key=True)
    role_name = Column(String)
    system_instruction = Column(Text)

class ChatMessage(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class MoodLog(Base):
    __tablename__ = "mood_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    score_before = Column(Integer)
    note_before = Column(Text, nullable=True)
    score_after = Column(Integer)
    note_after = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)