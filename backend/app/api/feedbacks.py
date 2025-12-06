"""
API endpoints для обратной связи
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.user import User
from app.models.chat import Chat
from app.models.tutor import Tutor
from app.models.feedback import Feedback
from app.schemas.feedback import (
    FeedbackCreate,
    QuickFeedbackCreate,
    FeedbackResponse
)
from app.utils.dependencies import get_current_user


router = APIRouter(prefix="/api/feedbacks", tags=["Feedbacks"])


async def update_tutor_rating(tutor_id: int, db: AsyncSession):
    """
    Пересчитывает средний рейтинг репетитора на основе всех отзывов.
    
    Параметры:
        tutor_id: ID репетитора
        db: Сессия базы данных
    
    Что делает:
    1. Находит все отзывы с оценками (rating) для этого репетитора
    2. Вычисляет средний рейтинг
    3. Обновляет поля rating и total_feedbacks в таблице tutors
    """
    
    # Получаем репетитора
    result = await db.execute(
        select(Tutor).where(Tutor.id == tutor_id)
    )
    tutor = result.scalar_one_or_none()
    
    if not tutor:
        return  # Репетитор не найден, выходим
    
    # Вычисляем средний рейтинг и количество отзывов
    rating_result = await db.execute(
        select(
            func.avg(Feedback.rating),  # Среднее значение рейтинга
            func.count(Feedback.id)     # Количество отзывов
        )
        .where(
            Feedback.tutor_id == tutor_id,
            Feedback.rating.isnot(None)  # Только отзывы с оценкой
        )
    )
    avg_rating, total_feedbacks = rating_result.one()
    
    # Обновляем данные репетитора
    tutor.rating = round(float(avg_rating), 2) if avg_rating else 0.0
    tutor.total_feedbacks = total_feedbacks or 0
    
    await db.commit()


async def mark_feedback_for_training(feedback_id: int, db: AsyncSession):
    """
    Помечает отзыв для обработки командой Андрея (для дообучения AI).
    
    Параметры:
        feedback_id: ID отзыва
        db: Сессия базы данных
    
    Что делает:
    1. Находит отзыв в БД
    2. Проверяет что allow_training = True (пользователь разрешил использование)
    3. Устанавливает processed = False (отзыв готов к обработке)
    
    Команда Андрея будет периодически запускать скрипт, который:
    - Находит все feedbacks где processed = False
    - Добавляет их в векторную БД для RAG
    - Использует для fine-tuning модели
    - Устанавливает processed = True
    """
    
    result = await db.execute(
        select(Feedback).where(Feedback.id == feedback_id)
    )
    feedback = result.scalar_one_or_none()
    
    if not feedback:
        return
    
    # Проверяем что пользователь разрешил использование отзыва для обучения
    if feedback.allow_training:
        feedback.processed = False  # Помечаем как необработанный
        await db.commit()
        
        # ОПЦИОНАЛЬНО: Если у вас есть очередь задач (Redis Queue, Celery)
        # можно отправить задачу напрямую команде Андрея:
        # 
        # from app.services.queue import send_to_training_queue
        # await send_to_training_queue(feedback_id)


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_detailed_feedback(
    feedback_data: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Создание детального отзыва о репетиторе.
    
    Фронтенд отправляет:
        POST /api/feedbacks
        {
          "chat_id": 1,
          "message_id": 150,
          "rating": 5,
          "positive_text": "Отличное объяснение с примерами",
          "improvement_text": "Можно добавить больше практики",
          "allow_training": true
        }
    
    После создания отзыва:
    1. ✅ Обновляется рейтинг репетитора
    2. ✅ Отзыв помечается для обработки командой Андрея
    """
    
    # Проверяем доступ к чату
    result = await db.execute(
        select(Chat).where(
            Chat.id == feedback_data.chat_id,
            Chat.user_id == current_user.id
        )
    )
    chat = result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Создаем отзыв
    new_feedback = Feedback(
        chat_id=feedback_data.chat_id,
        user_id=current_user.id,
        tutor_id=chat.tutor_id,
        message_id=feedback_data.message_id,
        feedback_type=feedback_data.feedback_type,
        rating=feedback_data.rating,
        positive_text=feedback_data.positive_text,
        improvement_text=feedback_data.improvement_text,
        allow_training=feedback_data.allow_training,
        processed=False  # Новый отзыв еще не обработан
    )
    
    db.add(new_feedback)
    await db.commit()
    await db.refresh(new_feedback)
    
    # === ✅ 1. ОБНОВЛЯЕМ РЕЙТИНГ РЕПЕТИТОРА ===
    if feedback_data.rating:  # Только если была оценка (1-5 звезд)
        await update_tutor_rating(chat.tutor_id, db)
    
    # === ✅ 2. ПОМЕЧАЕМ ДЛЯ ОБРАБОТКИ КОМАНДОЙ АНДРЕЯ ===
    await mark_feedback_for_training(new_feedback.id, db)
    
    return new_feedback


@router.post("/quick", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_quick_feedback(
    feedback_data: QuickFeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Быстрая реакция на сообщение AI.
    Кнопки: "Полезно", "Объясни проще", "Больше примеров", "Запутался".
    
    Фронтенд отправляет:
        POST /api/feedbacks/quick
        {
          "chat_id": 1,
          "message_id": 150,
          "quick_reaction": "more_examples"
        }
    
    Варианты quick_reaction:
    - "helpful" - 👍 Полезно
    - "explain_simpler" - Объясни проще
    - "more_examples" - Больше примеров
    - "confused" - Я запутался
    """
    
    # Проверяем доступ к чату
    result = await db.execute(
        select(Chat).where(
            Chat.id == feedback_data.chat_id,
            Chat.user_id == current_user.id
        )
    )
    chat = result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Создаем быстрый отзыв
    new_feedback = Feedback(
        chat_id=feedback_data.chat_id,
        user_id=current_user.id,
        tutor_id=chat.tutor_id,
        message_id=feedback_data.message_id,
        feedback_type="quick_reaction",
        quick_reaction=feedback_data.quick_reaction,
        allow_training=True,  # Быстрые реакции всегда разрешены для обучения
        processed=False  # Еще не обработан
    )
    
    db.add(new_feedback)
    await db.commit()
    await db.refresh(new_feedback)
    
    # === ✅ ПОМЕЧАЕМ ДЛЯ ОБРАБОТКИ ===
    # Быстрые реакции тоже важны для обучения AI
    await mark_feedback_for_training(new_feedback.id, db)
    
    return new_feedback


@router.get("/unprocessed", response_model=list[FeedbackResponse])
async def get_unprocessed_feedbacks(
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    🔧 СЛУЖЕБНЫЙ ENDPOINT ДЛЯ КОМАНДЫ АНДРЕЯ 🔧
    
    Получение необработанных отзывов для дообучения AI.
    Команда Андрея будет периодически вызывать этот endpoint
    или напрямую читать из БД.
    
    Запрос:
        GET /api/feedbacks/unprocessed?limit=100
    
    Ответ:
        [
          {
            "id": 1,
            "tutor_id": 1,
            "feedback_type": "detailed",
            "rating": 5,
            "positive_text": "Отличное объяснение",
            "improvement_text": "Больше примеров",
            "processed": false,
            ...
          },
          ...
        ]
    
    После обработки команда Андрея должна установить processed = True
    через PATCH /api/feedbacks/{id}/mark-processed
    """
    
    result = await db.execute(
        select(Feedback)
        .where(
            Feedback.processed == False,
            Feedback.allow_training == True
        )
        .order_by(Feedback.created_at)
        .limit(limit)
    )
    feedbacks = result.scalars().all()
    
    return feedbacks


@router.patch("/{feedback_id}/mark-processed", status_code=status.HTTP_204_NO_CONTENT)
async def mark_feedback_as_processed(
    feedback_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    🔧 СЛУЖЕБНЫЙ ENDPOINT ДЛЯ КОМАНДЫ АНДРЕЯ 🔧
    
    Помечает отзыв как обработанный после использования для дообучения.
    
    Запрос:
        PATCH /api/feedbacks/123/mark-processed
    
    Ответ:
        204 No Content
    """
    
    result = await db.execute(
        select(Feedback).where(Feedback.id == feedback_id)
    )
    feedback = result.scalar_one_or_none()
    
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    feedback.processed = True
    await db.commit()
    
    return None
