"""
Модель пользователя.
Эта модель описывает таблицу 'users' в PostgreSQL
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """
    Таблица пользователей в базе данных.
    SQLAlchemy автоматически создаст таблицу с этими колонками
    """
    __tablename__ = "users"  # Имя таблицы в PostgreSQL
    
    # === Колонки таблицы ===
    id = Column(Integer, primary_key=True, index=True)  # Уникальный ID
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)  # Хешированный пароль
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)  # Активен ли пользователь
    preferences = Column(JSON, nullable=True)  # Настройки пользователя (например, тема)

    
    # Автоматические временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # === Связи с другими таблицами ===
    # Один пользователь может иметь много чатов
    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")
    
    # Один пользователь может оставить много отзывов
    feedbacks = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")

    progress_items = relationship(
        "Progress",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    
    def __repr__(self):
        """Для удобного отображения в логах"""
        return f"<User(id={self.id}, username={self.username})>"
