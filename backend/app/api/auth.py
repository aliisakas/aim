"""
API endpoints для аутентификации и регистрации
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token, ChangePasswordRequest, UserSettingsUpdate
from app.utils.security import hash_password, verify_password, create_access_token
from app.utils.dependencies import get_current_user


# Создаем роутер с префиксом /api/auth
router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,  # JSON от фронтенда (валидируется Pydantic)
    db: AsyncSession = Depends(get_db)  # Автоматически получаем сессию БД
):
    """
    Регистрация нового пользователя.
    
    Фронтенд отправляет:
        POST /api/auth/register
        {
          "email": "student@mail.ru",
          "username": "ivanov",
          "password": "securepass123",
          "full_name": "Иван Иванов"
        }
    
    Бэкенд возвращает:
        201 Created
        {
          "id": 1,
          "email": "student@mail.ru",
          "username": "ivanov",
          "full_name": "Иван Иванов",
          "is_active": true,
          "created_at": "2025-12-06T15:40:00Z"
        }
    """
    
    # Проверяем, не занят ли email
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Проверяем, не занят ли username
    result = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Создаем нового пользователя
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hash_password(user_data.password),  # Хешируем пароль!
        full_name=user_data.full_name
    )
    
    # Сохраняем в БД
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)  # Получаем ID и created_at из БД
    
    return new_user


@router.post("/login", response_model=Token)
async def login_user(
    credentials: UserLogin,  # JSON с username и password
    db: AsyncSession = Depends(get_db)
):
    """
    Вход в систему. Возвращает JWT токен.
    
    Фронтенд отправляет:
        POST /api/auth/login
        {
          "username": "ivanov",
          "password": "securepass123"
        }
    
    Бэкенд возвращает:
        200 OK
        {
          "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
          "token_type": "bearer",
          "user": { ...данные пользователя... }
        }
    
    Фронтенд сохраняет токен и отправляет его в заголовке при каждом запросе:
        Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
    
    # Ищем пользователя по username
    result = await db.execute(
        select(User).where(User.username == credentials.username)
    )
    user = result.scalar_one_or_none()
    
    # Проверяем существование пользователя и правильность пароля
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Проверяем активен ли аккаунт
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    # Создаем JWT токен
    access_token = create_access_token(
        data={"user_id": user.id, "username": user.username}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)  # Автоматически проверяет токен
):
    """
    Получение информации о текущем авторизованном пользователе.
    
    Фронтенд отправляет:
        GET /api/auth/me
        Headers:
          Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    
    Бэкенд возвращает:
        200 OK
        {
          "id": 1,
          "email": "student@mail.ru",
          "username": "ivanov",
          ...
        }
    
    Dependency get_current_user автоматически:
    - Извлекает токен из заголовка
    - Проверяет его валидность
    - Находит пользователя в БД
    - Возвращает объект User
    
    Если токен невалидный, вернется 401 Unauthorized
    """
    return current_user





@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Смена пароля текущего пользователя.

    Шаги:
    1. Проверяем старый пароль.
    2. Если ок — хешируем новый и сохраняем.
    """
    # Проверяем, что старый пароль верный
    if not verify_password(data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password",
        )

    # Хешируем новый пароль
    current_user.hashed_password = hash_password(data.new_password)

    # Сохраняем изменения
    await db.commit()

    # 204 No Content — тело ответа не нужно
    return



@router.patch("/me/settings", response_model=UserResponse)
async def update_settings(
    settings_data: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Обновление настроек пользователя (например, темы интерфейса).
    Храним всё в поле preferences как JSON.
    """
    # Текущие настройки
    prefs = current_user.preferences or {}

    # Обновляем только те поля, которые пришли
    if settings_data.theme is not None:
        prefs["theme"] = settings_data.theme

    current_user.preferences = prefs

    await db.commit()
    await db.refresh(current_user)

    return current_user

