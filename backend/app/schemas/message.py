"""
Схемы для сообщений
"""

from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


class MessageCreate(BaseModel):
    """
    Отправка сообщения в чат.
    POST /api/chats/{chat_id}/messages
    """
    content: str  # Текст сообщения
    attachments: Optional[List[Dict]] = None  # Вложенные файлы
    
    # Пример JSON от фронтенда:
    # {
    #   "content": "Что такое list comprehension?",
    #   "attachments": [
    #     {
    #       "filename": "code.py",
    #       "url": "https://storage.com/files/code.py",
    #       "type": "text/x-python"
    #     }
    #   ]
    # }


class MessageResponse(BaseModel):
    """
    Одно сообщение для фронтенда.
    Может быть от пользователя (role="user") или от AI (role="assistant")
    """
    id: int
    chat_id: int
    role: str  # "user" или "assistant"
    content: str
    attachments: Optional[List[Dict]] = None
    metadata: Optional[Dict] = None  # Доп. данные (токены, время генерации)
    created_at: datetime
    
    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """
    История сообщений чата с пагинацией.
    GET /api/chats/{chat_id}/messages
    """
    messages: List[MessageResponse]
    has_more: bool  # Есть ли еще сообщения (для бесконечного скролла)
    total: int


class ChatMessagePairResponse(BaseModel):
    """
    Ответ после отправки сообщения.
    Включает сообщение пользователя И ответ AI
    """
    user_message: MessageResponse
    ai_response: MessageResponse
    
    # Пример JSON ответа:
    # {
    #   "user_message": {
    #     "id": 10,
    #     "role": "user",
    #     "content": "Объясни циклы",
    #     "created_at": "2025-12-06T15:30:00Z"
    #   },
    #   "ai_response": {
    #     "id": 11,
    #     "role": "assistant",
    #     "content": "Цикл for в Python используется для...",
    #     "created_at": "2025-12-06T15:30:03Z"
    #   }
    # }
