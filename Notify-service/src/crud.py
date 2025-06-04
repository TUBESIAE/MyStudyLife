from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime, timedelta

def create_notification(db: Session, notification: schemas.NotificationCreate):
    db_notification = models.Notification(
        user_id=notification.user_id,
        title=notification.title,
        message=notification.message,
        scheduled_time=notification.scheduled_time
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification

def get_notification(db: Session, notification_id: int):
    return db.query(models.Notification).filter(models.Notification.id == notification_id).first()

def get_user_notifications(db: Session, user_id: int):
    return db.query(models.Notification).filter(models.Notification.user_id == user_id).all()

def get_upcoming_notifications(db: Session, user_id: int):
    now = datetime.utcnow()
    return db.query(models.Notification).filter(
        models.Notification.user_id == user_id,
        models.Notification.scheduled_time > now
    ).all()

def delete_notification(db: Session, notification_id: int):
    notification = db.query(models.Notification).filter(models.Notification.id == notification_id).first()
    if notification:
        db.delete(notification)
        db.commit()
    return notification

def log_notification(message: str):
    print(f"Notification: {message}")