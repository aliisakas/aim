"""
Модель AI-репетитора.
Описывает таблицу 'tutors' - каждый репетитор это AI с определенным курсом
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Tutor(Base):
    """
    Таблица AI-репетиторов в базе данных.
    Каждый репетитор привязан к курсу и имеет свою модель AI
    """
    __tablename__ = "tutors"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"))
    name = Column(String(255), nullable=False)  # Например: "Python для начинающих"
    description = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)  # Ссылка на аватар
    
    # === Настройки AI модели ===
    model_id = Column(String(100), nullable=False)  # Версия модели: tutor_python_v1
    system_prompt = Column(Text, nullable=False)  # Базовый промпт для AI
    knowledge_base_id = Column(String(100), nullable=True)  # ID в векторной БД
    
    # === Рейтинг и статистика ===
    rating = Column(DECIMAL(3, 2), default=0.0)  # Средний рейтинг 0.00-5.00
    total_feedbacks = Column(Integer, default=0)  # Количество отзывов
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # === Связи ===
    course = relationship("Course", back_populates="tutors")
    chats = relationship("Chat", back_populates="tutor", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="tutor")
    progress_items = relationship(
        "Progress",
        back_populates="tutor",
        cascade="all, delete-orphan",
    )

