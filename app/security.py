from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from app.config import settings
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12 
)

class TokenPayload(BaseModel):
    sub: str
    exp: datetime
    is_superuser: bool = False

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Сравнение пароля с хешем"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification failed: {str(e)}")
        return False

def get_password_hash(password: str) -> str:
    """Генерация хеша пароля"""
    if len(password) < 8:
        raise ValueError("Password too short")
    return pwd_context.hash(password)

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
    refresh: bool = False
) -> str:
    """Создание JWT токена"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or 
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({
        "exp": expire,
        "type": "refresh" if refresh else "access"
    })
    try:
        return jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
    except Exception as e:
        logger.error(f"Token creation failed: {str(e)}")
        raise

def verify_token(token: str) -> TokenPayload:
    """Верификация JWT токена"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return TokenPayload(**payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token expired"
        )
    except jwt.JWTError as e:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )