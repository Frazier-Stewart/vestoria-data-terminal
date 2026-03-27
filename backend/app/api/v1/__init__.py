"""API router package."""
from fastapi import APIRouter

from app.api.v1 import assets, prices, update, indicators, scheduler

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(assets.router)
api_router.include_router(prices.router)
api_router.include_router(update.router)
api_router.include_router(indicators.router)
api_router.include_router(scheduler.router)
