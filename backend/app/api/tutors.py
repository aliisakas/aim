"""
API endpoints для работы с репетиторами
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from app.database import get_db
from app.models.tutor import Tutor
from app.models.course import Course
from app.schemas.tutor import TutorResponse, TutorListResponse


router = APIRouter(prefix="/api/tutors", tags=["Tutors"])


@router.get("", response_model=TutorListResponse)
async def get_tutors(
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    difficulty: Optional[str] = Query(None, description="Фильтр по сложности"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(20, ge=1, le=100, description="Количество на странице"),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение списка доступных репетиторов с фильтрацией.
    
    Фронтенд отправляет:
        GET /api/tutors?category=Программирование&difficulty=Начальный&page=1
    
    Бэкенд возвращает:
        {
          "tutors": [
            {
              "id": 1,
              "name": "Python для начинающих",
              "description": "...",
              "rating": 4.8,
              "total_feedbacks": 120,
              ...
            }
          ],
          "total": 5,
          "page": 1,
          "page_size": 20
        }
    """
    
    # Строим базовый запрос
    query = select(Tutor).where(Tutor.is_active == True)
    
    # Добавляем фильтры если указаны
    if category:
        # Джойним с таблицей courses для фильтрации по категории
        query = query.join(Course).where(Course.category == category)
    
    if difficulty:
        query = query.join(Course).where(Course.difficulty_level == difficulty)
    
    # Подсчитываем общее количество
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Применяем пагинацию
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Выполняем запрос
    result = await db.execute(query)
    tutors = result.scalars().all()
    
    return {
        "tutors": tutors,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{tutor_id}", response_model=TutorResponse)
async def get_tutor_by_id(
    tutor_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Получение детальной информации о конкретном репетиторе.
    
    Фронтенд отправляет:
        GET /api/tutors/1
    
    Бэкенд возвращает:
        {
          "id": 1,
          "name": "Python для начинающих",
          "description": "Подробное описание...",
          ...
        }
    """
    
    result = await db.execute(
        select(Tutor).where(Tutor.id == tutor_id)
    )
    tutor = result.scalar_one_or_none()
    
    if not tutor:
        raise HTTPException(
            status_code=404,
            detail="Tutor not found"
        )
    
    return tutor
