# services/user_service.py
from sqlalchemy.orm import Session
from database.models import User, Mood
from database import schemas
import security

class UserService:
    @staticmethod
    def create_user(db: Session, user_data: schemas.UserCreate):
        """Создание нового пользователя"""
        # Проверяем длину пароля
        if len(user_data.password.encode('utf-8')) > 72:
            raise ValueError("Пароль слишком длинный (максимум 72 символа)")
        
        hashed_pwd = security.get_password_hash(user_data.password)
        
        db_user = User(
            name=user_data.name,
            email=user_data.email,
            password=hashed_pwd,
            preferred_role=user_data.preferred_role if hasattr(user_data, 'preferred_role') else "Не выбрана"
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def get_user_by_email(db: Session, email: str):
        """Получение пользователя по email"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def save_mood(db: Session, mood_data: schemas.MoodSave, user_id: int):
        """Сохранение настроения"""
        db_mood = Mood(
            user_id=user_id,
            mood_value=mood_data.mood_value
        )
        db.add(db_mood)
        db.commit()
        db.refresh(db_mood)
        return db_mood