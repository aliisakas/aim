"""
Модель сообщения в чате
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Message(Base):
    """
    Таблица сообщений.
    Хранит всю историю переписки: сообщения пользователя и ответы AI
    """
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    
    # === Роль отправителя ===
    # "user" = сообщение от пользователя
    # "assistant" = ответ AI-репетитора
    role = Column(String(20), nullable=False)  
    
    content = Column(Text, nullable=False)  # Текст сообщения
    
    # === Вложения (файлы) ===
    # Хранится как JSON: [{"filename": "code.py", "url": "...", "type": "..."}]
    attachments = Column(JSON, nullable=True)
    
    # === Метаданные ===
    # Дополнительная информация: кол-во токенов, время генерации и т.д.
    # Переименовываем metadata → message_metadata (metadata зарезервировано в SQLAlchemy)
    message_metadata = Column("metadata", JSON, nullable=True)

    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # === Связи ===
    chat = relationship("Chat", back_populates="messages")
    feedbacks = relationship("Feedback", back_populates="message")
