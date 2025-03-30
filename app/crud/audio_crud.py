from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from app.models.audio import Audio
from app.schemas.schemas import AudioCreate

async def create_audio(db: AsyncSession, audio_in: AudioCreate, owner_id: int, file_path: str) -> Audio:
    db_audio = Audio(
        name=audio_in.name,
        path=file_path,
        owner_id=owner_id
    )
    db.add(db_audio)
    await db.commit()
    await db.refresh(db_audio)
    return db_audio

async def get_audio(db: AsyncSession, audio_id: int) -> Audio | None:
    result = await db.execute(select(Audio).filter(Audio.id == audio_id))
    return result.scalars().first()

async def get_audios_by_owner(db: AsyncSession, owner_id: int, skip: int = 0, limit: int = 100) -> list[Audio]:
    result = await db.execute(
        select(Audio)
        .filter(Audio.owner_id == owner_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def delete_user_audio(db: AsyncSession, audio_id: int, owner_id: int) -> None:
    await db.execute(
        delete(Audio)
        .where(Audio.id == audio_id, Audio.owner_id == owner_id)
    )
    await db.commit()

async def update_audio_name(db: AsyncSession, audio_id: int, new_name: str) -> Audio | None:
    await db.execute(
        update(Audio)
        .where(Audio.id == audio_id)
        .values(name=new_name)
    )
    await db.commit()
    return await get_audio(db, audio_id)