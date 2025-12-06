"""
API для прогресса пользователя по репетитору.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.tutor import Tutor
from app.models.progress import Progress
from app.schemas.progress import ProgressResponse, ProgressUpdate
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/api/progress", tags=["Progress"])


@router.get("/{tutor_id}", response_model=ProgressResponse)
async def get_progress(
    tutor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Проверяем, что репетитор существует
    result = await db.execute(select(Tutor).where(Tutor.id == tutor_id))
    tutor = result.scalar_one_or_none()
    if not tutor:
        raise HTTPException(status_code=404, detail="Tutor not found")

    # Ищем прогресс
    result = await db.execute(
        select(Progress).where(
            Progress.user_id == current_user.id,
            Progress.tutor_id == tutor_id,
        )
    )
    progress = result.scalar_one_or_none()

    if not progress:
        # Если ещё нет записи — считаем 0 минут
        progress = Progress(user_id=current_user.id, tutor_id=tutor_id, total_minutes=0)
        db.add(progress)
        await db.commit()
        await db.refresh(progress)

    return progress


@router.patch("/{tutor_id}", response_model=ProgressResponse)
async def update_progress(
    tutor_id: int,
    data: ProgressUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Ищем прогресс
    result = await db.execute(
        select(Progress).where(
            Progress.user_id == current_user.id,
            Progress.tutor_id == tutor_id,
        )
    )
    progress = result.scalar_one_or_none()

    if not progress:
        progress = Progress(user_id=current_user.id, tutor_id=tutor_id, total_minutes=0)
        db.add(progress)

    # Логика обновления
    if data.set_minutes is not None:
        progress.total_minutes = max(0, data.set_minutes)

    if data.add_minutes is not None:
        progress.total_minutes = max(0, progress.total_minutes + data.add_minutes)

    await db.commit()
    await db.refresh(progress)

    return progress
