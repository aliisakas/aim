"""
Экспорт всех схем для удобного импорта
"""

from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    TokenData
)
from app.schemas.tutor import TutorResponse, TutorListResponse
from app.schemas.chat import (
    ChatCreate,
    ChatResponse,
    ChatUpdate,
    ChatListResponse
)
from app.schemas.message import (
    MessageCreate,
    MessageResponse,
    MessageListResponse,
    ChatMessagePairResponse
)
from app.schemas.feedback import (
    FeedbackCreate,
    QuickFeedbackCreate,
    FeedbackResponse
)

__all__ = [
    "UserCreate", "UserLogin", "UserResponse", "Token", "TokenData",
    "TutorResponse", "TutorListResponse",
    "ChatCreate", "ChatResponse", "ChatUpdate", "ChatListResponse",
    "MessageCreate", "MessageResponse", "MessageListResponse", "ChatMessagePairResponse",
    "FeedbackCreate", "QuickFeedbackCreate", "FeedbackResponse"
]
