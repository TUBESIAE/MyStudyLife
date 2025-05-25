# schemas.py
from pydantic import BaseModel

class ScheduleBase(BaseModel):
    title: str
    time: str
    location: str
    description: str | None = None

class ScheduleCreate(ScheduleBase):
    pass

class Schedule(ScheduleBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True
