import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.core.config import settings
from app.core.logging_config import configure_logging_from_env
from app.services.rabbitmq_consumer import consumer

# Setup environment-aware logging
configure_logging_from_env()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown events"""
    # Startup
    print("🚀 Starting ScholarAI FastAPI Backend...")

    # Start RabbitMQ consumer as background task
    consumer_task = asyncio.create_task(consumer.start_consuming())
    print("🔄 RabbitMQ consumer started as background task")

    yield

    # Shutdown
    print("🛑 Shutting down ScholarAI FastAPI Backend...")
    consumer_task.cancel()
    await consumer.close()
    print("✅ Shutdown complete")


app = FastAPI(
    title="ScholarAI Backend",
    version="0.1.0",
    description="Backend for ScholarAI research assistant with RabbitMQ integration.",
    lifespan=lifespan,
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix="/api")


@app.get("/")
def read_root():
    return {"message": "ScholarAI backend is running 🚀", "rabbitmq_consumer": "active"}


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ScholarAI FastAPI Backend",
        "rabbitmq_consumer": "running",
        "version": "0.1.0",
    }
