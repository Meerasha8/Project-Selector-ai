import os
import tempfile
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from dependencies import get_db
from models import (
    Achievements,
    Certificates,
    Educations,
    Internship,
    Projects,
    Skills,
    User,
    UserDetails,
)
from resume_service import ResumeContent, ResumeService

router = APIRouter(prefix="/resume", tags=["Resume"])


class ResumeRequest(BaseModel):
    job_description: str


class ResumeJobResponse(BaseModel):
    job_id: str
    status: str
    message: str


class ResumeGenerationStatusResponse(BaseModel):
    job_id: str
    status: str
    download_url: str | None = None
    error: str | None = None


_jobs: dict[str, dict[str, Any]] = {}


def _collect_user_resume_data(db: Session, user_uuid: str) -> dict[str, Any]:
    user_details = db.query(UserDetails).filter(UserDetails.user_uuid == user_uuid).first()
    education = db.query(Educations).filter(Educations.user_uuid == user_uuid).all()
    certificates = db.query(Certificates).filter(Certificates.user_uuid == user_uuid).all()
    internship = db.query(Internship).filter(Internship.user_uuid == user_uuid).all()
    achievements = db.query(Achievements).filter(Achievements.user_uuid == user_uuid).all()
    projects = db.query(Projects).filter(Projects.user_uuid == user_uuid).all()
    skills = db.query(Skills).filter(Skills.user_uuid == user_uuid).all()

    return {
        "user_details": {
            "name": user_details.name if user_details else None,
            "email": user_details.email_id if user_details else None,
            "phone": user_details.mobile_number if user_details else None,
            "github": user_details.github_url if user_details else None,
            "linkedin": user_details.linkedin_url if user_details else None,
            "portfolio": user_details.portfolio_link if user_details else None,
        },
        "education": [
            {
                "course_name": item.course_name,
                "college_name": item.college_name,
                "location": item.location,
                "start_year": item.start_year,
                "end_year": item.end_year,
                "cgpa": item.cgpa,
            }
            for item in education
        ],
        "certificates": [
            {"certificate_name": item.certificate_name, "certificate_issuer": item.certificate_issuer}
            for item in certificates
        ],
        "internship": [
            {
                "role": item.role,
                "company_name": item.company_name,
                "description": item.description,
                "Duration": item.Duration,
            }
            for item in internship
        ],
        "achievements": [{"description": item.description} for item in achievements],
        "projects": [
            {
                "name": item.name,
                "description": item.description,
                "tech_stack": item.tech_stack,
                "github_url": item.github_url,
                "live_link": item.live_link,
            }
            for item in projects
        ],
        "skills": [{"name": item.name, "description": item.description} for item in skills],
    }


@router.post("/generate", response_model=ResumeJobResponse)
def generate_resume_job(
    payload: ResumeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_uuid = current_user.user_uuid
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "status": "queued",
        "user_uuid": user_uuid,
        "job_description": payload.job_description,
        "db": db,
    }

    try:
        user_data = _collect_user_resume_data(db, user_uuid)
        service = ResumeService()
        content = service.select_resume_content(payload.job_description, user_data)
        doc_bytes = service.render_docx(content, user_data.get("user_details"))
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp_file:
            tmp_file.write(doc_bytes)
            file_path = tmp_file.name
        _jobs[job_id]["status"] = "completed"
        _jobs[job_id]["file_path"] = file_path
        _jobs[job_id]["download_url"] = f"/resume/generate/{job_id}/download"
    except Exception as exc:
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["error"] = str(exc)

    return ResumeJobResponse(job_id=job_id, status=_jobs[job_id]["status"], message="Resume generation completed" if _jobs[job_id]["status"] == "completed" else "Resume generation failed")


@router.get("/generate/{job_id}", response_model=ResumeGenerationStatusResponse)
def resume_job_status(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return ResumeGenerationStatusResponse(
        job_id=job_id,
        status=job["status"],
        download_url=job.get("download_url"),
        error=job.get("error"),
    )


@router.post("/generate/{job_id}/download")
def resume_job_download(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "completed" or not job.get("file_path"):
        raise HTTPException(status_code=409, detail="Resume generation is not complete yet")

    response = FileResponse(job["file_path"], media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    response.headers["Content-Disposition"] = f"attachment; filename=resume-{job_id}.docx"
    return response
