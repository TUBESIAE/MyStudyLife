from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas, crud
from database import SessionLocal, engine
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/notify", response_model=schemas.Notification)
def send_notification(notification: schemas.NotificationCreate, db: Session = Depends(get_db)):
    return crud.create_notification(db, notification)

@app.get("/notify/upcoming", response_model=list[schemas.Notification])
def get_upcoming_notifications(db: Session = Depends(get_db)):
    return crud.get_upcoming_notifications(db)

@app.on_event("startup")
def startup_event():
    models.Base.metadata.create_all(bind=engine)
    logging.info("Notification Service started.")

@app.get("/")
def read_root():
    return {"message": "Notification Service is running."}