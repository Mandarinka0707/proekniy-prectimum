import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Получаем URL базы данных
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# 1. Создаем "движок" подключения
# Он отвечает за физическое соединение с PostgreSQL
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 2. Создаем фабрику сессий
# Каждое обращение к базе будет идти через отдельную сессию
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Базовый класс для всех моделей
# От него будут наследоваться User, Message и другие в models.py
Base = declarative_base()

# 4. Зависимость (Dependency) для FastAPI
# Она открывает базу при запросе и закрывает её после выполнения
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()