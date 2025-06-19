import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import requests
import os
from werkzeug.security import generate_password_hash, check_password_hash
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Configure services URLs
AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://auth-service:8000')
NOTES_SERVICE_URL = os.getenv('NOTES_SERVICE_URL', 'http://notes-service:8000')
SCHEDULE_SERVICE_URL = os.getenv('SCHEDULE_SERVICE_URL', 'http://schedule-service:8000')
NOTIFY_SERVICE_URL = os.getenv('NOTIFY_SERVICE_URL', 'http://notify-service:8000')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, token=None):
        self.id = id # This will be the user's actual ID from the auth service /me endpoint
        self.username = username
        self.token = token # Store the access token here for API calls

@login_manager.user_loader
def load_user(user_id):
    # user_id here is the access_token stored by Flask-Login
    logger.info(f"load_user called with user_id (token): {user_id}")
    if not user_id: # If user_id is empty or None
        logger.warning("load_user received empty user_id.")
        return None

    try:
        # Fetch user details using the token
        response = requests.get(f"{AUTH_SERVICE_URL}/me", 
                              headers={"Authorization": f"Bearer {user_id}"})
        
        if response.status_code == 200:
            user_data = response.json()
            logger.info(f"Auth service /me response: {user_data}")
            # Update the User object with actual ID and username from /me endpoint
            return User(id=user_data.get('id'), username=user_data.get('username'), token=user_id)
        else:
            logger.error(f"Auth service /me failed: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching user details from auth service: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in load_user: {e}", exc_info=True)
        return None

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        try:
            response = requests.post(f"{AUTH_SERVICE_URL}/login", 
                                   json={"username": username, "password": password})
            if response.status_code == 200:
                user_data = response.json()
                access_token = user_data.get('access_token')
                logger.info(f"Login successful. Received access_token: {access_token[:10]}...") # Log first 10 chars

                if access_token:
                    # For Flask-Login, we use the access_token as the ID for now.
                    # The load_user function will then use this token to fetch full user details (id, username).
                    # We pass the access_token directly to the User constructor.
                    user = User(id=access_token, username="temp_user", token=access_token)
                    login_user(user)
                    return redirect(url_for('dashboard'))
                else:
                    flash('Login failed: No access token received.')
                    logger.warning("Login successful, but no access_token found in response.")
            else:
                flash('Invalid username or password')
                logger.warning(f"Login failed for user {username}: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            flash(f'Service unavailable: {e}')
            logger.error(f"Network error during login: {e}")
        except Exception as e:
            flash('An unexpected error occurred during login.')
            logger.error(f"Unexpected error in login: {e}", exc_info=True)
        
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            response = requests.post(f"{AUTH_SERVICE_URL}/register",
                                   json={"username": username, "email": email, "password": password})
            if response.status_code == 200: # Assuming 200 for successful registration
                flash('Registration successful! Please login.')
                logger.info(f"User {username} registered successfully.")
                return redirect(url_for('login'))
            elif response.status_code == 400: # Assuming 400 for username exists
                error_detail = response.json().get("detail", "Registration failed.")
                flash(error_detail)
                logger.warning(f"Registration failed for user {username}: {error_detail}")
            else:
                flash('Registration failed. Please try again.')
                logger.error(f"Registration failed for user {username}: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            flash(f'Service unavailable: {e}')
            logger.error(f"Network error during registration: {e}")
        except Exception as e:
            flash('An unexpected error occurred during registration.')
            logger.error(f"Unexpected error in register: {e}", exc_info=True)
        
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # Ensure we have a token for current_user before making API calls
    token = current_user.token
    if not token:
        flash("Authentication token not found. Please log in again.")
        return redirect(url_for('login'))

    headers = {"Authorization": f"Bearer {token}"}

    # Fetch notes
    notes = []
    try:
        response = requests.get(f"{NOTES_SERVICE_URL}/notes", headers=headers)
        if response.status_code == 200:
            notes = response.json()
        else:
            logger.error(f"Notes service failed: {response.status_code} - {response.text}")
            flash("Failed to load notes.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching notes: {e}")
        flash("Notes service unavailable.")

    # Fetch schedule
    schedule = []
    try:
        response = requests.get(f"{SCHEDULE_SERVICE_URL}/schedule",
                              headers=headers)
        if response.status_code == 200:
            schedule = response.json()
        else:
            logger.error(f"Schedule service failed: {response.status_code} - {response.text}")
            flash("Failed to load schedule.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching schedule: {e}")
        flash("Schedule service unavailable.")

    # Fetch notifications
    notifications = []
    try:
        response = requests.get(f"{NOTIFY_SERVICE_URL}/notify",
                              headers=headers)
        if response.status_code == 200:
            notifications = response.json()
        else:
            logger.error(f"Notify service failed: {response.status_code} - {response.text}")
            flash("Failed to load notifications.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching notifications: {e}")
        flash("Notify service unavailable.")

    return render_template('dashboard.html', 
                         notes=notes,
                         schedule=schedule,
                         notifications=notifications)

@app.route('/notes', methods=['POST'])
@login_required
def create_note():
    token = current_user.token
    if not token:
        return jsonify({"error": "Authentication token not found"}), 401

    try:
        data = request.json
        response = requests.post(f"{NOTES_SERVICE_URL}/notes",
                               json=data,
                               headers={"Authorization": f"Bearer {token}"})
        if response.status_code in [200, 201]:
            logger.info("Note created successfully.")
            return jsonify(response.json()), response.status_code
        else:
            logger.error(f"Failed to create note: {response.status_code} - {response.text}")
            return jsonify({"error": response.json().get("detail", "Failed to create note")}), response.status_code
    except requests.exceptions.RequestException as e:
        logger.error(f"Error creating note: {e}")
        return jsonify({"error": "Notes service unavailable"}), 503
    except Exception as e:
        logger.error(f"Unexpected error in create_note: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/events', methods=['POST'])
@login_required
def create_event():
    token = current_user.token
    if not token:
        return jsonify({"error": "Authentication token not found"}), 401

    try:
        data = request.json
        response = requests.post(f"{SCHEDULE_SERVICE_URL}/schedule",
                               json=data,
                               headers={"Authorization": f"Bearer {token}"})
        if response.status_code in [200, 201]:
            logger.info("Event created successfully.")
            return jsonify(response.json()), response.status_code
        else:
            logger.error(f"Failed to create event: {response.status_code} - {response.text}")
            return jsonify({"error": response.json().get("detail", "Failed to create event")}), response.status_code
    except requests.exceptions.RequestException as e:
        logger.error(f"Error creating event: {e}")
        return jsonify({"error": "Schedule service unavailable"}), 503
    except Exception as e:
        logger.error(f"Unexpected error in create_event: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/notes/<int:note_id>', methods=['PUT', 'DELETE'])
@login_required
def manage_note(note_id):
    token = current_user.token
    if not token:
        return jsonify({"error": "Authentication token not found"}), 401

    try:
        if request.method == 'PUT':
            data = request.json
            response = requests.put(f"{NOTES_SERVICE_URL}/notes/{note_id}",
                                json=data,
                                headers={"Authorization": f"Bearer {token}"})
        elif request.method == 'DELETE':
            response = requests.delete(f"{NOTES_SERVICE_URL}/notes/{note_id}",
                                    headers={"Authorization": f"Bearer {token}"})
            
        if response.status_code in [200, 204]:
            logger.info(f"Note {request.method} successful.")
            if request.method == 'DELETE':
                return jsonify({"message": "Note deleted successfully"}), 200
            return jsonify(response.json()), response.status_code
        else:
            logger.error(f"Failed to {request.method} note: {response.status_code} - {response.text}")
            return jsonify({"error": response.json().get("detail", f"Failed to {request.method} note")}), response.status_code
    except requests.exceptions.RequestException as e:
        logger.error(f"Error in {request.method} note: {e}")
        return jsonify({"error": "Notes service unavailable"}), 503
    except Exception as e:
        logger.error(f"Unexpected error in manage_note: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/events/<int:event_id>', methods=['PUT', 'DELETE'])
@login_required
def manage_event(event_id):
    token = current_user.token
    if not token:
        return jsonify({"error": "Authentication token not found"}), 401

    try:
        if request.method == 'PUT':
            data = request.json
            response = requests.put(f"{SCHEDULE_SERVICE_URL}/schedule/{event_id}",
                                json=data,
                                headers={"Authorization": f"Bearer {token}"})
        elif request.method == 'DELETE':
            response = requests.delete(f"{SCHEDULE_SERVICE_URL}/schedule/{event_id}",
                                    headers={"Authorization": f"Bearer {token}"})
            
        if response.status_code in [200, 204]:
            logger.info(f"Event {request.method} successful.")
            if request.method == 'DELETE':
                return jsonify({"message": "Event deleted successfully"}), 200
            return jsonify(response.json()), response.status_code
        else:
            logger.error(f"Failed to {request.method} event: {response.status_code} - {response.text}")
            return jsonify({"error": response.json().get("detail", f"Failed to {request.method} event")}), response.status_code
    except requests.exceptions.RequestException as e:
        logger.error(f"Error in {request.method} event: {e}")
        return jsonify({"error": "Schedule service unavailable"}), 503
    except Exception as e:
        logger.error(f"Unexpected error in manage_event: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/notifications/<int:notification_id>', methods=['DELETE'])
@login_required
def delete_notification(notification_id):
    token = current_user.token
    if not token:
        return jsonify({"error": "Authentication token not found"}), 401

    try:
        response = requests.delete(f"{NOTIFY_SERVICE_URL}/notify/{notification_id}",
                                headers={"Authorization": f"Bearer {token}"})
            
        if response.status_code in [200, 204]:
            logger.info("Notification deleted successfully.")
            return jsonify({"message": "Notification deleted successfully"}), 200
        else:
            logger.error(f"Failed to delete notification: {response.status_code} - {response.text}")
            return jsonify({"error": response.json().get("detail", "Failed to delete notification")}), response.status_code
    except requests.exceptions.RequestException as e:
        logger.error(f"Error deleting notification: {e}")
        return jsonify({"error": "Notification service unavailable"}), 503
    except Exception as e:
        logger.error(f"Unexpected error in delete_notification: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)