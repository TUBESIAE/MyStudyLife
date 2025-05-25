# auth_utils.py
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import Dict

SECRET_KEY = "secret"  # harus sama dengan yang dipakai Auth Service
ALGORITHM = "HS256"

security = HTTPBearer()

def decode_token(token: str) -> Dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalid")

def get_current_user(token=Depends(security)):
    payload = decode_token(token.credentials)
    return payload  # berisi user_id, email, dll
