"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base
from app.api import api_router
from app.services.scheduler import get_data_scheduler

# Import fetchers to register them
import app.fetchers  # noqa: F401

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

# Create database tables
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    # --- Startup ---
    scheduler = get_data_scheduler()
    if settings.SCHEDULER_ENABLED:
        scheduler.start()
        logging.getLogger("main").info("Daily scheduler started")
    else:
        logging.getLogger("main").info("Daily scheduler disabled (SCHEDULER_ENABLED=false)")

    yield

    # --- Shutdown ---
    scheduler.stop()
    logging.getLogger("main").info("Daily scheduler stopped")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="数据终端 - 统一数据采集与管理系统",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router)


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Data Terminal API",
        "version": "0.2.0",
        "docs": "/docs",
        "scheduler": "enabled" if settings.SCHEDULER_ENABLED else "disabled",
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    scheduler = get_data_scheduler()
    return {
        "status": "healthy",
        "scheduler_running": scheduler.is_running,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
