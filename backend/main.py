from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.endpoints import router as api_router
from database.database import engine
from database.models import Base

# Создаем все таблицы при старте
Base.metadata.create_all(bind=engine)

app = FastAPI(title="HeartMind Professional API")

# Настройка CORS - перенесено сюда из endpoints.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500", 
        "http://127.0.0.1:5500",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутер
app.include_router(api_router)

@app.get("/")
def root():
    return {"message": "HeartMind API is running"}