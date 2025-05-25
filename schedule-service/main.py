# main.py
from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import models, schemas, crud
from database import SessionLocal, engine
from auth_utils import get_current_user
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import httpx
from typing import Optional

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

fake_users_db = {}

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(username: str, password: str):
    user = fake_users_db.get(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency: ambil session DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/schedule", response_model=schemas.Schedule)
def create_schedule(
    schedule: schemas.ScheduleCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user),
    request: Request = None
):
    # Buat jadwal di database
    new_schedule = crud.create_schedule(db, schedule, user_id)
    
    # Kirim notifikasi ke notify-service
    notification_data = {
        "user_id": user_id,
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
        print("Gagal mengirim notifikasi:", e)
    
    return new_schedule

@app.get("/schedule", response_model=list[schemas.Schedule])
def read_all(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return crud.get_user_schedules(db, user["user_id"])

@app.put("/schedule/{schedule_id}", response_model=schemas.Schedule)
def update(schedule_id: int, schedule: schemas.ScheduleCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return crud.update_schedule(db, schedule_id, schedule, user["user_id"])

@app.delete("/schedule/{schedule_id}")
def delete(schedule_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    deleted = crud.delete_schedule(db, schedule_id, user["user_id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Not found")
    return {"detail": "Deleted"}

@app.post("/register")
def register(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username in fake_users_db:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(form_data.password)
    fake_users_db[form_data.username] = {"username": form_data.username, "hashed_password": hashed_password}
    return {"msg": "User registered"}

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/")
def read_root():
    return {"message": "API is running. See /docs for documentation."}
