# auth.py
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException
from models import User, UserIn, fake_users_db
from utils import hash_password, verify_password

# Secret key untuk JWT (ganti dengan key yang lebih aman di production)
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Fungsi untuk membuat JWT token
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Fungsi untuk register user
def register_user(user: UserIn):
    # Cek apakah username sudah ada
    if any(u.username == user.username for u in fake_users_db):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Hash password dan simpan user
    hashed_password = hash_password(user.password)
    new_user = User(id=len(fake_users_db) + 1, username=user.username, hashed_password=hashed_password)
    fake_users_db.append(new_user)
    return {"message": "User registered successfully"}

# Fungsi untuk login
def login_user(user: UserIn):
    # Cari user di "database"
    for db_user in fake_users_db:
        if db_user.username == user.username and verify_password(user.password, db_user.hashed_password):
            # Buat token JWT
            access_token = create_access_token(data={"sub": str(db_user.id)})
            return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid username or password")

# Fungsi untuk mendapatkan user dari token
def get_current_user(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub") # Mengambil ID sebagai string
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        # Mengubah user_id menjadi integer untuk mencari user
        user_id_int = int(user_id)
        for user in fake_users_db:
            if user.id == user_id_int:
                return user
        raise HTTPException(status_code=404, detail="User not found")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")