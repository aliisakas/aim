"""
Главный файл FastAPI приложения.
Точка входа - здесь запускается весь бэкенд.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base

# Импортируем все роутеры (API endpoints)
from app.api import auth, tutors, chats, messages, feedbacks, progress


# === СОЗДАНИЕ ПРИЛОЖЕНИЯ ===
app = FastAPI(
    title="AI Tutor Platform API",
    description="Backend API для платформы AI-репетиторов",
    version="1.0.0",
    docs_url="/docs",  # Swagger документация: http://localhost:8000/docs
    redoc_url="/redoc"  # ReDoc документация: http://localhost:8000/redoc
)


# === НАСТРОЙКА CORS ===
# CORS (Cross-Origin Resource Sharing) - разрешает фронтенду обращаться к бэкенду
# Фронтенд обычно работает на другом порту (например, 3000), а бэкенд на 8000
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React/Vue фронтенд локально
        "http://localhost:5173",  # Vite фронтенд локально
        "https://yourfrontend.com"  # Продакшн домен (замени на свой)
    ],
    allow_credentials=True,  # Разрешить отправку cookies
    allow_methods=["*"],  # Разрешить все методы (GET, POST, PUT, DELETE и т.д.)
    allow_headers=["*"],  # Разрешить все заголовки
)
# для тестового эндпоинта
from app.api.test_ai import router as test_router
app.include_router(test_router, tags=["test"])

# === ПОДКЛЮЧЕНИЕ РОУТЕРОВ ===
# Каждый роутер отвечает за свою группу endpoints
app.include_router(auth.router)        # /api/auth/*
app.include_router(tutors.router)      # /api/tutors/*
app.include_router(chats.router)       # /api/chats/*
app.include_router(messages.router)    # /api/chats/{id}/messages/*
app.include_router(feedbacks.router)   # /api/feedbacks/*
app.include_router(progress.router)    # /api/progress/*



# === БАЗОВЫЕ ENDPOINTS ===

@app.get("/")
async def root():
    """
    Корневой endpoint.
    Просто проверка что API работает.
    
    Запрос:
        GET http://localhost:8000/
    
    Ответ:
        {
          "message": "AI Tutor Platform API",
          "version": "1.0.0",
          "docs": "/docs"
        }
    """
    return {
        "message": "AI Tutor Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint для мониторинга.
    Проверяет что сервер жив и может отвечать на запросы.
    
    Запрос:
        GET http://localhost:8000/health
    
    Ответ:
        {
          "status": "healthy",
          "database": "connected"
        }
    """
    # TODO: Можно добавить проверку подключения к БД
    # TODO: Можно добавить проверку доступности AI Core
    return {
        "status": "healthy",
        "database": "connected"
    }


# === СОБЫТИЯ ЖИЗНЕННОГО ЦИКЛА ===

@app.on_event("startup")
async def startup_event():
    """
    Выполняется при запуске сервера.
    Здесь можно инициализировать подключения, кеши и т.д.
    """
    print("🚀 Starting AI Tutor Platform API...")
    print(f"📊 Database: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    print(f"🤖 AI Core URL: {settings.AI_CORE_URL}")
    print("✅ Server is ready!")
    
    # ОПЦИОНАЛЬНО: Проверка подключения к AI Core
    # from app.services.ai_client import AIClient
    # ai_client = AIClient()
    # if await ai_client.health_check():
    #     print("✅ AI Core is available")
    # else:
    #     print("⚠️  Warning: AI Core is not available")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Выполняется при остановке сервера.
    Здесь можно закрыть соединения, сохранить данные и т.д.
    """
    print("👋 Shutting down AI Tutor Platform API...")
    # Закрываем соединения с БД (SQLAlchemy сделает это автоматически)


# === ОБРАБОТКА ОШИБОК ===

from fastapi import Request, status
from fastapi.responses import JSONResponse


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Глобальный обработчик ошибок.
    Ловит все необработанные исключения и возвращает понятный JSON.
    """
    print(f"❌ Unhandled error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.DEBUG else "An error occurred"
        }
    )


# === ТОЧКА ВХОДА ===
# Если запускаешь файл напрямую через python app/main.py
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",  # Слушать на всех интерфейсах
        port=8000,
        reload=True  # Автоперезагрузка при изменении кода (только для разработки!)
    )
