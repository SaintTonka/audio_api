import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.user import User
from app.security import get_password_hash
from app.schemas.schemas import UserCreate, UserUpdate

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

async def get_user(db: AsyncSession, user_id: int) -> User:
    result = await db.execute(
        select(User).filter(User.id == user_id)
    )
    return result.scalars().first()

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()

async def get_user_by_yandex_id(db: AsyncSession, yandex_id: str) -> User | None:
    result = await db.execute(select(User).filter(User.yandex_id == yandex_id))
    return result.scalars().first()

async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    hashed_password = get_password_hash(user_in.password) if user_in.password else None
    db_user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=hashed_password,
        yandex_id=user_in.yandex_id,
        is_superuser=user_in.is_superuser
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def update_user(db: AsyncSession, user_id: int, user_in: UserUpdate) -> User:
    update_data = user_in.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(**update_data)
    )
    await db.commit()
    return await get_user(db, user_id)

async def delete_user(db: AsyncSession, user_id: int) -> None:
    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()

async def get_users(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 100
) -> list[User]:
    result = await db.execute(
        select(User)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def deactivate_user(
    db: AsyncSession, 
    user_id: int
) -> User:
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(is_active=False)
    )
    await db.commit()
    return await get_user(db, user_id)

async def delete_user_as_superuser(
    db: AsyncSession,
    user_id: int,
    superuser_id: int 
) -> None:
    remover = await get_user(db, superuser_id)
    if not remover or not remover.is_superuser:
        raise PermissionError("Only superuser can delete users")
        
    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()