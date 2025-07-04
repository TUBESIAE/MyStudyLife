from fastapi import HTTPException
import os
from typing import Dict
import time
import httpx
import jwt

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

# Auth service circuit breaker
auth_circuit_breaker = CircuitBreaker("auth_service")

async def validate_token(token: str) -> Dict:
    if not auth_circuit_breaker.can_execute():
        raise HTTPException(status_code=503, detail="Auth service is currently unavailable")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SERVICE_CONFIG['auth_service']}/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                auth_circuit_breaker.record_success()
                return response.json()
            else:
                auth_circuit_breaker.record_failure()
                raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        auth_circuit_breaker.record_failure()
        raise HTTPException(status_code=503, detail="Auth service error")

# Health check response
def get_health_status() -> Dict:
    return {
        "status": "healthy",
        "service": "notes-service",
        "version": "1.0.0"
    } 