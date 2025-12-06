"""
Модель прогресса пользователя по репетитору.
"""

from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class Progress(Base):
    __tablename__ = "progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tutor_id = Column(Integer, ForeignKey("tutors.id", ondelete="CASCADE"), nullable=False)

    # Сколько минут пользователь учился у этого репетитора
    total_minutes = Column(Integer, nullable=False, default=0)

    # Один пользователь + один репетитор = одна запись
    __table_args__ = (
        UniqueConstraint("user_id", "tutor_id", name="unique_user_tutor_progress"),
    )

    # Связи (опционально)
    user = relationship("User", back_populates="progress_items")
    tutor = relationship("Tutor", back_populates="progress_items")
