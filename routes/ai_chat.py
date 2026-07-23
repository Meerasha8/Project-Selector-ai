import os
from uuid import UUID

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from groq import Groq
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from dependencies import get_db
from embedding_utils import embed_text
from models import (
    Achievements,
    Certificates,
    DocumentEmbedding,
    Educations,
    Internship,
    Projects,
    Skills,
    User,
    UserDetails,
)

load_dotenv()


class AskRequest(BaseModel):
    question: str


class SourceReference(BaseModel):
    source_table: str
    source_id: int


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceReference]


router = APIRouter(prefix="/ai", tags=["AI Service"])


def _get_groq_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is not configured")
    return Groq(api_key=api_key)


def _iter_structured_profile_rows(db: Session, user_uuid: UUID):
    tables = [
        ("projects", Projects),
        ("skills", Skills),
        ("education", Educations),
        ("internship", Internship),
        ("achievements", Achievements),
        ("certificates", Certificates),
        ("user_details", UserDetails),
    ]

    for source_table, model in tables:
        rows = db.query(model).filter(model.user_uuid == user_uuid).all()
        for row in rows:
            yield source_table, row


def _structured_profile_context(db: Session, user_uuid: UUID) -> list[tuple[str, int, str]]:
    chunks: list[tuple[str, int, str]] = []
    for source_table, row in _iter_structured_profile_rows(db, user_uuid):
        if source_table == "projects":
            content = f"Project: {row.name}. Description: {row.description}. Tech stack: {row.tech_stack}. GitHub: {row.github_url}. Live link: {row.live_link}."
        elif source_table == "skills":
            content = f"Skill: {row.name}. Description: {row.description}."
        elif source_table == "education":
            content = f"Education: {row.course_name}. CGPA: {row.cgpa}. Years: {row.start_year}-{row.end_year}. College: {row.college_name}. Location: {row.location}."
        elif source_table == "user_details":
            content = (
                f"User details: name={row.name or ''}; mobile={row.mobile_number or ''}; email={row.email_id or ''}; "
                f"github={row.github_url or ''}; linkedin={row.linkedin_url or ''}; portfolio={row.portfolio_link or ''}; "
                f"location={row.location or ''}; summary={row.profession_summary or ''}."
            )
        elif source_table == "internship":
            content = f"Internship: {row.company_name}. Role: {row.role}. Description: {row.description}. Duration: {row.Duration}."
        elif source_table == "achievements":
            content = f"Achievement: {row.description}."
        elif source_table == "certificates":
            content = f"Certificate: {row.certificate_name}. Issuer: {row.certificate_issuer}."
        else:
            continue
        chunks.append((source_table, row.id, content))
    return chunks


@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Ask the profile assistant",
    description="Answer a question about the authenticated user's profile by combining stored embeddings and structured profile data.",
)
def ask(
    payload: AskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_uuid = UUID(current_user.user_uuid)
    question_embedding = embed_text(payload.question)

    context_chunks: list[tuple[str, int, str]] = []
    try:
        vector_query = (
            select(DocumentEmbedding)
            .where(DocumentEmbedding.user_uuid == user_uuid)
            .order_by(DocumentEmbedding.embedding.cosine_distance(question_embedding))
            .limit(5)
        )
        embedding_rows = db.execute(vector_query).scalars().all()
    except Exception:
        embedding_rows = []

    if embedding_rows:
        for row in embedding_rows:
            if row.content:
                context_chunks.append((row.source_table, row.source_id, row.content))

    if not context_chunks or len(context_chunks) < 2:
        context_chunks = _structured_profile_context(db, user_uuid)

    if not context_chunks:
        raise HTTPException(status_code=404, detail="No profile data found for this user")

    context = "\n\n".join(
        f"[{source_table} #{source_id}] {content}" for source_table, source_id, content in context_chunks
    )

    try:
        client = _get_groq_client()
        completion = client.chat.completions.create(
            model=os.getenv("GROQ_CHAT_MODEL", "llama-3.3-70b-versatile"),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are answering questions about a single user's professional profile using only the provided context. "
                        "If the answer isn't in the context, say you don't have that information — don't invent details."
                    ),
                },
                {"role": "user", "content": f"Question: {payload.question}\n\nContext:\n{context}"},
            ],
            temperature=0.2,
            max_tokens=400,
        )
        answer = completion.choices[0].message.content
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Groq request failed: {exc}") from exc

    sources = [
        SourceReference(source_table=source_table, source_id=source_id)
        for source_table, source_id, _ in context_chunks
    ]
    return AskResponse(
        answer=answer or "I don't have that information in the provided context.",
        sources=sources,
    )

