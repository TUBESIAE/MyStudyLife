from fastapi import HTTPException
import os
from typing import Dict
import time
import httpx
import jwt
from datetime import datetime

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

# Circuit breakers
auth_circuit_breaker = CircuitBreaker("auth_service")
notify_circuit_breaker = CircuitBreaker("notify_service")

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

async def send_notification(user_id: int, title: str, message: str, scheduled_time: datetime, token: str) -> bool:
    if not notify_circuit_breaker.can_execute():
        return False

    try:
        async with httpx.AsyncClient() as client:
            # Convert datetime to ISO format string for JSON serialization
            scheduled_time_str = scheduled_time.isoformat()
            response = await client.post(
                f"{SERVICE_CONFIG['notify_service']}/notify",
                json={
                    "user_id": user_id,
                    "title": title,
                    "message": message,
                    "scheduled_time": scheduled_time_str
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code in [200, 201]:
                notify_circuit_breaker.record_success()
                return True
            else:
                notify_circuit_breaker.record_failure()
                return False
    except Exception as e:
        notify_circuit_breaker.record_failure()
        return False

# Health check response
def get_health_status() -> Dict:
    return {
        "status": "healthy",
        "service": "schedule-service",
        "version": "1.0.0"
    } 