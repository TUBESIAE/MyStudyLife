# models.py
from pydantic import BaseModel

# Model untuk input register/login
class UserIn(BaseModel):
    username: str
    password: str

# Model untuk menyimpan user di "database"
class User(BaseModel):
    id: int
    username: str
    hashed_password: str

# Simulasi database (list sementara)
fake_users_db = []