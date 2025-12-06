"""
Схемы для обратной связи
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class FeedbackCreate(BaseModel):
    """
    Создание детального отзыва.
    POST /api/feedbacks
    """
    chat_id: int
    message_id: Optional[int] = None  # Конкретное сообщение (необязательно)
    feedback_type: str = "detailed"  # "detailed" или "quick_reaction"
    
    # Для детального отзыва
    rating: Optional[int] = Field(None, ge=1, le=5)  # От 1 до 5
    positive_text: Optional[str] = None
    improvement_text: Optional[str] = None
    allow_training: bool = True
    
    # Пример JSON:
    # {
    #   "chat_id": 1,
    #   "message_id": 10,
    #   "rating": 5,
    #   "positive_text": "Отличное объяснение с примерами",
    #   "improvement_text": "Можно добавить больше практики",
    #   "allow_training": true
    # }


class QuickFeedbackCreate(BaseModel):
    """
    Быстрая реакция (кнопки 👍, "объясни проще").
    POST /api/feedbacks/quick
    """
    chat_id: int
    message_id: int
    quick_reaction: str  # "helpful", "explain_simpler", "more_examples", "confused"
    
    # Пример JSON:
    # {
    #   "chat_id": 1,
    #   "message_id": 10,
    #   "quick_reaction": "more_examples"
    # }


class FeedbackResponse(BaseModel):
    """Информация об отзыве"""
    id: int
    chat_id: int
    user_id: int
    tutor_id: int
    feedback_type: str
    rating: Optional[int] = None
    positive_text: Optional[str] = None
    improvement_text: Optional[str] = None
    quick_reaction: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
