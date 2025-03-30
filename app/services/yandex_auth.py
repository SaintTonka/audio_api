import httpx
from fastapi import HTTPException
from app.config import settings
from cachetools import TTLCache
yandex_cache = TTLCache(maxsize=1000, ttl=300)

async def get_yandex_token(code: str):
    async with httpx.AsyncClient() as client:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": settings.YANDEX_CLIENT_ID,
            "client_secret": settings.YANDEX_CLIENT_SECRET,
            "redirect_uri": settings.YANDEX_REDIRECT_URI,
        }
        response = await client.post("https://oauth.yandex.ru/token", data=data)
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get Yandex token")
        
        return response.json()

async def get_yandex_user_info(access_token: str):
    async with httpx.AsyncClient(timeout=10.0) as client:
        headers = {"Authorization": f"OAuth {access_token}"}
        response = await client.get(
            "https://login.yandex.ru/info",
            headers={"Authorization": f"OAuth {access_token}"},
            params={"format": "json"} 
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info from Yandex")
        
        return response.json()
    
async def get_yandex_user_info_cached(access_token: str):
    if access_token in yandex_cache:
        return yandex_cache[access_token]
    
    data = await get_yandex_user_info(access_token)
    yandex_cache[access_token] = data
    return data