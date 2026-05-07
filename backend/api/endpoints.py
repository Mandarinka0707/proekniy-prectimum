from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List

# Импорты из твоих папок
from database.database import get_db
from database import schemas, models
from services.ai_service import AIService
from services.user_service import UserService
import security

router = APIRouter()

# Настройка "Замка" в Swagger: теперь это просто поле для вставки токена
security_scheme = HTTPBearer()

# --- ФУНКЦИЯ-ПРОВЕРКА АВТОРИЗАЦИИ (Dependency) ---

def get_current_user(
    auth: HTTPAuthorizationCredentials = Depends(security_scheme), 
    db: Session = Depends(get_db)
):
    """
    Вытаскивает токен из заголовка, расшифровывает его и находит пользователя в базе.
    """
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

# --- ПУБЛИЧНЫЕ ЭНДПОИНТЫ (Без замка) ---

@router.post("/register", status_code=201)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Регистрация нового пользователя.
    """
    # Проверка на уникальность email
    existing_user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Этот email уже зарегистрирован")
    
    user = UserService.create_user(db, user_data)
    return {"status": "success", "user_id": user.id}

@router.post("/login")
def login(data: schemas.UserLogin, db: Session = Depends(get_db)):
    """
    Вход в систему. Возвращает JWT токен.
    """
    user = db.query(models.User).filter(models.User.email == data.email).first()
    
    if not user or not security.verify_password(data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Неверная почта или пароль"
        )
    
    # Создаем токен, зашифровывая в него email
    token = security.create_access_token(data={"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

# --- ЗАЩИЩЕННЫЕ ЭНДПОИНТЫ (Нужен токен) ---

@router.post("/chat")
async def chat(
    data: schemas.ChatRequestOnlyMessage, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Отправка сообщения в чат. user_id берется автоматически из токена.
    """
    # AIService сам найдет системную инструкцию по role_name и сохранит историю
    reply = await AIService.get_reply(
        user_id=current_user.id, 
        message=data.user_message, 
        role=data.role_name, 
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
    С
    """
    # Принудительно привязываем оценку к текущему авторизованному пользователю
    data.user_id = current_user.id
    return UserService.save_mood(db, data)

@router.get("/user/me", response_model=schemas.UserCreate) # Можно создать отдельную схему UserOut
def get_me(current_user: models.User = Depends(get_current_user)):
    """
    Получение данных о текущем пользователе (для профиля).
    """
    return current_user