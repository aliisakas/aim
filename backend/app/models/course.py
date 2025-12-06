"""
Модель курса/навыка
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Course(Base):
    """
    Таблица курсов.
    Например: "Python для начинающих", "ЕГЭ Русский язык"
    """
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # Название курса
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)  # "Программирование", "ЕГЭ"
    difficulty_level = Column(String(50), nullable=True)  # "Начальный", "Продвинутый"
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # === Связи ===
    # У курса может быть несколько версий репетиторов
    tutors = relationship("Tutor", back_populates="course")
