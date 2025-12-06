from pydantic import BaseModel
from typing import Optional


class ProgressResponse(BaseModel):
    """
    Прогресс по конкретному репетитору.
    """
    tutor_id: int
    total_minutes: int

    class Config:
        from_attributes = True


class ProgressUpdate(BaseModel):
    """
    Обновление прогресса.
    Либо задаём точное значение, либо добавляем дельту.
    """
    add_minutes: Optional[int] = None  # например +5 минут
    set_minutes: Optional[int] = None  # если надо явно установить
