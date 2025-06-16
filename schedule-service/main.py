# main.py
from fastapi import FastAPI, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
import models, schemas, crud
from database import SessionLocal, engine
from utils import validate_token, send_notification, get_health_status
import logging
import httpx
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency: ambil session DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Health check endpoint
@app.get("/health")
async def health_check():
    return get_health_status()

async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = authorization.split(" ", 1)[1]
    return await validate_token(token)

@app.post("/schedule", response_model=schemas.Schedule)
async def create_schedule(
    schedule: schemas.ScheduleCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
    authorization: str = Header(None)
):
    try:
        user_id = user["id"]
        # Convert time string to datetime object before saving
        # Assuming schedule.time is already a datetime object due to Pydantic, but if it comes as string, convert it
        if isinstance(schedule.time, str):
            schedule.time = datetime.fromisoformat(schedule.time)
        
        new_schedule = crud.create_schedule(db, schedule, user_id)
        
        notification_data = {
            "user_id": user_id,
            "message": f"Kamu punya jadwal baru: {schedule.title} pada {schedule.time}"
        }
        
        if authorization:
            try:
                await send_notification(user_id, notification_data["message"], authorization.split(" ", 1)[1])
            except Exception as notify_e:
                logger.error(f"Gagal mengirim notifikasi untuk jadwal baru: {str(notify_e)}")
        
        return new_schedule
    except Exception as e:
        logger.error(f"Error in create_schedule: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/schedule", response_model=list[schemas.Schedule])
async def read_all(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    try:
        return crud.get_user_schedules(db, user["id"])
    except Exception as e:
        logger.error(f"Error in read_all: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/schedule/{schedule_id}", response_model=schemas.Schedule)
async def update(
    schedule_id: int,
    schedule: schemas.ScheduleCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    try:
        # Convert time string to datetime object if present in update
        if isinstance(schedule.time, str):
            schedule.time = datetime.fromisoformat(schedule.time)
            
        return crud.update_schedule(db, schedule_id, schedule, user["id"])
    except Exception as e:
        logger.error(f"Error in update: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/schedule/{schedule_id}")
async def delete(schedule_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    try:
        deleted = crud.delete_schedule(db, schedule_id, user["id"])
        if not deleted:
            raise HTTPException(status_code=404, detail="Not found")
        return {"detail": "Deleted"}
    except Exception as e:
        logger.error(f"Error in delete: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/")
async def root():
    return {"message": "Schedule Service is running"}

@app.get("/schedule/check-notifications")
async def check_schedule_notifications(
    db: Session = Depends(get_db),
    authorization: str = Header(None)
):
    try:
        schedules_to_notify = crud.get_schedules_due_for_notification(db)
        notified_schedules = []

        for schedule in schedules_to_notify:
            notification_message = f"Jadwal Anda: {schedule.title} telah dimulai pada {schedule.time.strftime('%Y-%m-%d %H:%M')}"
            user_id = schedule.user_id # Assuming user_id is directly available on the schedule object

            if authorization:
                try:
                    await send_notification(user_id, notification_message, authorization.split(" ", 1)[1])
                    crud.mark_schedule_as_notified(db, schedule.id)
                    notified_schedules.append({"id": schedule.id, "title": schedule.title, "message": notification_message})
                except Exception as notify_e:
                    logger.error(f"Gagal mengirim notifikasi untuk jadwal {schedule.id}: {str(notify_e)}")

        return {"status": "success", "notified_count": len(notified_schedules), "notified_schedules": notified_schedules}
    except Exception as e:
        logger.error(f"Error checking schedule notifications: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")