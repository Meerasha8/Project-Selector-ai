from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Table
from database import Base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from pydantic import BaseModel

auth_users = Table(
    "users",
    Base.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    schema="auth",
)


class User(BaseModel):
    user_uuid: str
    email: str | None = None


class UserDetails(Base):
    
    __tablename__ = "user_details"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    mobile_number = Column(String(20), index=True)
    email_id = Column(String(40), index=True)
    github_url = Column(String(40), index=True)
    linkedin_url = Column(String(40), index=True)
    portfolio_link = Column(String(40), index=True)
    location = Column(String(40), index=True)
    profession_summary = Column(String(255), index=True)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)



class Educations(Base):
    
    __tablename__ = "education"
    id = Column(Integer, primary_key=True, index=True)
    course_name = Column(String(50),index=True)
    cgpa = Column(Float,index=True)
    start_year = Column(Integer,index=True)
    end_year = Column(Integer,index=True)
    college_name = Column(String(50), index=True)
    location = Column(String(50),index=True)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)


    
class Certificates(Base):
    
    __tablename__= "certificates"
    id = Column(Integer, primary_key=True, index=True)
    certificate_issuer = Column(String(255),index=True)
    certificate_name = Column(String(50), index=True)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)

    
class Internship(Base):
    
    __tablename__="internship"
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(50), index=True)
    role = Column(String(20), index=True)
    description = Column(String(255),index=True)
    Duration = Column(String(20),index=True)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)

    
class Achievements(Base):
    
    __tablename__="achievements"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String(255),index=True)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    

class Projects(Base):
    
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    description = Column(String(255), index=True)
    tech_stack = Column(String(50),index=True)
    github_url = Column(String(255), index=True)
    live_link = Column(String(255), index=True)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    
class Skills(Base):

    __tablename__ = "skills"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    description = Column(String(255), index=True)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    



class DocumentEmbedding(Base):
    __tablename__ = "document_embeddings"
    id = Column(Integer, primary_key=True)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    source_table = Column(String, nullable=False)
    source_id = Column(Integer, nullable=False)
    content = Column(String, nullable=False)
    embedding = Column(Vector(384))