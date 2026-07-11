import os
from models import User,Internship,Skills,Certificates,Projects,Achievements
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from dependencies import get_db
from pydantic import BaseModel 
from auth.dependencies import get_current_user
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

class Message(BaseModel):
    message:str
    
router=APIRouter(
    prefix="/ai",
    tags=["AI Service"]
)

client = Groq(
    # This is the default and can be omitted
    api_key=os.getenv("GROQ_API_KEY"),
)

@router.get("/chat")
def chat():
    pass

@router.get("/create-resume")
def create_resume():
    pass

