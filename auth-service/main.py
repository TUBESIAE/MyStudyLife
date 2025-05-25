# main.py
from fastapi import FastAPI, Depends, HTTPException, Header
from models import UserIn
from auth import register_user, login_user, get_current_user

app = FastAPI()

# Endpoint untuk register
@app.post("/register")
async def register(user: UserIn):
    return register_user(user)

# Endpoint untuk login
@app.post("/login")
async def login(user: UserIn):
    return login_user(user)

# Endpoint untuk cek info user dari token
@app.get("/me")
async def read_users_me(authorization: str = Header(default=None)):
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    token = authorization.split(" ")[1]  # Ambil token setelah "Bearer "
    user = get_current_user(token)
    return {"username": user.username, "id": user.id}

# Endpoint root (yang sudah ada)
@app.get("/")
async def root():
    return {"message": "Hello World"}