import json
import os
import tempfile
from typing import Any

from docx import Document
from docx.shared import Inches, Pt
from fastapi import HTTPException
from groq import Groq
from pydantic import BaseModel


class ResumeContent(BaseModel):
    summary: str
    skills: list[str]
    experience: list[dict[str, Any]]
    projects: list[dict[str, Any]]
    education: list[dict[str, Any]]
    certificates: list[dict[str, Any]]


class ResumeService:
    def __init__(self, api_key: str | None = None):
        self.client = Groq(api_key=api_key) if api_key else None
        if self.client is None:
            self.client = Groq(api_key=os.getenv("GROQ_API_KEY")) if os.getenv("GROQ_API_KEY") else None

    def select_resume_content(self, job_description: str, user_data: dict[str, Any]) -> ResumeContent:
        if self.client is None:
            raise HTTPException(status_code=500, detail="GROQ_API_KEY is not configured")

        raw_payload = json.dumps(user_data, ensure_ascii=False, indent=2)
        schema = {
            "summary": "string",
            "skills": ["string"],
            "experience": [
                {"role": "string", "company": "string", "duration": "string", "highlights": ["string"]}
            ],
            "projects": [{"name": "string", "highlights": ["string"]}],
            "education": [
                {
                    "course_name": "string",
                    "college_name": "string",
                    "location": "string",
                    "start_year": "number",
                    "end_year": "number",
                    "cgpa": "number",
                }
            ],
            "certificates": [{"certificate_name": "string", "certificate_issuer": "string"}],
        }
        prompt = (
            "You are selecting content for a one-page resume tailored to a job description. "
            "Use only the provided user data. Select only the most relevant projects, skills, experience, education, and certificates. "
            "Rewrite bullets concisely, action-verb-first, and quantified where possible. "
            "Return strict JSON matching this schema: " + json.dumps(schema) + ". "
            "Do not include prose outside the JSON."
        )

        for attempt in range(2):
            try:
                response = self.client.chat.completions.create(
                    model=os.getenv("GROQ_CHAT_MODEL", "llama-3.3-70b-versatile"),
                    messages=[
                        {"role": "system", "content": "Return only valid JSON matching the requested schema."},
                        {
                            "role": "user",
                            "content": f"Job description:\n{job_description}\n\nUser data:\n{raw_payload}\n\nInstructions:\n{prompt}",
                        },
                    ],
                    temperature=0.2,
                    max_tokens=1200,
                )
                content = response.choices[0].message.content or "{}"
                parsed = json.loads(content)
                return ResumeContent(**parsed)
            except Exception:
                if attempt == 1:
                    break

        raise HTTPException(status_code=502, detail="Groq failed to return valid resume JSON")

    def render_docx(self, content: ResumeContent, user_details: dict[str, Any] | None = None) -> bytes:
        document = Document()
        sections = document.sections
        for section in sections:
            section.top_margin = Inches(0.35)
            section.bottom_margin = Inches(0.35)
            section.left_margin = Inches(0.4)
            section.right_margin = Inches(0.4)

        style = document.styles["Normal"]
        style.font.name = "Calibri"
        style.font.size = Pt(10.5)

        heading_style = document.styles["Heading 1"]
        heading_style.font.size = Pt(12)
        heading_style.font.bold = True

        title = document.add_paragraph()
        title.alignment = 1
        run = title.add_run((user_details or {}).get("name") or "Resume")
        run.bold = True
        run.font.size = Pt(14)

        contact = document.add_paragraph()
        contact.alignment = 1
        contact_lines = []
        if (user_details or {}).get("email"):
            contact_lines.append(user_details["email"])
        if (user_details or {}).get("phone"):
            contact_lines.append(user_details["phone"])
        if (user_details or {}).get("github"):
            contact_lines.append(user_details["github"])
        if (user_details or {}).get("linkedin"):
            contact_lines.append(user_details["linkedin"])
        if (user_details or {}).get("portfolio"):
            contact_lines.append(user_details["portfolio"])
        if contact_lines:
            contact.add_run(" | ".join(contact_lines))

        if content.summary:
            document.add_paragraph().add_run("Summary").bold = True
            document.add_paragraph(content.summary)

        if content.skills:
            document.add_paragraph().add_run("Skills").bold = True
            skills_paragraph = document.add_paragraph()
            skills_paragraph.add_run(", ".join(content.skills[:12]))

        if content.experience:
            document.add_paragraph().add_run("Experience").bold = True
            for item in content.experience[:3]:
                p = document.add_paragraph()
                p.add_run(f"{item.get('role', '')} — {item.get('company', '')}").bold = True
                if item.get("duration"):
                    p.add_run(f"  ({item['duration']})")
                for bullet in (item.get("highlights") or [])[:4]:
                    bullet_paragraph = document.add_paragraph()
                    bullet_paragraph.style = "List Bullet"
                    bullet_paragraph.add_run(str(bullet))

        if content.projects:
            document.add_paragraph().add_run("Projects").bold = True
            for item in content.projects[:3]:
                p = document.add_paragraph()
                p.add_run(item.get("name", "Project")).bold = True
                for bullet in (item.get("highlights") or [])[:4]:
                    bullet_paragraph = document.add_paragraph()
                    bullet_paragraph.style = "List Bullet"
                    bullet_paragraph.add_run(str(bullet))

        if content.education:
            document.add_paragraph().add_run("Education").bold = True
            for item in content.education[:3]:
                p = document.add_paragraph()
                p.add_run(f"{item.get('course_name', '')} — {item.get('college_name', '')}").bold = True
                if item.get("location"):
                    p.add_run(f" ({item.get('location')})")

        if content.certificates:
            document.add_paragraph().add_run("Certificates").bold = True
            for item in content.certificates[:3]:
                document.add_paragraph().add_run(f"- {item.get('certificate_name', '')} — {item.get('certificate_issuer', '')}")

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp_file:
            document.save(tmp_file.name)
            tmp_file.flush()
            tmp_file.seek(0)
            return tmp_file.read()
