from fastapi import FastAPI
from api.endpoints import router as api_router
from database.database import engine
from database.models import Base # Импортируем Base

# Создаем все таблицы при старте
Base.metadata.create_all(bind=engine)

app = FastAPI(title="HeartMind Professional API")
app.include_router(api_router)