import asyncio
from app.services.ai_client import AIClient

async def test():
    client = AIClient()
    
    print("Checking LM Studio...")
    health = await client.health_check()
    print(f"LM Studio available: {health}")
    
    if health:
        print("\nSending test message...")
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2+2?"}
        ]
        response = await client.chat_completion(messages)
        print(f"AI Response: {response}")
    
    await client.close()

asyncio.run(test())
