"""
Инициализация пакета api.
Экспортируем все роутеры для удобного импорта в main.py
"""

from app.api import auth, tutors, chats, messages, feedbacks

__all__ = ["auth", "tutors", "chats", "messages", "feedbacks"]
