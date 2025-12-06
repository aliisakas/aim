"""
Схемы для чатов
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.schemas.tutor import TutorResponse


class ChatCreate(BaseModel):
    """
    Создание нового чата с репетитором.
    POST /api/chats
    """
    tutor_id: int
    
    # Пример JSON от фронтенда:
    # { "tutor_id": 1 }


class ChatResponse(BaseModel):
    """
    Информация о чате для фронтенда.
    Включает информацию о репетиторе
    """
    id: int
    user_id: int
    tutor_id: int
    custom_name: Optional[str] = None
    last_message_at: Optional[datetime] = None
    created_at: datetime
    
    # Вложенный объект с данными репетитора
    tutor: TutorResponse
    
    # Дополнительные поля (вычисляемые)
    last_message: Optional[str] = None  # Последнее сообщение
    unread_count: int = 0  # Количество непрочитанных
    
    class Config:
        from_attributes = True


class ChatUpdate(BaseModel):
    """
    Обновление настроек чата.
    PATCH /api/chats/{chat_id}
    """
    custom_name: Optional[str] = None
    
    # Пример JSON:
    # { "custom_name": "Мой Python курс" }


class ChatListResponse(BaseModel):
    """Список всех чатов пользователя"""
    chats: list[ChatResponse]
    total: int
