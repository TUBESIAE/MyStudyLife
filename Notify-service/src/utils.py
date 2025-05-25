# utils.py
import logging

def send_notification(user_id: int, message: str):
    # Simulate sending a notification by logging it to the terminal
    logging.info(f"Notification sent to user {user_id}: {message}")