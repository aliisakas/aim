from fastapi import APIRouter
from app.services.ai_client import AIClient

router = APIRouter()

@router.get("/test-ai")
async def test_ai(question: str = "What is 2+2?"):
    """Test AI endpoint without database"""
    client = AIClient()
    
    try:
        health = await client.health_check()
        if not health:
            return {"error": "AI Core not available"}
        
        messages = [
            {"role": "system", "content": "You are a helpful Python tutor."},
            {"role": "user", "content": question}
        ]
        
        response = await client.chat_completion(messages)
        return {
            "question": question,
            "ai_response": response,
            "status": "success"
        }
    finally:
        await client.close()
