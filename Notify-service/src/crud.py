from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime, timedelta

def create_notification(db: Session, notification: schemas.NotificationCreate):
    db_notification = models.Notification(**notification.dict())
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification

def get_upcoming_notifications(db: Session, user_id: int):
    upcoming_time = datetime.utcnow() + timedelta(minutes=15)
    return db.query(models.Notification).filter(models.Notification.user_id == user_id, models.Notification.timestamp <= upcoming_time).all()

def log_notification(message: str):
    print(f"Notification: {message}")