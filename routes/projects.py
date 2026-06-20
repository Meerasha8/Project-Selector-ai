from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from models import Projects
from dependencies import get_db
from pydantic import BaseModel 

class Project(BaseModel):
    name:str
    description:str
    tech_stack:str
    github_url:str
    live_link:str
    

router = APIRouter(
    prefix="/projects",
    tags=["Projects"]
)

# to get all the projects
@router.get("/")
def get_all_projects(db: Session = Depends(get_db)):
    query = select(Projects)
    projects = db.scalars(query).all()
    return {"projects":projects}
    
# to get a individual projects
@router.get("/{project_id}")
def get_project(project_id:int,db: Session = Depends(get_db)):
    project = db.get(Projects,project_id)
    return {"name":project.name,"description":project.description,"techstack":project.tech_stack,"github_url":project.github_url,"live_link":project.live_link}

# to add completely a new project to db
@router.post("/add-project")
def add_project(project:Project,db: Session = Depends(get_db)):
    new_project = Projects(name=project.name,description=project.description,tech_stack=project.tech_stack,github_url=project.github_url,live_link=project.live_link)
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return {"message":f"Project:{project.name} have been added successfully"}


#to edit things in the projects
@router.put("/edit-project/{project_id}")
def edit_project(project:Project,project_id:int,db: Session = Depends(get_db)):
    curr_project = db.query(Projects).filter(Projects.id==project_id).first()
    curr_project.name = project.name
    curr_project.description = project.description
    curr_project.tech_stack = project.tech_stack
    curr_project.github_url = project.github_url
    curr_project.live_link = project.live_link
    db.commit()
    db.refresh(curr_project)
    
    return {"message":f"Project:{project.name} has been updated successfully"}    
    
    
#to delete a project in the db
@router.delete("/delete-project/{project_id}")
def delete_project(project_id:int,db: Session = Depends(get_db)):
    project = db.get(Projects,project_id)
    db.delete(project)
    db.commit()
    return {"message":f"Project:{project.name} have been deleted successfully"}

