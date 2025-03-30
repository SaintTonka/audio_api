from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models.user import User
from app.db import database
from app.crud.user_crud import get_user_by_email
import logging

logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/yandex")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(database.get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_aud": False}
        )
        email: str = payload.get("sub")
        if not email:
            logger.error("No email in JWT token")
            raise credentials_exception
            
        user = await get_user_by_email(db, email=email)
        if user is None or not user.is_active:
            logger.error(f"User not found or inactive: {email}")
            raise credentials_exception
        return user
        
    except JWTError as e:
        logger.error(f"JWT error: {str(e)}")
        raise credentials_exception