from sqlalchemy import Column, Integer, String,Float, DateTime, ForeignKey
from database import Base
from sqlalchemy.sql import func
import uuid 


class User(Base):
    
    __tablename__ = "users"
    user_uuid = Column(String(36),primary_key=True,default=lambda: str(uuid.uuid4()))
    username = Column(String(50),nullable=False,unique=True,index=True)
    email = Column(String(255),nullable=False,unique=True,index=True)
    password = Column(String(255),nullable=False)
    created_at = Column(DateTime(timezone=True),server_default=func.now())
    
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
    user_uuid = Column(String(36),ForeignKey("users.user_uuid"),nullable=False)



class Educations(Base):
    
    __tablename__ = "education"
    id = Column(Integer, primary_key=True, index=True)
    course_name = Column(String(50),index=True)
    cgpa = Column(Float,index=True)
    start_year = Column(Integer,index=True)
    end_year = Column(Integer,index=True)
    college_name = Column(String(50), index=True)
    location = Column(String(50),index=True)
    user_uuid = Column(String(36),ForeignKey("users.user_uuid"),nullable=False)


    
class Certificates(Base):
    
    __tablename__= "certificates"
    id = Column(Integer, primary_key=True, index=True)
    certificate_issuer = Column(String(255),index=True)
    certificate_name = Column(String(50), index=True)
    user_uuid = Column(String(36),ForeignKey("users.user_uuid"),nullable=False)


    
class Internship(Base):
    
    __tablename__="internship"
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(50), index=True)
    role = Column(String(20), index=True)
    description = Column(String(255),index=True)
    Duration = Column(String(20),index=True)
    user_uuid = Column(String(36),ForeignKey("users.user_uuid"),nullable=False)


    
class Achievements(Base):
    
    __tablename__="achievements"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String(255),index=True)
    user_uuid = Column(String(36),ForeignKey("users.user_uuid"),nullable=False)


    

class Projects(Base):
    
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    description = Column(String(255), index=True)
    tech_stack = Column(String(50),index=True)
    github_url = Column(String(255), index=True)
    live_link = Column(String(255), index=True)
    user_uuid = Column(String(36),ForeignKey("users.user_uuid"),nullable=False)


    
class Skills(Base):

    __tablename__ = "skills"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    description = Column(String(255), index=True)
    user_uuid = Column(String(36),ForeignKey("users.user_uuid"),nullable=False)

