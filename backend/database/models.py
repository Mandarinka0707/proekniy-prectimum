# database/models.py
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    preferred_role = Column(String(50), default="Не выбрана")
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # type: ignore
    
    # Связи
    chat_messages = relationship("ChatMessage", back_populates="user")
    moods = relationship("Mood", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")  # Добавьте эту строку

class Prompt(Base):
    __tablename__ = "prompts"
    
    id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(50), unique=True, index=True, nullable=False)
    system_instruction = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # type: ignore

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    role = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # type: ignore
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # type: ignore
    
    # Связи
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)  # Изменено с True на False
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    is_user = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связи
    user = relationship("User", back_populates="chat_messages")
    session = relationship("ChatSession", back_populates="messages")

class Mood(Base):
    __tablename__ = "moods"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    mood_value = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # type: ignore
    
    # Связи
    user = relationship("User", back_populates="moods")