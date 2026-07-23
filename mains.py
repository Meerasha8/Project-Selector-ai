import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth import routes
from database import Base, engine
from routes import (
    achievements,
    ai_chat,
    certificates,
    document_embeddings,
    education,
    internship,
    projects,
    resume,
    skills,
    user_details,
)

load_dotenv()

if engine.url.get_backend_name() == "sqlite":
    sqlite_tables = [
        table for table in Base.metadata.sorted_tables if getattr(table, "schema", None) != "auth"
    ]
    Base.metadata.create_all(bind=engine, tables=sqlite_tables)
else:
    Base.metadata.create_all(bind=engine)


dapp = FastAPI(
    title="Project Knowledge API",
    version="1.0.0",
    description="Backend API for a mobile-friendly professional profile assistant, resume generation, and profile CRUD operations.",
)

allowed_origins = [origin.strip() for origin in os.getenv("CORS_ALLOWED_ORIGINS", "*").split(",") if origin.strip()]
dapp.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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
dapp.include_router(document_embeddings.router)
dapp.include_router(resume.router)


@dapp.get("/", tags=["Health"], summary="API root")
def root_health_check():
    return {"status": "the service is running"}


@dapp.get("/health", tags=["Health"], summary="Health check")
def health_check():
    return {"status": "ok"}
