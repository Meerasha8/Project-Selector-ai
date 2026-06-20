from fastapi import FastAPI,Depends,HTTPException
import os
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel
from database import SessionLocal,engine
from models import Projects,Base,Skills
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

class Project(BaseModel):
    title : str
    description : str
    
class Skill(BaseModel):
    title : str
    description : str

class Message(BaseModel):
    message : str

class Skill(BaseModel):
    skill_name: str
    experience: str
    
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
            "content": f"Your job is to select 3 jobs from the given data which suits the job description the best and provide rating out of 10 for each of the projects also tell whether its suitable or not for the job description with the reason with 2 lines on what reason this is the best choice->{data} ,this is the job description:{message}, if there is no suitable one give only the one which match to the title if the rating seems to be less than 7 mark it as not suitable, also if received any inapproriate message dont proceed return empty stuff"
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

@dapp.post("/add-skill")
def add_skill(skill:Skill,db: Session = Depends(get_db)):
    data = Skills(name=skill.title,description=skill.description)
    db.add(data)
    db.commit()
    db.refresh(data)
    return {"message":"data added successfully","Added Skill":data.name}

@dapp.get("/get-all-projects",)
def get_all_projects(db: Session = Depends(get_db)):
    
    stmt = select(Projects)
    
    result = db.execute(stmt).scalars().all()
    
    return {"projects":result}

@dapp.get("/get-all-skills")
def get_all_skills(db: Session = Depends(get_db)):
    stmt = select(Skills)
    result=db.execute(stmt).scalars().all()
    return {"skills":result}

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
    
    return {"message":"project was deleted successfully","Deleted project":result.name}

@dapp.get("/skills")
def get_skills(db: Session = Depends(get_db)):
    stmt = select(Skills)
    
    result = db.execute(stmt).scalars().all()
    
    return {"Skills":result}

@dapp.post("/add-skills")
def add_skills(skill:Skill,db: Session = Depends(get_db)):
    data = Skills(skill_name=skill.skill_name,how_much_known=skill.experience)
    db.add(data)
    db.commit()
    db.refresh(data)
    return {"message":f"data added successfully {skill.skill_name,skill.experience}"}
    
    
    
@dapp.delete("/delete-skill/{skill_id}")
def delete_skill(skill_id:int,db: Session = Depends(get_db)):
    result = db.get(Skills,skill_id)
    if not result:
        raise HTTPException(status_code=404, detail="Skill not found")
    db.delete(result)
    db.commit()
    return {"message":"skill was deleted successfully","Deleted skill": result.name}    
    
    



