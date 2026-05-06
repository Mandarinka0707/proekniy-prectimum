from sqlalchemy.orm import Session
from database.models import User, MoodLog
# Добавляем импорт MoodSave и UserCreate из наших схем
from database.schemas import UserCreate, MoodSave 
import security

class UserService:
    @staticmethod
    def create_user(db: Session, user_data: UserCreate):
        hashed_pwd = security.get_password_hash(user_data.password)
        new_user = User(
            name=user_data.name,
            email=user_data.email,
            password=hashed_pwd,
            preferred_role=user_data.role
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def save_mood(db: Session, data: MoodSave):
        # Логика сохранения настроения
        if data.stage == "before":
            log = MoodLog(
                user_id=data.user_id, 
                score_before=data.score, 
                note_before=data.note
            )
            db.add(log)
        else:
            # Ищем последнюю запись пользователя, чтобы обновить её (оценка "после")
            log = db.query(MoodLog).filter(MoodLog.user_id == data.user_id)\
                    .order_by(MoodLog.created_at.desc()).first()
            if log:
                log.score_after = data.score
                log.note_after = data.note
        
        db.commit()
        return {"status": "success"}