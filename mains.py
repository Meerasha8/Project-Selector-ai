from fastapi import FastAPI,Depends,HTTPException
import os
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel
from database import SessionLocal,engine
from models import Projects,Base,Skills,UserDetails
from sqlalchemy.orm import Session
from sqlalchemy import select
import json
from fastapi.middleware.cors import CORSMiddleware
from routes import projects,skills,internship,certificates,achievements,education,ai_chat,user_details,achievements
from auth import routes

load_dotenv()

Base.metadata.create_all(bind=engine)



Schema ={
            "type": "object",
            "properties": {
                "projects": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "project_name": {"type": "string"},
                            "project_description": {"type": "string"},
                            "rating":{"type":"number"},
                            "suitable":{"type":"string","enum":["Yes","No"]},
                            "reason":{"type":"string"}
                        },
                        "required": [
                            "project_name",
                            "project_description",
                            "rating",
                            "suitable",
                            "reason"
                        ],
                        "additionalProperties": False
                    }
                }
            },
            "required": ["projects"],
            "additionalProperties": False
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_item(db: Session, name: str, description: str):
    db_item = Projects(name=name, description=description)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


    
client = Groq(
    # This is the default and can be omitted
    api_key=os.getenv("GROQ_API_KEY"),
)

dapp = FastAPI()

dapp.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

dapp.include_router(projects.router)
dapp.include_router(skills.router)
dapp.include_router(internship.router)
dapp.include_router(certificates.router)
dapp.include_router(achievements.router)
dapp.include_router(education.router)
dapp.include_router(routes.router)
dapp.include_router(ai_chat.router)
dapp.include_router(user_details.router)
dapp.include_router(achievements.router)
@dapp.get("/")
def heathy_check():
    return {"status":"the service is running"}
