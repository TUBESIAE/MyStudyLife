# main.py
from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
import models, schemas, crud
from database import SessionLocal, engine
from utils import validate_token, send_notification, get_health_status
import logging

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
    user=Depends(get_current_user),
    request: Request = None
):
    try:
        # Buat jadwal di database
        new_schedule = crud.create_schedule(db, schedule, user["id"])
        
        # Kirim notifikasi ke notify-service
        notification_data = {
            "user_id": user["id"],
            "message": f"Kamu punya jadwal baru: {schedule.title} pada {schedule.time}"
        }
        
        if authorization:
            await send_notification(user["id"], notification_data["message"], authorization.split(" ", 1)[1])
        
        return new_schedule
    db_user = db.query(models.User).filter(models.User.username == user["sub"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    new_schedule = crud.create_schedule(db, schedule, db_user.id)

    # Kirim notifikasi ke notify-service (opsional)
    notification_data = {
        "user_id": db_user.id,
        "message": f"Kamu punya jadwal baru: {schedule.title} pada {schedule.time}"
    }
    try:
        notify_url = "http://localhost:8003/notify"
        headers = {}
        if request and "authorization" in request.headers:
            headers["Authorization"] = request.headers["authorization"]
        with httpx.Client() as client:
            client.post(notify_url, json=notification_data, headers=headers)
    except Exception as e:
        logger.error(f"Error in create_schedule: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
        print("Gagal mengirim notifikasi:", e)

    return new_schedule

@app.get("/schedule", response_model=list[schemas.Schedule])
async def read_all(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    try:
        return crud.get_user_schedules(db, user["id"])
    except Exception as e:
        logger.error(f"Error in read_all: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
def read_all_schedules(db: Session = Depends(get_db), user=Depends(get_current_user)):
    db_user = db.query(models.User).filter(models.User.username == user["sub"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.get_user_schedules(db, db_user.id)

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
def update_schedule(
    schedule_id: int,
    schedule: schemas.ScheduleCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = db.query(models.User).filter(models.User.username == user["sub"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    updated = crud.update_schedule(db, schedule_id, schedule, db_user.id)
    if not updated:
        raise HTTPException(status_code=404, detail="Schedule not found or not yours")
    return updated

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
def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = db.query(models.User).filter(models.User.username == user["sub"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    deleted = crud.delete_schedule(db, schedule_id, db_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Schedule not found or not yours")
    return {"detail": "Deleted"}

@app.post("/register")
def register(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    if form_data.username in fake_users_db:
        raise HTTPException(status_code=400, detail="Username already registered")
    # Simpan ke fake_users_db (opsional, untuk login lama)
    hashed_password = get_password_hash(form_data.password)
    fake_users_db[form_data.username] = {"username": form_data.username, "hashed_password": hashed_password}
    # Simpan ke database
    db_user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered (db)")
    new_user = models.User(username=form_data.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"msg": "User registered"}

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": db_user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/")
async def root():
    return {"message": "Schedule Service is running"}

@app.get("/users/me")
def read_me(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = fake_users_db.get(username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user