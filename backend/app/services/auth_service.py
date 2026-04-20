"""Authentication service."""
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.admin import Admin


class AuthService:
    """Service for auth helpers."""

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify bcrypt password."""
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception:
            return False

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash password with bcrypt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def create_access_token(data: dict) -> str:
        """Create JWT access token."""
        payload = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
        payload.update({"exp": expire})
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> Optional[str]:
        """Return username from valid token."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            username = payload.get("sub")
            if not username:
                return None
            return username
        except JWTError:
            return None

    @staticmethod
    def authenticate(db: Session, username: str, password: str) -> Optional[Admin]:
        """Authenticate admin by username and password."""
        admin = db.query(Admin).filter(Admin.username == username).first()
        if not admin:
            return None
        if not AuthService.verify_password(password, admin.password_hash):
            return None
        return admin
