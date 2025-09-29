from fastapi import APIRouter
from app.api.api_v1.api import api_router as api_v1_router
from app.api.routes import graphs as graphs_routes

api_router = APIRouter()

# Include API v1 routes
api_router.include_router(api_v1_router, prefix="/v1")

# LangGraph research graph routes
api_router.include_router(graphs_routes.router, prefix="/graphs", tags=["Graphs"])


@api_router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ScholarAI FastAPI Backend",
        "version": "0.1.0",
    }
