from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from models import users_db, User
from schemas import UserRegister, UserLogin, TokenResponse
from auth import hash_password, verify_password, create_access_token
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Untuk testing dari browser/postman (bisa disesuaikan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(user: UserRegister):
    # Cek apakah username sudah ada
    for u in users_db:
        if u.username == user.username:
            raise HTTPException(status_code=400, detail="Username sudah dipakai")
    hashed = hash_password(user.password)
    new_user = User(username=user.username, hashed_password=hashed)
    users_db.append(new_user)
    return {"msg": "User berhasil didaftarkan"}

@app.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Cari user
    user = None
    for u in users_db:
        if u.username == form_data.username:
            user = u
            break
    if not user:
        raise HTTPException(status_code=400, detail="Username atau password salah")

    # Cek password
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Username atau password salah")

    # Buat token
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}
