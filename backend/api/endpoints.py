# api/endpoints.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy.sql import func

# Импорты из твоих папок
from database.database import get_db
from database import schemas, models
from services.ai_service import AIService
from services.user_service import UserService
import security

router = APIRouter()

# Настройка "Замка" в Swagger
security_scheme = HTTPBearer()

# --- ФУНКЦИЯ-ПРОВЕРКА АВТОРИЗАЦИИ ---
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
    # Используем роль из запроса
    role_name = data.role_name if data.role_name else current_user.preferred_role or "Не выбрана"
    
    # Проверяем, существует ли такая роль в таблице prompts
    from database.models import Prompt  # Импорт здесь, чтобы избежать циклической зависимости
    prompt = db.query(Prompt).filter(Prompt.role_name == role_name).first()
    
    if not prompt and role_name != "Не выбрана":
        # Если роли нет, используем дефолтную
        role_name = "Не выбрана"
        print(f"Role '{data.role_name}' not found in prompts, using default")
    
    # Получаем ответ от AI
    reply = await AIService.get_reply(
        user_id=current_user.id, 
        message=data.user_message, 
        role=role_name, 
        db=db
    )
    
    return {"reply": reply}

@router.post("/mood/log")
def log_mood(
    data: schemas.MoodSave, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Сохранение настроения пользователя
    """
    return UserService.save_mood(db, data, current_user.id)

@router.get("/user/me")
def get_me(current_user: models.User = Depends(get_current_user)):
    """
    Получение данных текущего пользователя
    """
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "preferred_role": current_user.preferred_role,
        "created_at": current_user.created_at
    }

# api/endpoints.py - добавьте эти эндпоинты

from database import schemas
from typing import List

# Получить все чаты пользователя
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

# Создать новый чат
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

# Получить историю сообщений чата
@router.get("/chats/{chat_id}/messages", response_model=List[schemas.ChatMessageOut])
def get_chat_messages(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Получить все сообщения чата"""
    # Проверяем, что чат принадлежит пользователю
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

# Сохранить сообщение в чат
@router.post("/chats/{chat_id}/messages")
def save_message(
    chat_id: int,
    message_data: schemas.ChatRequestOnlyMessage,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Сохранить сообщение в чат (для синхронизации)"""
    # Проверяем доступ к чату
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