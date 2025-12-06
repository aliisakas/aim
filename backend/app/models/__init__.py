"""
Импорт всех моделей для удобства.
Alembic будет автоматически находить модели через этот файл
"""

from app.models.user import User
from app.models.course import Course
from app.models.tutor import Tutor
from app.models.chat import Chat
from app.models.message import Message
from app.models.feedback import Feedback

# Экспортируем все модели
__all__ = ["User", "Course", "Tutor", "Chat", "Message", "Feedback"]
