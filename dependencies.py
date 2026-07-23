import os
from typing import Generator

from fastapi import Depends, HTTPException
from groq import Groq
from supabase import Client, create_client
from sqlalchemy.orm import Session

from auth.dependencies import oauth2_scheme
from database import SessionLocal

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def get_supabase_user_client(token: str = Depends(oauth2_scheme)) -> Client:
    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    if hasattr(client.auth, "set_session"):
        try:
            client.auth.set_session(token, "")
        except Exception:
            pass

    if hasattr(getattr(client, "postgrest", None), "auth"):
        try:
            client.postgrest.auth(token)
        except Exception:
            pass

    return client


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_groq_client() -> Groq:
    if groq_client is None:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is not configured")
    return groq_client