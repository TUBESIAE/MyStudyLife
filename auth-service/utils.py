# utils.py
from passlib.context import CryptContext
from fastapi import HTTPException
import os
from typing import Dict
import time

# Konfigurasi hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Service configuration
SERVICE_CONFIG = {
    "auth_service": os.getenv("AUTH_SERVICE_URL", "http://localhost:8001"),
    "notes_service": os.getenv("NOTES_SERVICE_URL", "http://localhost:8002"),
    "schedule_service": os.getenv("SCHEDULE_SERVICE_URL", "http://localhost:8003"),
    "notify_service": os.getenv("NOTIFY_SERVICE_URL", "http://localhost:8004")
}

# Circuit breaker configuration
CIRCUIT_BREAKER_CONFIG = {
    "failure_threshold": 5,
    "recovery_timeout": 30,
    "half_open_timeout": 10
}

class CircuitBreaker:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.failures = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN

    def record_failure(self):
        self.failures += 1
        if self.failures >= CIRCUIT_BREAKER_CONFIG["failure_threshold"]:
            self.state = "OPEN"
            self.last_failure_time = time.time()

    def record_success(self):
        self.failures = 0
        self.state = "CLOSED"

    def can_execute(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > CIRCUIT_BREAKER_CONFIG["recovery_timeout"]:
                self.state = "HALF-OPEN"
                return True
            return False
        return True

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Health check response
def get_health_status() -> Dict:
    return {
        "status": "healthy",
        "service": "auth-service",
        "version": "1.0.0"
    }