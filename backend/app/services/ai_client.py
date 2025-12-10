import httpx
import asyncio
from typing import List, Dict
import logging
import json

logger = logging.getLogger(__name__)

class AIClient:
    def __init__(self, base_url: str = "http://localhost:1234", timeout: float = 120.0):
        self.base_url = base_url
        self.model_id = "local-model"
        self.timeout = timeout
        self.client = httpx.AsyncClient(base_url=base_url, timeout=timeout)
    
    async def health_check(self) -> bool:
        try:
            response = await self.client.get("/v1/models")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"AI health check failed: {e}")
            return False
    
    async def chat_completion(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 1024, stream: bool = False) -> str:
        payload = {"model": self.model_id, "messages": messages, "temperature": temperature, "max_tokens": max_tokens, "stream": stream, "top_p": 0.95}
        try:
            logger.info(f"Sending to AI: {len(messages)} messages")
            response = await self.client.post("/v1/chat/completions", json=payload)
            if response.status_code != 200:
                raise Exception(f"AI error {response.status_code}")
            result = response.json()
            answer = result["choices"][0]["message"]["content"]
            logger.info(f"Got response: {len(answer)} chars")
            return answer
        except Exception as e:
            logger.error(f"AI failed: {e}")
            raise
    
    async def close(self):
        await self.client.aclose()
