# main.py
from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
import models, schemas, crud
from database import SessionLocal, engine
from utils import validate_token, send_notification, get_health_status
import logging
from datetime import datetime

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
        # Buat jadwal di database
        new_schedule = crud.create_schedule(db, schedule, user["id"])
        
        # Convert schedule.date and schedule.time to datetime object for notification
        # Assuming schedule.date is 'YYYY-MM-DD' and schedule.time is 'HH:MM'
        event_datetime_str = f"{schedule.date}T{schedule.time}:00" # Adding seconds to match ISO format
        event_datetime = datetime.fromisoformat(event_datetime_str)

        notification_message = f"Kamu punya jadwal baru: {schedule.title} pada {schedule.date} {schedule.time}"
        
        if authorization:
            try:
                await send_notification(user["id"], schedule.title, notification_message, event_datetime, authorization.split(" ", 1)[1])
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
