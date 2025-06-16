# crud.py
from sqlalchemy.orm import Session
from datetime import datetime, timedelta # Import datetime and timedelta
import models, schemas

def create_schedule(db: Session, schedule: schemas.ScheduleCreate, user_id: int):
    # Convert time string to datetime object before saving
    db_schedule = models.Schedule(
        title=schedule.title,
        time=schedule.time,
        location=schedule.location,
        description=schedule.description,
        user_id=user_id,
        is_notified=False # Initialize as False
    )
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

def get_user_schedules(db: Session, user_id: int):
    return db.query(models.Schedule).filter(models.Schedule.user_id == user_id).all()

def get_schedule(db: Session, schedule_id: int, user_id: int):
    return db.query(models.Schedule).filter(models.Schedule.id == schedule_id, models.Schedule.user_id == user_id).first()

def update_schedule(db: Session, schedule_id: int, schedule: schemas.ScheduleCreate, user_id: int):
    db_schedule = get_schedule(db, schedule_id, user_id)
    if db_schedule:
        for key, value in schedule.dict(exclude_unset=True).items(): # exclude_unset to avoid overwriting with None
            if key == "time":
                setattr(db_schedule, key, value)
            else:
                setattr(db_schedule, key, value)
        db.commit()
        db.refresh(db_schedule)
    return db_schedule

def delete_schedule(db: Session, schedule_id: int, user_id: int):
    db_schedule = get_schedule(db, schedule_id, user_id)
    if db_schedule:
        db.delete(db_schedule)
        db.commit()
    return db_schedule

def get_schedules_due_for_notification(db: Session):
    now = datetime.now()
    # Consider schedules that start within the next minute and haven't been notified
    notification_window_start = now
    notification_window_end = now + timedelta(minutes=1)
    
    return db.query(models.Schedule).filter(
        models.Schedule.time >= notification_window_start,
        models.Schedule.time <= notification_window_end,
        models.Schedule.is_notified == False
    ).all()

def mark_schedule_as_notified(db: Session, schedule_id: int):
    db_schedule = db.query(models.Schedule).filter(models.Schedule.id == schedule_id).first()
    if db_schedule:
        db_schedule.is_notified = True
        db.commit()
        db.refresh(db_schedule)
    return db_schedule
