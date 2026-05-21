from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy.sql import func

from database.database import get_db
from database import schemas, models
from services.ai_service import AIService
from services.user_service import UserService
import security

router = APIRouter()
security_scheme = HTTPBearer()

def get_current_user(
    auth: HTTPAuthorizationCredentials = Depends(security_scheme), 
    db: Session = Depends(get_db)
):
    token = auth.credentials
    email = security.decode_access_token(token)
    
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Невалидный или просроченный токен"
        )
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Пользователь не найден"
        )
    return user

# --- ПУБЛИЧНЫЕ ЭНДПОИНТЫ ---
@router.post("/register", status_code=201)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Этот email уже зарегистрирован")
    
    user = UserService.create_user(db, user_data)
    return {"status": "success", "user_id": user.id}

@router.post("/login")
def login(data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    
    if not user or not security.verify_password(data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Неверная почта или пароль"
        )
    
    token = security.create_access_token(data={"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

# --- ЗАЩИЩЕННЫЕ ЭНДПОИНТЫ ---
@router.post("/chat")
async def chat(
    data: schemas.ChatRequestOnlyMessage, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Отправка сообщения в чат. Использует выбранную роль AI.
    """
    role_name = data.role_name if data.role_name else current_user.preferred_role or "Не выбрана"
    
    # Проверяем существование роли
    from database.models import Prompt
    prompt = db.query(Prompt).filter(Prompt.role_name == role_name).first()
    
    if not prompt and role_name != "Не выбрана":
        role_name = "Не выбрана"
        print(f"Role '{data.role_name}' not found in prompts, using default")
    
    # Получаем или создаем сессию чата
    chat_session = None
    if data.chat_id:
        chat_session = db.query(models.ChatSession).filter(
            models.ChatSession.id == data.chat_id,
            models.ChatSession.user_id == current_user.id
        ).first()
    
    # Если чат не существует, создаем новый
    if not chat_session:
        existing_chats = db.query(models.ChatSession).filter(
            models.ChatSession.user_id == current_user.id
        ).count()
        
        chat_title = f"Новый чат {existing_chats + 1}"
        chat_session = models.ChatSession(
            user_id=current_user.id,
            title=chat_title,
            role=role_name
        )
        db.add(chat_session)
        db.commit()
        db.refresh(chat_session)
    
    # Обновляем время последнего обновления чата
    chat_session.updated_at = func.now()
    db.commit()
    
    # Сохраняем сообщение пользователя
    user_msg = models.ChatMessage(
        session_id=chat_session.id,
        user_id=current_user.id,
        role=role_name,
        message=data.user_message,
        is_user=True
    )
    db.add(user_msg)
    db.commit()
    
    # Получаем ответ от AI
    reply = await AIService.get_reply(
        user_id=current_user.id,
        session_id=chat_session.id,
        message=data.user_message,
        role=role_name,
        db=db
    )
    
    # Сохраняем ответ AI
    ai_msg = models.ChatMessage(
        session_id=chat_session.id,
        user_id=current_user.id,
        role=role_name,
        message=reply,
        is_user=False
    )
    db.add(ai_msg)
    db.commit()
    
    return {
        "reply": reply,
        "chat_id": chat_session.id,
        "chat_title": chat_session.title
    }

@router.post("/mood/log")
def log_mood(
    data: schemas.MoodSave, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Сохранение настроения пользователя"""
    return UserService.save_mood(db, data, current_user.id)

@router.get("/user/me")
def get_me(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Получение данных текущего пользователя"""
    # Подсчитываем количество сообщений пользователя
    total_messages = db.query(models.ChatMessage).filter(
        models.ChatMessage.user_id == current_user.id
    ).count()
    
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "preferred_role": current_user.preferred_role,
        "created_at": current_user.created_at,
        "total_messages": total_messages
    }

# --- ЭНДПОИНТЫ ДЛЯ ЧАТОВ ---
@router.get("/chats", response_model=List[schemas.ChatSessionOut])
def get_user_chats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Получить все чаты текущего пользователя"""
    chats = db.query(models.ChatSession).filter(
        models.ChatSession.user_id == current_user.id
    ).order_by(models.ChatSession.updated_at.desc()).all()
    return chats

@router.post("/chats", response_model=schemas.ChatSessionOut)
def create_chat(
    chat_data: schemas.ChatSessionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Создать новый чат"""
    new_chat = models.ChatSession(
        user_id=current_user.id,
        title=chat_data.title,
        role=chat_data.role
    )
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    return new_chat

@router.get("/chats/{chat_id}/messages", response_model=List[schemas.ChatMessageOut])
def get_chat_messages(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Получить все сообщения чата"""
    chat = db.query(models.ChatSession).filter(
        models.ChatSession.id == chat_id,
        models.ChatSession.user_id == current_user.id
    ).first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")
    
    messages = db.query(models.ChatMessage).filter(
        models.ChatMessage.session_id == chat_id
    ).order_by(models.ChatMessage.created_at.asc()).all()
    
    return messages

@router.post("/chats/{chat_id}/messages")
def save_message(
    chat_id: int,
    message_data: schemas.ChatRequestOnlyMessage,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Сохранить сообщение в чат"""
    chat = db.query(models.ChatSession).filter(
        models.ChatSession.id == chat_id,
        models.ChatSession.user_id == current_user.id
    ).first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")
    
    # Обновляем время последнего обновления
    chat.updated_at = func.now()
    
    # Сохраняем сообщение пользователя
    user_msg = models.ChatMessage(
        session_id=chat_id,
        user_id=current_user.id,
        role=chat.role,
        message=message_data.user_message,
        is_user=True
    )
    db.add(user_msg)
    db.commit()
    
    return {"status": "success"}