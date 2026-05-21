import os
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
from sqlalchemy.orm import Session
from database.models import Prompt, ChatMessage

class AIService:
    @staticmethod
    async def get_reply(user_id: int, session_id: int, message: str, role: str, db: Session):
        # 1. Получаем системную инструкцию для роли
        prompt = db.query(Prompt).filter(Prompt.role_name == role).first()
        
        if not prompt:
            system_instruction = "Ты полезный AI-ассистент для помощи в отношениях. Отвечай дружелюбно и профессионально."
        else:
            system_instruction = prompt.system_instruction
        
        # 2. Получаем историю этого чата (последние 10 сообщений)
        history = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id,
            ChatMessage.user_id == user_id
        ).order_by(ChatMessage.created_at.desc()).limit(10).all()
        
        # 3. Формируем сообщения для GigaChat
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
        
        try:
            # Запрос к GigaChat
            with GigaChat(
                credentials=os.getenv("GIGACHAT_CREDENTIALS"),
                verify_ssl_certs=False,
                timeout=30
            ) as giga:
                chat_payload = Chat(messages=messages)
                response = giga.chat(chat_payload)
                reply = response.choices[0].message.content
            
            return reply
            
        except Exception as e:
            print(f"GigaChat error: {e}")
            # Fallback ответ в случае ошибки
            fallback_reply = f"**{role}**: Извините, произошла техническая ошибка. Пожалуйста, попробуйте позже."
            return fallback_reply