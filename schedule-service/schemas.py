# schemas.py
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class ScheduleBase(BaseModel):
    title: str
    date: str
    time: str
    location: str
    description: Optional[str] = None

class ScheduleCreate(ScheduleBase):
    pass

class Schedule(ScheduleBase):
    id: int
    user_id: int
    is_notified: bool

    class Config:
        orm_mode = True
