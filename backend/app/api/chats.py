"""
API endpoints для управления чатами
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database import get_db
from app.models.user import User
from app.models.chat import Chat
from app.models.tutor import Tutor
from app.models.message import Message
from app.schemas.chat import (
    ChatCreate, ChatResponse, ChatUpdate, ChatListResponse
)
from app.utils.dependencies import get_current_user


router = APIRouter(prefix="/api/chats", tags=["Chats"])


@router.post("", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    chat_data: ChatCreate,  # JSON: { "tutor_id": 1 }
    current_user: User = Depends(get_current_user),  # Проверка авторизации
    db: AsyncSession = Depends(get_db)
):
    """
    Создание нового чата с репетитором.
    
    Фронтенд отправляет:
        POST /api/chats
        Headers: Authorization: Bearer <token>
        { "tutor_id": 1 }
    
    Бэкенд возвращает:
        201 Created
        {
          "id": 1,
          "user_id": 1,
          "tutor_id": 1,
          "tutor": { ...данные репетитора... },
          "created_at": "2025-12-06T15:50:00Z",
          ...
        }
    """
    
    # Проверяем существование репетитора
    result = await db.execute(
        select(Tutor).where(Tutor.id == chat_data.tutor_id)
    )
    tutor = result.scalar_one_or_none()
    
    if not tutor or not tutor.is_active:
        raise HTTPException(
            status_code=404,
            detail="Tutor not found or inactive"
        )
    
    # Проверяем, нет ли уже чата с этим репетитором
    result = await db.execute(
        select(Chat).where(
            Chat.user_id == current_user.id,
            Chat.tutor_id == chat_data.tutor_id
        )
    )
    existing_chat = result.scalar_one_or_none()
    
    if existing_chat:
        # Возвращаем существующий чат
        return existing_chat
    
    # Создаем новый чат
    new_chat = Chat(
        user_id=current_user.id,
        tutor_id=chat_data.tutor_id
    )
    
    db.add(new_chat)
    await db.commit()
    await db.refresh(new_chat)
    
    # Загружаем связанного репетитора
    await db.refresh(new_chat, ["tutor"])
    
    return new_chat


@router.get("", response_model=ChatListResponse)
async def get_user_chats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение списка всех чатов текущего пользователя.
    
    Фронтенд отправляет:
        GET /api/chats
        Headers: Authorization: Bearer <token>
    
    Бэкенд возвращает:
        {
          "chats": [
            {
              "id": 1,
              "tutor": { "name": "Python для начинающих", ... },
              "last_message": "Отличный вопрос! Циклы...",
              "last_message_at": "2025-12-06T15:45:00Z",
              "unread_count": 0
            }
          ],
          "total": 3
        }
    """
    
    # Получаем все чаты пользователя
    result = await db.execute(
        select(Chat)
        .where(Chat.user_id == current_user.id)
        .order_by(desc(Chat.last_message_at))  # Сначала самые свежие
    )
    chats = result.scalars().all()
    
    # Для каждого чата получаем последнее сообщение
    chat_list = []
    for chat in chats:
        # Загружаем репетитора
        await db.refresh(chat, ["tutor"])
        
        # Получаем последнее сообщение
        last_msg_result = await db.execute(
            select(Message)
            .where(Message.chat_id == chat.id)
            .order_by(desc(Message.created_at))
            .limit(1)
        )
        last_message = last_msg_result.scalar_one_or_none()
        
        # Формируем объект ответа
        chat_response = ChatResponse.model_validate(chat)
        if last_message:
            chat_response.last_message = last_message.content[:50] + "..."
        
        chat_list.append(chat_response)
    
    return {
        "chats": chat_list,
        "total": len(chat_list)
    }


@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat_by_id(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение информации о конкретном чате.
    Проверяет, что чат принадлежит текущему пользователю.
    """
    
    result = await db.execute(
        select(Chat).where(
            Chat.id == chat_id,
            Chat.user_id == current_user.id  # Проверка владельца
        )
    )
    chat = result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(
            status_code=404,
            detail="Chat not found"
        )
    
    await db.refresh(chat, ["tutor"])
    return chat


@router.patch("/{chat_id}", response_model=ChatResponse)
async def update_chat(
    chat_id: int,
    update_data: ChatUpdate,  # JSON: { "custom_name": "Мой Python курс" }
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Обновление настроек чата (например, переименование).
    
    Фронтенд отправляет:
        PATCH /api/chats/1
        { "custom_name": "Мой Python курс" }
    """
    
    # Находим чат
    result = await db.execute(
        select(Chat).where(
            Chat.id == chat_id,
            Chat.user_id == current_user.id
        )
    )
    chat = result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Обновляем поля
    if update_data.custom_name is not None:
        chat.custom_name = update_data.custom_name
    
    await db.commit()
    await db.refresh(chat)
    await db.refresh(chat, ["tutor"])
    
    return chat


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Удаление чата.
    Все сообщения и отзывы тоже удалятся (CASCADE).
    
    Фронтенд отправляет:
        DELETE /api/chats/1
        Headers: Authorization: Bearer <token>
    
    Бэкенд возвращает:
        204 No Content
    """
    
    result = await db.execute(
        select(Chat).where(
            Chat.id == chat_id,
            Chat.user_id == current_user.id
        )
    )
    chat = result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    await db.delete(chat)
    await db.commit()
    
    return None  # 204 No Content не возвращает тело ответа
