"""Application configuration."""
from typing import Optional
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

    # Auth
    SECRET_KEY: str = "change-this-secret-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7
    
    # Scheduler
    SCHEDULER_ENABLED: bool = True  # Set to False to disable daily auto-updates
    
    # Proxy (e.g. socks5://127.0.0.1:1082 or http://127.0.0.1:1089)
    # Set in .env file to enable, leave empty to disable
    PROXY_URL: Optional[str] = None
    
    class Config:
        env_file = ".env"


settings = Settings()
