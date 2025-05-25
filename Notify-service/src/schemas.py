from pydantic import BaseModel
from datetime import datetime

class NotificationBase(BaseModel):
    user_id: int
    message: str

class NotificationCreate(NotificationBase):
    pass

class Notification(NotificationBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True

class UpcomingSchedule(BaseModel):
    user_id: int
    title: str
    time: datetime
    location: str
    description: str | None = None

class UpcomingSchedulesResponse(BaseModel):
    schedules: list[UpcomingSchedule]