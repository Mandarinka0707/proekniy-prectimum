import os
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole  # Правильные импорты
from sqlalchemy.orm import Session
from database.models import Prompt, ChatMessage

class AIService:
    @staticmethod
    async def get_reply(user_id: int, message: str, role: str, db: Session):
        # 1. Получаем системную инструкцию для роли
        prompt = db.query(Prompt).filter(Prompt.role_name == role).first()
        
        if not prompt:
            system_instruction = "Ты полезный AI-ассистент для помощи в отношениях. Отвечай дружелюбно и профессионально."
        else:
            system_instruction = prompt.system_instruction
        
        # 2. Получаем историю (последние 10 сообщений)
        history = db.query(ChatMessage).filter(
            ChatMessage.user_id == user_id,
            ChatMessage.role == role
        ).order_by(ChatMessage.created_at.desc()).limit(10).all()
        
        # 3. Формируем сообщения для GigaChat (используя Messages, а не Message)
        messages = []
        
        # Добавляем системное сообщение
        messages.append(Messages(role=MessagesRole.SYSTEM, content=system_instruction))
        
        # Добавляем историю в правильном порядке
        for hist_msg in reversed(history):
            if hist_msg.is_user:
                messages.append(Messages(role=MessagesRole.USER, content=hist_msg.message))
            else:
                messages.append(Messages(role=MessagesRole.ASSISTANT, content=hist_msg.message))
        
        # Добавляем текущее сообщение пользователя
        messages.append(Messages(role=MessagesRole.USER, content=message))
        
        # 4. Сохраняем сообщение пользователя в БД
        user_msg = ChatMessage(
            user_id=user_id,
            role=role,
            message=message,
            is_user=True
        )
        db.add(user_msg)
        db.commit()
        
        try:
            # 5. Запрос к GigaChat с правильным объектом Chat
            with GigaChat(
                credentials=os.getenv("GIGACHAT_CREDENTIALS"),
                verify_ssl_certs=False,
                timeout=30
            ) as giga:
                # Создаем объект Chat и передаем его
                chat_payload = Chat(messages=messages)
                response = giga.chat(chat_payload)
                reply = response.choices[0].message.content
            
            # 6. Сохраняем ответ AI
            ai_msg = ChatMessage(
                user_id=user_id,
                role=role,
                message=reply,
                is_user=False
            )
            db.add(ai_msg)
            db.commit()
            
            return reply
            
        except Exception as e:
            print(f"GigaChat error: {e}")
            db.rollback()
            
            # 7. Fallback ответ в случае ошибки
            fallback_reply = f"**{role}**: Извините, произошла техническая ошибка. Пожалуйста, попробуйте позже."
            
            ai_msg = ChatMessage(
                user_id=user_id,
                role=role,
                message=fallback_reply,
                is_user=False
            )
            db.add(ai_msg)
            db.commit()
            
            return fallback_reply