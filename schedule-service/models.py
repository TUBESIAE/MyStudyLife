# models.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from database import Base

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    time = Column(DateTime)
    location = Column(String)
    description = Column(String, nullable=True)
    user_id = Column(Integer, index=True)  # diambil dari token JWT
    is_notified = Column(Boolean, default=False)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
