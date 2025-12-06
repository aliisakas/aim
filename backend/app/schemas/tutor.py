"""
Схемы для AI-репетиторов
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TutorBase(BaseModel):
    """Базовые поля репетитора"""
    name: str
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    category: Optional[str] = None


class TutorResponse(TutorBase):
    """
    Полная информация о репетиторе для фронтенда.
    GET /api/tutors возвращает список таких объектов
    """
    id: int
    course_id: int
    rating: float
    total_feedbacks: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
    
    # Пример JSON:
    # {
    #   "id": 1,
    #   "name": "Python для начинающих",
    #   "description": "Изучите основы Python",
    #   "avatar_url": "/avatars/python.png",
    #   "category": "Программирование",
    #   "rating": 4.8,
    #   "total_feedbacks": 120,
    #   "is_active": true
    # }


class TutorListResponse(BaseModel):
    """Список репетиторов с пагинацией"""
    tutors: list[TutorResponse]
    total: int
    page: int
    page_size: int
