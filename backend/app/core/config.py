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
    
    # Scheduler
    SCHEDULER_ENABLED: bool = True  # Set to False to disable daily auto-updates
    
    # Proxy (e.g. socks5://127.0.0.1:1082 or http://127.0.0.1:1089)
    PROXY_URL: Optional[str] = "socks5://127.0.0.1:1082"
    
    class Config:
        env_file = ".env"


settings = Settings()
