"""
API endpoints для работы с сообщениями.
КЛЮЧЕВОЙ ФАЙЛ - здесь происходит взаимодействие с AI!
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, delete
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.models.user import User
from app.models.chat import Chat
from app.models.message import Message
from app.models.tutor import Tutor
from app.schemas.message import (
    MessageCreate,
    MessageResponse,
    MessageListResponse,
    ChatMessagePairResponse
)
from app.utils.dependencies import get_current_user
from app.services.orchestrator import Orchestrator
from app.services.ai_client import AIClient


router = APIRouter(prefix="/api/chats", tags=["Messages"])


@router.get("/{chat_id}/messages", response_model=MessageListResponse)
async def get_chat_messages(
    chat_id: int,
    limit: int = Query(50, ge=1, le=100, description="Количество сообщений"),
    before_id: Optional[int] = Query(None, description="ID сообщения для пагинации"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение истории сообщений чата с пагинацией.
    Для "бесконечного скролла" на фронтенде.
    
    Фронтенд отправляет:
        GET /api/chats/1/messages?limit=50&before_id=100
        Headers: Authorization: Bearer <token>
    
    Параметры:
        - limit: сколько сообщений загрузить (по умолчанию 50)
        - before_id: загрузить сообщения старше этого ID (для скролла вверх)
    
    Бэкенд возвращает:
        {
          "messages": [
            {
              "id": 99,
              "role": "assistant",
              "content": "Отличный вопрос! Циклы...",
              "created_at": "2025-12-06T15:30:05Z"
            },
            {
              "id": 98,
              "role": "user",
              "content": "Что такое циклы?",
              "created_at": "2025-12-06T15:30:00Z"
            },
            ...
          ],
          "has_more": true,
          "total": 150
        }
    """
    
    # Проверяем доступ к чату
    result = await db.execute(
        select(Chat).where(
            Chat.id == chat_id,
            Chat.user_id == current_user.id
        )
    )
    chat = result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Строим запрос для получения сообщений
    query = select(Message).where(Message.chat_id == chat_id)
    
    # Если указан before_id, загружаем сообщения старше его
    if before_id:
        query = query.where(Message.id < before_id)
    
    # Сортируем по убыванию (новые сначала), ограничиваем количество
    query = query.order_by(desc(Message.created_at)).limit(limit + 1)
    
    # Выполняем запрос
    result = await db.execute(query)
    messages = result.scalars().all()
    
    # Проверяем, есть ли еще сообщения (для has_more)
    has_more = len(messages) > limit
    if has_more:
        messages = messages[:limit]  # Убираем лишнее
    
    # Переворачиваем список (старые сообщения сверху)
    messages = list(reversed(messages))
    
    # Подсчитываем общее количество сообщений
    from sqlalchemy import func
    count_result = await db.execute(
        select(func.count()).select_from(Message).where(Message.chat_id == chat_id)
    )
    total = count_result.scalar()
    
    return {
        "messages": messages,
        "has_more": has_more,
        "total": total
    }


@router.post("/{chat_id}/messages", response_model=ChatMessagePairResponse)
async def send_message(
    chat_id: int,
    message_data: MessageCreate,  # JSON: { "content": "Что такое циклы?", "attachments": [...] }
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    ⭐ САМЫЙ ВАЖНЫЙ ENDPOINT ⭐
    Отправка сообщения в чат и получение ответа от AI.
    
    Фронтенд отправляет:
        POST /api/chats/1/messages
        Headers: Authorization: Bearer <token>
        {
          "content": "Объясни что такое list comprehension?",
          "attachments": [
            {
              "filename": "code.py",
              "url": "https://storage.com/code.py",
              "type": "text/x-python"
            }
          ]
        }
    
    Что происходит внутри:
    1. Проверяем доступ к чату
    2. Сохраняем сообщение пользователя в БД
    3. Получаем историю диалога
    4. Вызываем Orchestrator (который обращается к AI Core Андрея)
    5. Получаем ответ от AI
    6. Сохраняем ответ AI в БД
    7. Возвращаем оба сообщения фронтенду
    
    Бэкенд возвращает:
        {
          "user_message": {
            "id": 150,
            "role": "user",
            "content": "Объясни что такое list comprehension?",
            "created_at": "2025-12-06T16:00:00Z"
          },
          "ai_response": {
            "id": 151,
            "role": "assistant",
            "content": "List comprehension — это компактный способ создания списков...",
            "created_at": "2025-12-06T16:00:03Z"
          }
        }
    """
    
    # === ШАГ 1: Проверка доступа к чату ===
    result = await db.execute(
        select(Chat).where(
            Chat.id == chat_id,
            Chat.user_id == current_user.id
        )
    )
    chat = result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # === ШАГ 2: Получаем информацию о репетиторе ===
    result = await db.execute(
        select(Tutor).where(Tutor.id == chat.tutor_id)
    )
    tutor = result.scalar_one_or_none()
    
    if not tutor:
        raise HTTPException(status_code=500, detail="Tutor not found")
    
    # === ШАГ 3: Сохраняем сообщение пользователя в БД ===
    user_message = Message(
        chat_id=chat_id,
        role="user",
        content=message_data.content,
        attachments=message_data.attachments
    )
    
    db.add(user_message)
    await db.commit()
    await db.refresh(user_message)
    
    # === ШАГ 4: Получаем историю последних сообщений для контекста ===
    history_result = await db.execute(
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at)
        .limit(20)  # Последние 20 сообщений для контекста
    )
    message_history = history_result.scalars().all()
    
    # === ШАГ 5: Вызываем Orchestrator для получения ответа AI ===
    ai_client = AIClient()
    orchestrator = Orchestrator(ai_client)
    
    try:
        # Вызываем оркестратор (он обращается к AI Core Андрея)
        ai_response_content = await orchestrator.process_user_message(
            chat_id=chat_id,
            tutor=tutor,
            user_message=message_data.content,
            message_history=message_history,
            attachments=message_data.attachments
        )
    
    except Exception as e:
        # Если AI Core недоступен или произошла ошибка
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI processing error: {str(e)}"
        )
    
    # === ШАГ 6: Сохраняем ответ AI в БД ===
    ai_message = Message(
    chat_id=chat_id,
    role="assistant",
    content=ai_response_content,
    message_metadata={  # ✅ Новое название
        "model_id": tutor.model_id
        }
    )
    
    db.add(ai_message)
    
    # === ШАГ 7: Обновляем время последнего сообщения в чате ===
    chat.last_message_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(ai_message)
    
    # === ШАГ 8: Возвращаем оба сообщения фронтенду ===
    return {
        "user_message": user_message,
        "ai_response": ai_message
    }





@router.delete(
    "/{chat_id}/messages",
    status_code=204,
    summary="Clear chat history",
    description="Удалить все сообщения в чате текущего пользователя",
)
async def clear_chat_messages(
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Проверяем, что чат принадлежит текущему пользователю
    result = await db.execute(
        select(Chat).where(
            Chat.id == chat_id,
            Chat.user_id == current_user.id,
        )
    )
    chat = result.scalar_one_or_none()

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Удаляем все сообщения этого чата
    await db.execute(
        delete(Message).where(Message.chat_id == chat_id)
    )

    # Можно обнулить last_message_at
    chat.last_message_at = None

    await db.commit()

    # 204 No Content — тела нет
    return
