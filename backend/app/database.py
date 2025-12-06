"""
Настройка подключения к базе данных PostgreSQL.
Использует асинхронный движок SQLAlchemy
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings


# === Создание асинхронного движка базы данных ===
engine = create_async_engine(
    settings.database_url,  # Строка подключения из config.py
    echo=True,  # Логирование SQL запросов (отключить в production)
    future=True,  # Использовать SQLAlchemy 2.0 стиль
    pool_size=10,  # Размер пула соединений
    max_overflow=20  # Максимальное количество дополнительных соединений
)

# === Фабрика для создания сессий ===
# Каждый запрос к БД будет использовать свою сессию
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Не сбрасывать объекты после commit
    autoflush=False,
    autocommit=False
)

# === Базовый класс для всех моделей ===
# Все таблицы будут наследоваться от него
Base = declarative_base()


# === Dependency для FastAPI ===
# Эта функция будет вызываться в каждом endpoint для получения сессии БД
async def get_db() -> AsyncSession:
    """
    Создает и возвращает сессию базы данных.
    После завершения запроса автоматически закрывает соединение.
    
    Используется так:
    @app.get("/users")
    async def get_users(db: AsyncSession = Depends(get_db)):
        ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session  # Передаем сессию в endpoint
        finally:
            await session.close()  # Закрываем после использования
