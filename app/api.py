from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from fastapi import HTTPException
from app.services.yandex_auth import get_yandex_token, get_yandex_user_info
from app.security import create_access_token
from app.db.database import get_db
from app.schemas.schemas import UserCreate,AudioCreate, AudioOut, UserUpdate, Token
from app.crud import user_crud, audio_crud
from app.models.user import User
from app.services.auth import get_current_user
from pathlib import Path
import re

router = APIRouter()

@router.post("/auth/yandex", response_model=Token)
async def auth_yandex(code: str, db: AsyncSession = Depends(get_db)):
    try:
        token_data = await get_yandex_token(code)
        user_info = await get_yandex_user_info(token_data["access_token"])
        
        if not user_info.get("default_email"):
            raise HTTPException(status_code=400, detail="Email not provided by Yandex")

        user = await user_crud.get_user_by_yandex_id(db, yandex_id=user_info["id"])
        if not user:
            user = await user_crud.get_user_by_email(db, email=user_info["default_email"])
            if user:
                user = await user_crud.update_user(db, user.id, UserUpdate(yandex_id=user_info["id"]))
            else:
                user_in = UserCreate(
                    email=user_info["default_email"],
                    username=user_info["login"],
                    yandex_id=user_info["id"],
                    password=None
                )
                user = await user_crud.create_user(db, user_in)

        access_token = create_access_token(
            data={"sub": user.email, "is_superuser": user.is_superuser}
        )
        return {"access_token": access_token, "token_type": "bearer"}
    
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=400, detail=f"Yandex API error: {str(e)}")

ALLOWED_EXTENSIONS = {"mp3", "wav", "ogg"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

@router.post("/audio/upload", response_model=AudioOut)
async def upload_audio(
    file: UploadFile = File(...),
    name: str = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    file_ext = Path(file.filename).suffix[1:].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, detail="Invalid file extension")

    if file.size > MAX_FILE_SIZE:
        raise HTTPException(400, detail="File too large")

    clean_name = re.sub(r'[^\w.-]', '', name or Path(file.filename).stem)
    if not clean_name:
        clean_name = "audio"
    filename = f"{clean_name}.{file_ext}"

    upload_dir = Path(f"static/audios/user_{current_user.id}")
    upload_dir.mkdir(exist_ok=True, parents=True)
    file_path = upload_dir / filename

    try:
        contents = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(contents)
    except Exception as e:
        raise HTTPException(500, detail=f"Error saving file: {str(e)}")

    audio_in = AudioCreate(name=filename)
    audio = await audio_crud.create_audio(
        db, 
        audio_in=audio_in,
        owner_id=current_user.id,
        file_path=str(file_path)
    )
    return audio

@router.get("/audio/", response_model=list[AudioOut])
def list_audios(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return audio_crud.get_multi_by_owner(db, owner_id=current_user.id)