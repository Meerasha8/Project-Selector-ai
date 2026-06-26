from fastapi import APIRouter, Depends, HTTPException
from pydantic import HttpUrl,EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import select
from models import UserDetails
from dependencies import get_db
from auth.dependencies import get_current_user
from pydantic import BaseModel 

class UserDetail(BaseModel):
    name:str
    mobile_number:str
    email_id:EmailStr
    github_url:HttpUrl
    linkedin_url:HttpUrl
    portfolio_link:HttpUrl
    location:str
    profession_summary:str
    
    

router = APIRouter(
    prefix="/user-details",
    tags=["User Details"]
)

# to get user details
@router.get("/")
def get_details(db: Session = Depends(get_db)):
    details = db.execute(select(UserDetails)).scalars().all()
    return details


# to add completely a new user_details
@router.post("/add-details/")
def add_user_details(details:UserDetail,current_user=Depends(get_current_user),db: Session = Depends(get_db)):
    new_details=UserDetails(name=details.name,mobile_number=details.mobile_number,email_id=details.email_id,github_url=details.github_url,linkedin_url=details.linkedin_url,portfolio_link=details.portfolio_link,location=details.location,profession_summary=details.profession_summary,user_uuid=current_user.user_uuid)
    db.add(new_details)
    db.commit()
    db.refresh(new_details)
    return {"message":"User details added successfully"}

#to edit things in the skill
@router.put("/edit-details/{user_id}")
def edit_details(user_id:int,user_details:UserDetail,current_user=Depends(get_current_user),db: Session = Depends(get_db)):
    details=db.get(UserDetails,user_id)
    if not details:
        raise HTTPException(status_code=404,detail="User details not found for the given id")
    if details.user_uuid != current_user.user_uuid:
        raise HTTPException(status_code=403, detail="Unauthorized")
    details.name=user_details.name
    details.mobile_number=user_details.mobile_number
    details.email_id=user_details.email_id
    details.github_url=user_details.github_url
    details.linkedin_url=user_details.linkedin_url
    details.portfolio_link=user_details.portfolio_link
    details.location=user_details.location
    details.profession_summary=user_details.profession_summary
    db.commit()
    db.refresh(details)
    return {"message":"Details updated successfully"}

#delete route is unnecessary

