"""Application configuration."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # App
    APP_NAME: str = "Data Terminal"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite:///./data/data_terminal.db"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # Scheduler
    SCHEDULER_ENABLED: bool = True  # Set to False to disable daily auto-updates
    
    class Config:
        env_file = ".env"


settings = Settings()
