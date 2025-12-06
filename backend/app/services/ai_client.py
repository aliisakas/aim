"""
HTTP клиент для общения с AI Core микросервисом (команда Андрея).
Этот класс отправляет запросы к API Андрея.
"""

import httpx
from typing import Dict, Any
from app.config import settings


class AIClient:
    """
    Клиент для взаимодействия с AI Core API.
    Отправляет запросы к микросервису команды Андрея.
    """
    
    def __init__(self):
        """
        Инициализация клиента.
        Адрес AI Core берется из настроек (.env файл)
        """
        self.base_url = settings.AI_CORE_URL  # Например: http://localhost:8001
        self.timeout = 60.0  # AI может думать долго, даем 60 секунд
    
    async def generate_response(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Отправка запроса к AI Core для генерации ответа.
        
        Параметры:
            request_data: Словарь с данными запроса
                {
                  "chat_id": 1,
                  "tutor_id": 1,
                  "model_id": "tutor_python_v1",
                  "knowledge_base_id": "python_course",
                  "system_prompt": "Ты - AI-репетитор по Python...",
                  "message": "Что такое циклы?",
                  "history": [
                    {"role": "user", "content": "Привет"},
                    {"role": "assistant", "content": "Здравствуй!"}
                  ],
                  "attachments": [...]
                }
        
        Возвращает:
            Словарь с ответом от AI Core:
                {
                  "content": "Цикл for в Python используется для...",
                  "tokens_used": 150,
                  "processing_time": 2.3
                }
        
        Исключения:
            Exception: Если AI Core недоступен или вернул ошибку
        """
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                # === ВАЖНО: Этот endpoint должен предоставить команда Андрея ===
                # Уточни у Андрея точный адрес их API
                response = await client.post(
                    f"{self.base_url}/api/v1/generate",  # Адрес API Андрея
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                )
                
                # Проверяем статус ответа
                response.raise_for_status()
                
                # Возвращаем JSON ответ
                return response.json()
            
            except httpx.TimeoutException:
                # AI Core не ответил за 60 секунд
                raise Exception("AI Core service timeout - model is taking too long to respond")
            
            except httpx.HTTPStatusError as e:
                # AI Core вернул ошибку (4xx или 5xx)
                raise Exception(
                    f"AI Core returned error: {e.response.status_code} - {e.response.text}"
                )
            
            except httpx.RequestError as e:
                # Не удалось подключиться к AI Core
                raise Exception(f"Failed to connect to AI Core: {str(e)}")
    
    async def health_check(self) -> bool:
        """
        Проверка доступности AI Core сервиса.
        Полезно для мониторинга.
        
        Возвращает:
            True если AI Core работает, False если недоступен
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except:
            return False