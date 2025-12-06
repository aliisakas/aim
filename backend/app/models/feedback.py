"""
Модель обратной связи (отзывов) от пользователей
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Feedback(Base):
    """
    Таблица отзывов.
    Пользователи оценивают работу AI и дают рекомендации по улучшению
    """
    __tablename__ = "feedbacks"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tutor_id = Column(Integer, ForeignKey("tutors.id", ondelete="CASCADE"), nullable=False)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)
    
    # === Тип отзыва ===
    # "quick_reaction" = быстрая кнопка (👍, "объясни проще")
    # "detailed" = развернутый отзыв с текстом
    feedback_type = Column(String(50), nullable=False)
    
    # === Детальный отзыв ===
    rating = Column(Integer, nullable=True)  # 1-5 звезд
    positive_text = Column(Text, nullable=True)  # Что хорошо
    improvement_text = Column(Text, nullable=True)  # Что улучшить
    
    # === Быстрая реакция ===
    # Варианты: "explain_simpler", "more_examples", "helpful", "confused"
    quick_reaction = Column(String(100), nullable=True)
    
    # === Разрешение на использование ===
    allow_training = Column(Boolean, default=True)  # Можно ли использовать для дообучения
    processed = Column(Boolean, default=False)  # Уже использован для fine-tuning
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # === Связи ===
    user = relationship("User", back_populates="feedbacks")
    tutor = relationship("Tutor", back_populates="feedbacks")
    chat = relationship("Chat", back_populates="feedbacks")
    message = relationship("Message", back_populates="feedbacks")
