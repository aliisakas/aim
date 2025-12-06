"""
Dependency функции для FastAPI endpoints.
Используются для проверки авторизации и получения текущего пользователя.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.utils.security import decode_access_token


# === HTTP Bearer токен схема ===
# Автоматически извлекает токен из заголовка Authorization: Bearer <token>
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency для получения текущего авторизованного пользователя.
    Используется в защищенных endpoints.
    
    Как работает:
    1. Извлекает JWT токен из заголовка Authorization
    2. Расшифровывает токен
    3. Находит пользователя в БД
    4. Возвращает объект User
    
    Использование в endpoint:
        @router.get("/profile")
        async def get_profile(
            current_user: User = Depends(get_current_user)
        ):
            return current_user
    
    Если токен невалидный или пользователь не найден, вернется ошибка 401
    """
    
    # Извлекаем токен из заголовка
    token = credentials.credentials
    
    # Расшифровываем токен
    token_data = decode_access_token(token)
    
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Ищем пользователя в базе данных
    result = await db.execute(
        select(User).where(User.id == token_data.user_id)
    )
    user = result.scalar_one_or_none()
    
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user


# === Опциональная авторизация ===
async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    То же что get_current_user, но не выбрасывает ошибку если токена нет.
    Используется для endpoints, где авторизация опциональна.
    """
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None
