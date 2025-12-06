"""
Функции для работы с JWT токенами и паролями
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings
from app.schemas.user import TokenData


# === ХЕШИРОВАНИЕ ПАРОЛЕЙ ===
# Используем bcrypt для безопасного хранения паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Хеширует пароль перед сохранением в БД.
    Никогда не храним пароли в открытом виде!
    
    Пример:
        hash_password("mypass123") 
        -> "$2b$12$KIXl.../aAbBcC" (хеш)
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет, совпадает ли пароль с хешем.
    Используется при входе в систему.
    
    Пример:
        verify_password("mypass123", "$2b$12$KIXl.../aAbBcC") 
        -> True
    """
    return pwd_context.verify(plain_password, hashed_password)


# === JWT ТОКЕНЫ ===

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Создает JWT токен для аутентификации.
    Токен содержит user_id и username, подписан секретным ключом.
    
    Параметры:
        data: Данные для включения в токен (user_id, username)
        expires_delta: Срок жизни токена (по умолчанию из config)
    
    Возвращает:
        Строку с JWT токеном
    
    Пример:
        create_access_token({"user_id": 1, "username": "ivanov"})
        -> "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    """
    to_encode = data.copy()
    
    # Устанавливаем время истечения токена
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire})
    
    # Кодируем токен с секретным ключом
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    """
    Расшифровывает JWT токен и извлекает данные.
    Проверяет подпись и срок действия.
    
    Параметры:
        token: JWT токен от фронтенда
    
    Возвращает:
        TokenData с user_id и username, или None если токен невалидный
    
    Пример:
        decode_access_token("eyJhbGc...") 
        -> TokenData(user_id=1, username="ivanov")
    """
    try:
        # Декодируем токен
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Извлекаем данные
        user_id: int = payload.get("user_id")
        username: str = payload.get("username")
        
        if user_id is None or username is None:
            return None
        
        return TokenData(user_id=user_id, username=username)
    
    except JWTError:
        # Токен невалидный или истек срок действия
        return None
