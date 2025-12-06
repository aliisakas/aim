"""
Pydantic схемы для пользователей.
Описывают формат JSON данных для API endpoints
"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


# === СХЕМА ДЛЯ РЕГИСТРАЦИИ ===
class UserCreate(BaseModel):
    """
    Данные для регистрации нового пользователя.
    Фронтенд отправляет POST /api/auth/register с этим JSON
    """
    email: EmailStr  # Валидирует email формат (user@example.com)
    username: str = Field(min_length=3, max_length=50)  # От 3 до 50 символов
    password: str = Field(min_length=8)  # Минимум 8 символов
    full_name: Optional[str] = None  # Необязательное поле
    
    # Пример JSON от фронтенда:
    # {
    #   "email": "student@mail.ru",
    #   "username": "ivanov",
    #   "password": "securepass123",
    #   "full_name": "Иван Иванов"
    # }


# === СХЕМА ДЛЯ ВХОДА ===
class UserLogin(BaseModel):
    """
    Данные для входа в систему.
    Фронтенд отправляет POST /api/auth/login
    """
    username: str
    password: str
    
    # Пример JSON:
    # {
    #   "username": "ivanov",
    #   "password": "securepass123"
    # }


# === СХЕМА ОТВЕТА (что возвращаем фронтенду) ===
class UserResponse(BaseModel):
    """
    Информация о пользователе, которую возвращаем в API.
    НЕ включает пароль (безопасность!)
    """
    id: int
    email: str
    username: str
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        # Позволяет создавать схему из SQLAlchemy модели
        from_attributes = True  # В старых версиях: orm_mode = True
    
    # Пример JSON ответа бэкенда:
    # {
    #   "id": 1,
    #   "email": "student@mail.ru",
    #   "username": "ivanov",
    #   "full_name": "Иван Иванов",
    #   "is_active": true,
    #   "created_at": "2025-12-06T14:30:00Z"
    # }


# === СХЕМА ДЛЯ JWT ТОКЕНА ===
class Token(BaseModel):
    """Ответ после успешного входа"""
    access_token: str  # JWT токен
    token_type: str = "bearer"
    user: UserResponse  # Информация о пользователе
    
    # Пример:
    # {
    #   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    #   "token_type": "bearer",
    #   "user": { ...данные пользователя... }
    # }


# === ДАННЫЕ ИЗ JWT ТОКЕНА ===
class TokenData(BaseModel):
    """Данные, которые хранятся внутри JWT токена"""
    user_id: int
    username: str
