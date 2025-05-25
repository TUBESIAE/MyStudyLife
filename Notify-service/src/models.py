# models.py
from sqlalchemy import Column, Integer, String, DateTime
from database import Base
from datetime import datetime

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    message = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)