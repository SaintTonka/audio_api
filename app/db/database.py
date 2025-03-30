from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from typing import AsyncGenerator
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import text
from app.config import settings
import asyncio
import logging

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.database_url,
    pool_size=20,
    max_overflow=10,
    echo=True,
    connect_args={"server_settings": {"jit": "off"}}  
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

Base = declarative_base()

async def create_all_async():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def check_db_health() -> bool:
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

async def shutdown_db():
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_all_async())