"""Admin model for authentication."""
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime

from app.core.database import Base


class Admin(Base):
    """Admin user."""

    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
