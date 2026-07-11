from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
import httpx
import os
from models import User

SUPABASE_JWKS_URL = os.getenv("SUPABASE_JWKS_URL")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

_jwks_cache = None

async def get_jwks():
    global _jwks_cache
    if _jwks_cache is None:
        async with httpx.AsyncClient() as client:
            resp = await client.get(SUPABASE_JWKS_URL)
            resp.raise_for_status()
            _jwks_cache = resp.json()
    return _jwks_cache


async def decode_token(token: str):
    try:
        jwks = await get_jwks()
        unverified_header = jwt.get_unverified_header(token)
        key = next((k for k in jwks["keys"] if k["kid"] == unverified_header["kid"]), None)
        if key is None:
            raise HTTPException(status_code=401, detail="Invalid token key")

        payload = jwt.decode(
            token,
            key,
            algorithms=["ES256"],   # use ["HS256"] + SUPABASE_JWT_SECRET if your project is still on legacy
            audience="authenticated",
        )
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = await decode_token(token)
    user_uuid = payload.get("sub")
    if not user_uuid:
        raise HTTPException(status_code=401, detail="Invalid token")

    return User(user_uuid=user_uuid, email=payload.get("email"))