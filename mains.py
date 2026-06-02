from fastapi import FastAPI,Depends
import os
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel
from database import SessionLocal,engine
from models import Projects,Base
from sqlalchemy.orm import Session
from sqlalchemy import select
import json
from fastapi.middleware.cors import CORSMiddleware

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
                            "suitable":{"type":"string","enum":["Yes","No"]}
                        },
                        "required": [
                            "project_name",
                            "project_description",
                            "rating",
                            "suitable"
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

class Project(BaseModel):
    title : str
    description : str

class Message(BaseModel):
    message : str
    
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


@dapp.get("/")
def heathy_check():
    return {"status":"the service is running"}

@dapp.post("/ai-analysis")
def ai_response(message:Message,db: Session = Depends(get_db)):
    stmt = select(Projects)
    all_projects = db.scalars(stmt).all()
    data = {}
    for i in all_projects:
        data[i.name] = i.description
    chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": f"Your job is to select 3 jobs from the given data which suits the job description the best and provide rating for each of the projects also tell whether its suitable or not for the job description->{data} ,this is the job description:{message}"
        }
    ],
    response_format={
    "type": "json_schema",
    "json_schema": {
        "name": "Project_Details",
        "strict": True,
        "schema": Schema}
    },
    model="openai/gpt-oss-120b",
)

    data = chat_completion.choices[0].message.content
    
    result = json.loads(data)
    
    return result


#manage task routes
@dapp.post("/add-project")
def add_project(project:Project,db: Session = Depends(get_db)):
    
    data = Projects(name=project.title,description=project.description)
    db.add(data)
    db.commit()
    db.refresh(data)
    return {"message":f"data added successfully {data}"}

@dapp.get("/get-all-projects",)
def get_all_projects(db: Session = Depends(get_db)):
    
    stmt = select(Projects)
    
    result = db.execute(stmt).scalars().all()
    
    return {"projects":result}

@dapp.get("/get-project/{project_id}")
def get_project(project_id:int,db: Session = Depends(get_db)):
    
    stmt = select(Projects).where(Projects.id == project_id)
    
    result = db.execute(stmt).scalars().all()
    
    output = {"title":result[0].name,"description":result[0].description}
    return output

@dapp.put("/edit-project/{project_id}")
def edit_project(project_id:int,project:Project,db: Session = Depends(get_db)):
    
    stmt = select(Projects).where(Projects.id == project_id)
    result = db.execute(stmt).scalars().one()
    
    if project.title != "":
        result.name = project.title
    
    if project.description != "":
        result.description = project.description
    
    db.commit()
    
    return {"message":"data updated successfully"}

@dapp.delete("/delete-project/{project-id}")
def delete_project(project_id:int,db: Session = Depends(get_db)):
    
    result = db.get(Projects,project_id)
    db.delete(result)
    db.commit()
    
    return {"message":"project was deleted successfully"}
    
    
    
    



