from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
import jwt
from . import models, schemas, crud
from .database import SessionLocal, engine
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub") or payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/notify", response_model=schemas.Notification)
def send_notification(
    notification: schemas.NotificationCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    # Pastikan user_id dari token sama dengan notification.user_id
    if notification.user_id != int(user_id):
        raise HTTPException(status_code=403, detail="User ID mismatch")
    return crud.create_notification(db, notification)

@app.get("/notify", response_model=list[schemas.Notification])
def get_all_notifications(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    return crud.get_user_notifications(db, user_id)

@app.get("/notify/upcoming", response_model=list[schemas.Notification])
def get_upcoming_notifications(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    return crud.get_upcoming_notifications(db, user_id)

@app.delete("/notify/{notification_id}")
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    notification = crud.get_notification(db, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notification.user_id != int(user_id):
        raise HTTPException(status_code=403, detail="Not authorized to delete this notification")
    crud.delete_notification(db, notification_id)
    return {"detail": "Notification deleted"}

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "notify-service",
        "version": "1.0.0"
    }

@app.on_event("startup")
def startup_event():
    models.Base.metadata.create_all(bind=engine)
    logging.info("Notification Service started.")

@app.get("/")
def read_root():
    return {"message": "Notification Service is running."}