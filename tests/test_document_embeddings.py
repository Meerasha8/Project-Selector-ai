import os
import unittest
from uuid import UUID
from unittest.mock import patch

os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("SUPABASE_DB_URL", "sqlite:///./test.db")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from auth.dependencies import get_current_user
from database import Base
from dependencies import get_db
from mains import dapp
from models import (
    Achievements,
    Certificates,
    ChatHistory,
    DocumentEmbedding,
    Educations,
    Internship,
    Projects,
    ResumeHistory,
    Skills,
    User,
    UserDetails,
)
from routes import ai_chat as ai_chat_module, resume as resume_module


class DocumentEmbeddingRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        sqlite_tables = [
            Projects.__table__,
            Skills.__table__,
            Educations.__table__,
            Internship.__table__,
            Achievements.__table__,
            Certificates.__table__,
            UserDetails.__table__,
            DocumentEmbedding.__table__,
            ChatHistory.__table__,
            ResumeHistory.__table__,
        ]
        Base.metadata.drop_all(bind=engine, tables=sqlite_tables)
        Base.metadata.create_all(bind=engine, tables=sqlite_tables)

        def override_get_db():
            db = self.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        async def override_get_current_user():
            return User(user_uuid="00000000-0000-0000-0000-000000000001", email="user@example.com")

        dapp.dependency_overrides[get_db] = override_get_db
        dapp.dependency_overrides[get_current_user] = override_get_current_user
        self.client = TestClient(dapp)

        self.session = self.TestingSessionLocal()
        self.session.add(
            Projects(
                name="Portfolio app",
                description="Built a portfolio app",
                tech_stack="FastAPI",
                github_url="https://example.com",
                live_link="https://app.example.com",
                user_uuid="00000000-0000-0000-0000-000000000001",
            )
        )
        self.session.commit()
        self.session.close()

    def test_create_and_list_document_embeddings(self) -> None:
        response = self.client.post(
            "/document-embeddings/",
            json={
                "source_table": "projects",
                "source_id": 1,
                "content": "hello world",
                "embedding": [0.1 + index * 0.001 for index in range(384)],
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["content"], "hello world")
        self.assertEqual(payload["source_table"], "projects")

        list_response = self.client.get("/document-embeddings/")
        self.assertEqual(list_response.status_code, 200, list_response.text)
        self.assertEqual(len(list_response.json()), 1)

    def test_ai_ask_uses_structured_fallback(self) -> None:
        class FakeChatCompletion:
            def create(self, **kwargs):
                return type("Response", (), {"choices": [type("Choice", (), {"message": type("Message", (), {"content": "The user built a portfolio app."})()})()]})()

        class FakeClient:
            def __init__(self, *args, **kwargs):
                self.chat = type("Chat", (), {"completions": type("Completions", (), {"create": FakeChatCompletion().create})()})()

        with patch.object(ai_chat_module, "embed_text", return_value=[0.0] * 384), patch.object(ai_chat_module, "Groq", FakeClient):
            response = self.client.post(
                "/ai/ask",
                json={"question": "What did this user build?"},
            )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertIn("portfolio app", payload["answer"].lower())
        self.assertTrue(payload["sources"])

        history_response = self.client.get("/ai/history")
        self.assertEqual(history_response.status_code, 200, history_response.text)
        self.assertEqual(len(history_response.json()["items"]), 1)

    def test_resume_history_is_persisted_and_listed(self) -> None:
        class FakeResumeService:
            def select_resume_content(self, *args, **kwargs):
                return {"summary": "test"}

            def render_docx(self, *args, **kwargs):
                return b"PK\x03\x04"

        with patch.object(resume_module, "ResumeService", FakeResumeService):
            response = self.client.post(
                "/resume/generate",
                json={"job_description": "Senior backend engineer"},
            )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["status"], "completed")

        history_response = self.client.get("/resume/history")
        self.assertEqual(history_response.status_code, 200, history_response.text)
        self.assertEqual(len(history_response.json()["items"]), 1)
        self.assertEqual(history_response.json()["items"][0]["job_description"], "Senior backend engineer")


if __name__ == "__main__":
    unittest.main()
