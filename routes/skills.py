from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from models import Skills,User
from dependencies import get_db
from pydantic import BaseModel 
from auth.dependencies import get_current_user

class Skill(BaseModel):
    name:str
    description:str
    

router = APIRouter(
    prefix="/skills",
    tags=["Skills"]
)

# to get all the skills
@router.get("/")
def get_all_skills(db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    skills = db.execute(select(Skills)).scalars().all()
    return skills

# to get a individual skills
@router.get("/{skill_id}")
def get_skill(skill_id:int,db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    skill=db.get(Skills,skill_id)
    if not skill:
        raise HTTPException(status_code=404,detail="Skill not found for the given id")
    if skill.user_uuid != current_user.user_uuid:
        raise HTTPException(status_code=403,detail="You are not allowed to view this skill")
    return skill

# to add completely a new skill to db
@router.post("/add-skill")
def add_skill(skill:Skill,db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    skill=Skills(name=skill.name,description=skill.description,user_uuid=current_user.user_uuid)
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return {"message":f"Skill added successfully{skill}"}

#to edit things in the skill
@router.put("/edit-skill/{skill_id}")
def edit_skill(skill_data:Skill,skill_id:int,db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    skill=db.get(Skills,skill_id)
    if not skill:
        raise HTTPException(status_code=404,detail="Skill not found for the given id")
    if skill.user_uuid != current_user.user_uuid:
        raise HTTPException(status_code=403,detail="You are not allowed to edit this skill")
    skill.name=skill_data.name
    skill.description=skill_data.description
    db.commit()
    db.refresh(skill)
    return {"message":f"Skill updated{skill}"}

#to delete a skill in the db
@router.delete("/delete-skill/{skill_id}")
def delete_skill(skill_id:int,db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    skill=db.get(Skills,skill_id)
    if not skill:
        raise HTTPException(status_code=404,detail="Skill not found")
    if skill.user_uuid != current_user.user_uuid:
        raise HTTPException(status_code=403,detail="You are not allowed to delete this skill")
    db.delete(skill)
    db.commit()
    return {"message":f"Skill deleted{skill}"}

