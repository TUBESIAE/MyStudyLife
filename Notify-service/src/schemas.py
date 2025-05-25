from pydantic import BaseModel
from datetime import datetime
from typing import Optional  # Add this import

class NotificationBase(BaseModel):
    user_id: int
    message: str

class NotificationCreate(NotificationBase):
    pass

class Notification(NotificationBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class UpcomingSchedule(BaseModel):
    user_id: int
    title: str
    time: datetime
    location: str
    description: Optional[str] = None  # Change here

class UpcomingSchedulesResponse(BaseModel):
    schedules: list[UpcomingSchedule]