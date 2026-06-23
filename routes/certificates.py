from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from models import Certificates,User
from dependencies import get_db
from pydantic import BaseModel 
from auth.dependencies import get_current_user

class Certificate(BaseModel):
    certificate_issuer: str
    certificate_name: str
    
router=APIRouter(
    prefix="/certificates",
    tags=["Certificates"]
)

@router.get("/")
def get_all_certificates(db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    query = select(Certificates.where(Certificates.user_uuid == current_user.user_uuid))
    certificates = db.scalars(query).all()
    return {"certificates": certificates}

@router.get("/get-certificate/{certificate_id}")
def get_certificate(certificate_id:int,db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    certificate=db.get(Certificates,certificate_id)
    if not certificate:
        raise HTTPException(status_code=404,detail="Certificate not found for the given id")
    if certificate.user_uuid != current_user.user_uuid:
        raise HTTPException(status_code=403,detail="You do not have permission to view this certificate")
    return certificate

@router.post("/add-certificate")
def add_certificate(certificate:Certificate,db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    certificate=Certificates(certificate_issuer=certificate.certificate_issuer,certificate_name=certificate.certificate_name,user_uuid=current_user.user_uuid)
    db.add(certificate)
    db.commit()
    db.refresh(certificate)
    return {"Certificate added successfully": certificate}


@router.put("/edit-certificate/{certificate_id}")
def edit_certificate(certificate:Certificate,certificate_id:int,db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):        
    curr_certificate=db.get(Certificates,certificate_id)
    if not certificate:
        raise HTTPException(status_code=404,detail="Certificate not found for the given id")
    if curr_certificate.user_uuid != current_user.user_uuid:
        raise HTTPException(status_code=403,detail="You do not have permission to edit this certificate")
    curr_certificate.certificate_issuer=certificate.certificate_issuer
    curr_certificate.certificate_name=certificate.certificate_name
    db.commit()
    db.refresh(curr_certificate)
    return {"Certificate updated": curr_certificate}


@router.delete("/delete-certificate/{certificate_id}")    
def delete_certificate(certificate_id:int,db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    certificate=db.get(Certificates,certificate_id)
    if not certificate:
        raise HTTPException(status_code=404,detail="Certificate not found for the given id")
    if certificate.user_uuid != current_user.user_uuid:
        raise HTTPException(status_code=403,detail="You do not have permission to delete this achievement")
    
    db.delete(certificate)
    db.commit()
    return {"Certificate deleted": certificate}