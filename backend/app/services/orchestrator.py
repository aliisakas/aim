"""
Orchestrator - оркестратор запросов к AI.
Центральный компонент, который координирует взаимодействие с AI Core.
"""

from typing import List, Dict, Optional
from app.models.message import Message
from app.models.tutor import Tutor
from app.services.ai_client import AIClient


class Orchestrator:
    """
    Оркестратор запросов к AI.
    Подготавливает данные и вызывает AI Core для генерации ответов.
    """
    
    def __init__(self, ai_client: AIClient):
        """
        Параметры:
            ai_client: Экземпляр AIClient для общения с AI Core
        """
        self.ai_client = ai_client
    
    async def process_user_message(
        self,
        chat_id: int,
        tutor: Tutor,
        user_message: str,
        message_history: List[Message],
        attachments: Optional[List[Dict]] = None
    ) -> str:
        """
        Главная функция оркестрации.
        Получает сообщение пользователя, подготавливает контекст,
        отправляет в AI Core и возвращает ответ.
        
        Параметры:
            chat_id: ID чата
            tutor: Объект репетитора (с model_id, system_prompt и т.д.)
            user_message: Текст сообщения пользователя
            message_history: История предыдущих сообщений (для контекста)
            attachments: Прикрепленные файлы (если есть)
        
        Возвращает:
            Строку с ответом AI
        
        Процесс:
            1. Форматируем историю сообщений в нужный формат
            2. Формируем запрос для AI Core с всеми данными
            3. Вызываем AI Core API
            4. Извлекаем и возвращаем текст ответа
        """
        
        # === ШАГ 1: Форматируем историю сообщений ===
        # Преобразуем SQLAlchemy объекты в простые словари
        formatted_history = self._format_message_history(message_history)
        
        # === ШАГ 2: Подготавливаем данные для AI Core ===
        ai_request = {
            "chat_id": chat_id,
            "tutor_id": tutor.id,
            "model_id": tutor.model_id,  # Например: "tutor_python_v1"
            "knowledge_base_id": tutor.knowledge_base_id,  # ID в векторной БД
            "system_prompt": tutor.system_prompt,  # Базовый промпт репетитора
            "message": user_message,  # Вопрос пользователя
            "history": formatted_history,  # Последние 20 сообщений
            "attachments": attachments or []  # Прикрепленные файлы
        }
        
        # === ШАГ 3: Вызываем AI Core API ===
        # AIClient отправит HTTP POST запрос к команде Андрея
        ai_response = await self.ai_client.generate_response(ai_request)
        
        # === ШАГ 4: Извлекаем текст ответа ===
        # AI Core вернет JSON типа: {"content": "Ответ...", "tokens_used": 150}
        return ai_response["content"]
    
    def _format_message_history(self, messages: List[Message]) -> List[Dict]:
        """
        Форматирует историю сообщений из SQLAlchemy объектов в список словарей.
        Берем только последние N сообщений, чтобы не перегружать контекст.
        
        Параметры:
            messages: Список объектов Message из БД
        
        Возвращает:
            Список словарей вида:
            [
              {"role": "user", "content": "Привет"},
              {"role": "assistant", "content": "Здравствуй!"},
              {"role": "user", "content": "Что такое циклы?"}
            ]
        """
        
        # Берем последние 20 сообщений (или меньше если их меньше)
        # Это ограничение нужно чтобы не превысить лимит токенов модели
        recent_messages = messages[-20:] if len(messages) > 20 else messages
        
        # Преобразуем в простые словари
        return [
            {
                "role": msg.role,  # "user" или "assistant"
                "content": msg.content  # Текст сообщения
            }
            for msg in recent_messages
        ]
