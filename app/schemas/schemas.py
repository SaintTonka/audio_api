from pydantic import BaseModel, EmailStr, field_validator, ConfigDict, Field
from typing import Optional
import re
from datetime import datetime

class AudioBase(BaseModel):
    name: str = Field(..., description="Название аудиофайла")

class UserBase(BaseModel):
    email: EmailStr = Field(..., description="Email пользователя")
    username: str = Field(..., description="Имя пользователя")
    yandex_id: Optional[str] = Field(None, description="ID пользователя в Яндекс")

def validate_username(name: str) -> str:
    if not re.match(r'^[a-zA-Z0-9_-]{3,10}$', name):
        raise ValueError('Username должен содержать 3-10 символов (буквы, цифры, _-)')
    return name

class AudioCreate(BaseModel):
    name: str = Field(..., description="Имя для аудиофайла")

class AudioOut(AudioBase):
    id: int
    path: str
    owner_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class UserCreate(UserBase):
    password: Optional[str] = Field(None, description="Пароль (не используется при Яндекс-авторизации)")
    is_superuser: bool = Field(False, description="Флаг суперпользователя")

    @field_validator('username')
    def validate_username(cls, v: str) -> str:
        return validate_username(v)

class UserOut(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator('username')
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_username(v)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    sub: str 
    is_superuser: bool = False