import os
from gigachat import GigaChat
from sqlalchemy.orm import Session
from database.models import Prompt, ChatMessage

class AIService:
    @staticmethod
    async def get_reply(user_id: int, message: str, role: str, db: Session):
        # 1. Получаем технику
        prompt = db.query(Prompt).filter(Prompt.role_name == role).first()
        
        # 2. Получаем историю (RAG)
        history = db.query(ChatMessage).filter(ChatMessage.user_id == user_id)\
                    .order_by(ChatMessage.created_at.desc()).limit(5).all()

        # 3. Запрос к GigaChat
        with GigaChat(credentials=os.getenv("GIGACHAT_CREDENTIALS"), verify_ssl_certs=False) as giga:
            msgs = [{"role": "system", "content": prompt.system_instruction}]
            for m in reversed(history):
                msgs.append({"role": m.role, "content": m.content})
            msgs.append({"role": "user", "content": message})
            
            response = giga.chat({"messages": msgs})
            reply = response.choices[0].message.content

        # 4. Сохраняем в базу
        db.add(ChatMessage(user_id=user_id, role="user", content=message))
        db.add(ChatMessage(user_id=user_id, role="assistant", content=reply))
        db.commit()
        return reply