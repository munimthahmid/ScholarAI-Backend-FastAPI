from fastapi import APIRouter
from app.api.api_v1.endpoints import admin

api_router = APIRouter()

# Include admin routes for B2 storage management
api_router.include_router(admin.router, prefix="/admin", tags=["Admin B2 Storage"])

# Add your other API routes here
# Example:
# @api_router.get("/example")
# def example_route():
#     return {"message": "This is an example route"} 