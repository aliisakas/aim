"""
Orchestrator - главный дирижёр между Backend и AI Core.

Его задача:
1. Собрать контекст из истории чата
2. Если есть RAG - найти релевантные документы
3. Собрать финальный промпт
4. Отправить в AI Core
5. Вернуть ответ
"""

from typing import List, Optional, Dict
from app.models.message import Message
from app.models.tutor import Tutor
from app.services.ai_client import AIClient
import logging

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Оркестратор для управления диалогом между пользователем и AI.
    """
    
    def __init__(self, ai_client: AIClient):
        """
        Args:
            ai_client: Экземпляр AIClient для работы с LLM
        """
        self.ai_client = ai_client
    
    def _format_message_history(
        self, 
        messages: List[Message],
        max_messages: int = 10
    ) -> List[Dict[str, str]]:
        """
        Преобразует историю сообщений из БД в формат OpenAI API.
        
        Args:
            messages: Список объектов Message из БД
            max_messages: Сколько последних сообщений включить
        
        Returns:
            Список вида:
            [
                {"role": "user", "content": "Что такое цикл?"},
                {"role": "assistant", "content": "Цикл это..."},
                ...
            ]
        """
        
        # Берём только последние max_messages
        recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages
        
        formatted = []
        for msg in recent_messages:
            formatted.append({
                "role": msg.role,  # "user" или "assistant"
                "content": msg.content
            })
        
        return formatted
    
    def _build_system_prompt(self, tutor: Tutor) -> str:
        """
        Формирует системный промпт для модели.
        
        Системный промпт определяет "личность" и поведение AI.
        
        Args:
            tutor: Объект репетитора с его настройками
        
        Returns:
            Системный промпт, например:
            "Ты — терпеливый репетитор по Python для начинающих.
             Объясняй концепции простыми словами с примерами.
             Если ученик ошибается, задавай наводящие вопросы..."
        """
        
        # TODO: Когда RAG будет готов, можно добавить контекст из документов
        # Пока просто используем промпт из БД
        
        if tutor.system_prompt:
            return tutor.system_prompt
        
        # Fallback промпт если в БД ничего нет
        return f"""Ты — репетитор по курсу "{tutor.name}".
Помогай пользователю учиться, объясняя просто и понятно.
Всегда приводи примеры кода или формулы.
Если ученик затрудняется, задай наводящий вопрос вместо готового ответа."""
    
    def _build_rag_context(self, tutor: Tutor) -> Optional[str]:
        """
        Получает релевантный контекст из RAG (если доступен).
        
        ВАЖНО: Эта функция заполняется ПОЗЖЕ, когда RAG будет готов.
        
        На данный момент она просто возвращает None.
        
        Args:
            tutor: Репетитор для которого нужен контекст
        
        Returns:
            Строка с контекстом из документов или None
        
        Example возвращаемого значения:
        ```
        "Из документов найдено:
        
        === Лекция: Циклы в Python ===
        Цикл for используется для итерации по элементам:
        ```python
        for i in range(5):
            print(i)
        ```
        
        === Задача #12: Вывести чётные числа ===
        Решение:
        ```python
        for i in range(10):
            if i % 2 == 0:
                print(i)
        ```
        "
        ```
        """
        
        # TODO: Позже добавить вызов RAG API
        # rag_results = await rag_client.search(
        #     query=user_message,
        #     tutor_id=tutor.id,
        #     top_k=3
        # )
        # return rag_results.format_as_context()
        
        return None  # На данный момент RAG нет
    
    async def process_user_message(
        self,
        chat_id: int,
        tutor: Tutor,
        user_message: str,
        message_history: List[Message],
        attachments: Optional[List[Dict]] = None
    ) -> str:
        """
        Основной метод обработки сообщения пользователя.
        
        WORKFLOW:
        1. Формируем историю в формате OpenAI
        2. Собираем контекст из RAG (если есть)
        3. Строим финальный промпт
        4. Отправляем в AI Core
        5. Возвращаем ответ
        
        Args:
            chat_id: ID чата (для логирования)
            tutor: Репетитор (его промпт и настройки)
            user_message: Текст сообщения от пользователя
            message_history: История сообщений из БД (для контекста)
            attachments: Загруженные файлы (пока не используются)
        
        Returns:
            Текст ответа AI для сохранения в БД
        
        Raises:
            Exception если AI Core недоступен
        """
        
        logger.info(f"Processing message in chat {chat_id}")
        
        # === ШАГ 1: Формируем историю ===
        formatted_history = self._format_message_history(message_history, max_messages=10)
        
        # === ШАГ 2: Строим системный промпт ===
        system_prompt = self._build_system_prompt(tutor)
        
        # === ШАГ 3: Получаем контекст из RAG ===
        rag_context = self._build_rag_context(tutor)
        
        # === ШАГ 4: Собираем финальный список сообщений для API ===
        
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Добавляем контекст из RAG если есть
        if rag_context:
            messages.append({
                "role": "system",
                "content": f"Релевантная информация из базы знаний:\n\n{rag_context}"
            })
        
        # Добавляем историю диалога
        messages.extend(formatted_history)
        
        # Добавляем текущее сообщение пользователя
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # === ШАГ 5: Отправляем в AI Core ===
        logger.info(f"Sending to AI Core: {len(messages)} messages total")
        
        try:
            response = await self.ai_client.chat_completion(
                messages=messages,
                temperature=0.7,  # Небольшая креативность
                max_tokens=1024,  # Обычный размер ответа репетитора
                stream=False
            )
            
            logger.info(f"Got response from AI Core: {len(response)} chars")
            
            return response
        
        except Exception as e:
            logger.error(f"Failed to get AI response: {e}")
            # Возвращаем "graceful" сообщение об ошибке вместо краша
            return f"❌ Извините, репетитор временно недоступен. Ошибка: {str(e)}"
