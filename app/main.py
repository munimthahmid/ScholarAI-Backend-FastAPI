from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router

from app.core.config import settings

app = FastAPI(
    title="ScholarAI Backend",
    version="0.1.0",
    description="Backend for ScholarAI research assistant."
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
    return {"message": "ScholarAI backend is running 🚀"}
