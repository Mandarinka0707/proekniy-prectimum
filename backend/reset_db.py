# reset_db.py
from database.database import engine
from database import models
from sqlalchemy import text

def reset_database():
    print("🗑 Удаляем все таблицы...")
    
    with engine.connect() as conn:
        with conn.begin():
            # Для PostgreSQL: отключаем проверки внешних ключей
            try:
                conn.execute(text("SET session_replication_role = replica;"))
            except:
                pass
            
            # Удаляем таблицы в правильном порядке (сначала зависимые)
            tables_to_drop = [
                "chat_messages",
                "chat_sessions", 
                "moods",
                "prompts",
                "users"
            ]
            
            for table in tables_to_drop:
                try:
                    conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
                    print(f"  ✓ Удалена таблица: {table}")
                except Exception as e:
                    print(f"  ⚠ Не удалось удалить {table}: {e}")
            
            # Возвращаем проверки обратно
            try:
                conn.execute(text("SET session_replication_role = DEFAULT;"))
            except:
                pass
    
    print("✅ Все таблицы удалены")
    
    print("📦 Создаем таблицы заново...")
    models.Base.metadata.create_all(bind=engine)
    print("✅ Таблицы созданы")
    
    # Проверяем созданные таблицы
    with engine.connect() as conn:
        result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public';"))
        tables = [row[0] for row in result]
        print(f"\n📋 Созданные таблицы: {', '.join(tables)}")

if __name__ == "__main__":
    reset_database()