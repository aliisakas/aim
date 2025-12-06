"""
Конфигурация окружения Alembic.
Этот файл связывает Alembic с вашими SQLAlchemy моделями.
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import asyncio
import sys
from pathlib import Path

# === ДОБАВЛЯЕМ ПУТЬ К МОДУЛЮ APP ===
# Получаем путь к корневой папке backend/
backend_path = Path(__file__).resolve().parent.parent
# Добавляем в sys.path чтобы Python нашел модуль app
sys.path.insert(0, str(backend_path))

# === ТЕПЕРЬ ИМПОРТИРУЕМ НАШИ МОДЕЛИ И НАСТРОЙКИ ===
from app.database import Base
from app.config import settings

# Импортируем ВСЕ модели чтобы Alembic их увидел
from app.models import User, Course, Tutor, Chat, Message, Feedback


# === КОНФИГУРАЦИЯ ALEMBIC ===
config = context.config

# Настраиваем логирование
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Указываем метаданные наших моделей
# Alembic будет сравнивать эти модели с БД и генерировать миграции
target_metadata = Base.metadata


# === СТРОКА ПОДКЛЮЧЕНИЯ К БД ===
# Берем из config.py вместо alembic.ini
def get_url():
    """Получает URL БД из настроек приложения"""
    # Для миграций используем синхронный драйвер
    return settings.database_url.replace(
        "postgresql+asyncpg://",
        "postgresql+psycopg2://"
    )


config.set_main_option("sqlalchemy.url", get_url())


# === OFFLINE РЕЖИМ ===
def run_migrations_offline() -> None:
    """
    Запуск миграций в 'offline' режиме.
    Генерирует SQL скрипт без выполнения.
    
    Команда: alembic upgrade head --sql > migration.sql
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# === ONLINE РЕЖИМ (основной) ===
def run_migrations_online() -> None:
    """
    Запуск миграций в 'online' режиме.
    Подключается к БД и выполняет миграции.
    
    Команда: alembic upgrade head
    """
    
    # Создаем движок БД
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


# === ОПРЕДЕЛЯЕМ РЕЖИМ ===
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
