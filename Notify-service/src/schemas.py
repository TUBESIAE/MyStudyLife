from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class NotificationBase(BaseModel):
    title: str
    message: str
    scheduled_time: datetime

class NotificationCreate(NotificationBase):
    user_id: int

class Notification(NotificationBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True

class UpcomingSchedule(BaseModel):
    user_id: int
    title: str
    time: datetime
    location: str
    description: Optional[str] = None  # Change here

class UpcomingSchedulesResponse(BaseModel):
    schedules: list[UpcomingSchedule]