# main.py
from fastapi import FastAPI, Depends, HTTPException, Header
from models import UserIn
from auth import register_user, login_user, get_current_user
from utils import get_health_status
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Health check endpoint
@app.get("/health")
async def health_check():
    return get_health_status()

# Endpoint untuk register
@app.post("/register")
async def register(user: UserIn):
    try:
        return register_user(user)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in register: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

# Endpoint untuk login
@app.post("/login")
async def login(user: UserIn):
    try:
        return login_user(user)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in login: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

# Endpoint untuk cek info user dari token
@app.get("/me")
async def read_users_me(authorization: str = Header(default=None)):
    try:
        if authorization is None or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Bearer token required")
        token = authorization.split(" ")[1]  # Ambil token setelah "Bearer "
        user = get_current_user(token)
        return {"username": user.username, "id": user.id}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in read_users_me: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

# Endpoint root
@app.get("/")
async def root():
    return {"message": "Auth Service is running"}