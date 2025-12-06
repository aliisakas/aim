"""
Модель чата между пользователем и AI-репетитором
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Chat(Base):
    """
    Таблица чатов.
    Каждый чат = диалог между одним пользователем и одним репетитором
    """
    __tablename__ = "chats"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tutor_id = Column(Integer, ForeignKey("tutors.id", ondelete="CASCADE"), nullable=False)
    
    custom_name = Column(String(255), nullable=True)  # Пользователь может переименовать
    last_message_at = Column(DateTime(timezone=True), nullable=True)  # Время последнего сообщения
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # === Связи ===
    user = relationship("User", back_populates="chats")
    tutor = relationship("Tutor", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="chat")
    
    # === Ограничение уникальности ===
    # Один пользователь может иметь только один чат с каждым репетитором
    __table_args__ = (
        UniqueConstraint('user_id', 'tutor_id', name='unique_user_tutor_chat'),
    )
