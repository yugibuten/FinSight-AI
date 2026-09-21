from fastapi import APIRouter

from app.api.routes import canvas, conversations, health, market, query, research


api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(market.router)
api_router.include_router(query.router)
api_router.include_router(research.router)
api_router.include_router(conversations.router)
api_router.include_router(canvas.router)
