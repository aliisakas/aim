"""
Конфигурация приложения.
Загружает переменные окружения из файла .env
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Класс с настройками приложения.
    Все переменные автоматически загружаются из .env файла
    """
    
    # === Настройки базы данных ===
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "tutor_ai_db"
    DB_USER: str = "postgres"
    DB_PASSWORD: str
    
    # Формирование строки подключения к PostgreSQL
    @property
    def database_url(self) -> str:
        """Асинхронное подключение к PostgreSQL"""
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
    
    # === JWT аутентификация ===
    JWT_SECRET_KEY: str  # Секретный ключ для подписи токенов
    JWT_ALGORITHM: str = "HS256"  # Алгоритм шифрования
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # Срок жизни токена (24 часа)
    
    # === AI Core микросервис ===
    AI_CORE_URL: str = "http://localhost:8001"  # URL API команды Андрея
    
    class Config:
        """Настройки Pydantic"""
        env_file = ".env"  # Откуда читать переменные
        case_sensitive = True  # Учитывать регистр


# Создаем глобальный объект настроек
# Он будет доступен во всех модулях через импорт
settings = Settings()
