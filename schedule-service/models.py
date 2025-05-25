# models.py
from sqlalchemy import Column, Integer, String, ForeignKey
from database import Base

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    time = Column(String)
    location = Column(String)
    description = Column(String, nullable=True)
    user_id = Column(Integer, index=True)  # diambil dari token JWT
