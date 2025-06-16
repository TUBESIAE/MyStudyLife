from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import requests
import os
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv('SECRET_KEY', 'supersecretkey')

# Endpoint service-service
AUTH_SERVICE_URL = 'http://localhost:8001'
NOTES_SERVICE_URL = 'http://localhost:8002'
SCHEDULE_SERVICE_URL = 'http://localhost:8003'
NOTIFY_SERVICE_URL = 'http://localhost:8004'

@app.route('/')
def home():
    if 'access_token' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            resp = requests.post(f'{AUTH_SERVICE_URL}/login', json={"username": username, "password": password})
            if resp.status_code == 200:
                session['access_token'] = resp.json()['access_token']
                return jsonify({"success": True, "access_token": resp.json()['access_token']})
            else:
                return jsonify({"success": False, "message": 'Login gagal! Username/password salah.'})
        except Exception as e:
            return jsonify({"success": False, "message": 'Gagal terhubung ke Auth Service.'})
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            resp = requests.post(f'{AUTH_SERVICE_URL}/register', json={"username": username, "password": password})
            if resp.ok:
                return jsonify({"success": True, "message": 'Registrasi berhasil! Silakan login.'})
            else:
                return jsonify({"success": False, "message": resp.json().get('error', 'Registrasi gagal!')})
        except Exception as e:
            return jsonify({"success": False, "message": 'Gagal terhubung ke Auth Service.'})
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'access_token' not in session:
        return redirect(url_for('login'))
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    user = None
    notes = []
    schedules = []
    notifications = []
    # Ambil info user
    try:
        resp = requests.get(f'{AUTH_SERVICE_URL}/me', headers=headers)
        if resp.status_code == 200:
            user = resp.json()
        else:
            # If fetching user fails, clear session and redirect to login
            session.clear()
            return redirect(url_for('login'))
    except Exception as e:
        # If Auth Service is unreachable, clear session and redirect to login
        session.clear()
        return redirect(url_for('login'))

    # Ambil data notes
    try:
        resp = requests.get(f'{NOTES_SERVICE_URL}/notes', headers=headers)
        if resp.status_code == 200:
            notes = resp.json()
        else:
            notes = [] # Ensure notes is empty if API call fails
            print(f"Error fetching notes: Status code {resp.status_code} - {resp.text}")
    except Exception as e:
        notes = [] # Ensure notes is empty if API call fails
        print(f"Error fetching notes: {str(e)}")
    
    # Ambil data schedule
    try:
        resp = requests.get(f'{SCHEDULE_SERVICE_URL}/schedule', headers=headers)
        if resp.status_code == 200:
            schedules = resp.json()
        else:
            schedules = [] # Ensure schedules is empty if API call fails
            print(f"Error fetching schedules: Status code {resp.status_code} - {resp.text}")
    except Exception as e:
        schedules = [] # Ensure schedules is empty if API call fails
        print(f"Error fetching schedules: {str(e)}")

    # Ambil data notifikasi
    try:
        resp = requests.get(f'{NOTIFY_SERVICE_URL}/notify', headers=headers)
        if resp.status_code == 200:
            notifications = resp.json()
        else:
            notifications = [] # Ensure notifications is empty if API call fails
            print(f"Error fetching notifications: Status code {resp.status_code} - {resp.text}")
    except Exception as e:
        notifications = [] # Ensure notifications is empty if API call fails
        print(f"Error fetching notifications: {str(e)}")
        
    return render_template('dashboard.html', user=user, notes=notes, schedules=schedules, notifications=notifications)

@app.route('/get-notes-json')
def get_notes_json():
    if 'access_token' not in session:
        return jsonify([]), 401
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    try:
        resp = requests.get(f'{NOTES_SERVICE_URL}/notes', headers=headers)
        if resp.status_code == 200:
            return jsonify(resp.json())
        return jsonify([]), resp.status_code
    except Exception as e:
        print(f"Error fetching notes JSON: {str(e)}")
        return jsonify([]), 500

@app.route('/get-schedules-json')
def get_schedules_json():
    if 'access_token' not in session:
        return jsonify([]), 401
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    try:
        resp = requests.get(f'{SCHEDULE_SERVICE_URL}/schedule', headers=headers)
        if resp.status_code == 200:
            return jsonify(resp.json())
        return jsonify([]), resp.status_code
    except Exception as e:
        print(f"Error fetching schedules JSON: {str(e)}")
        return jsonify([]), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Notes CRUD operations
@app.route('/add-note', methods=['POST'])
def add_note():
    if 'access_token' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    title = request.form.get('title')
    content = request.form.get('content')
    
    if not title or not content:
        return jsonify({"success": False, "message": "Judul dan isi catatan harus diisi!"}), 400
    
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    try:
        resp = requests.post(
            f'{NOTES_SERVICE_URL}/notes', 
            json={"title": title, "content": content},
            headers=headers
        )
        if resp.status_code == 201 or resp.status_code == 200:
            return jsonify({"success": True, "message": "Catatan berhasil ditambahkan!"})
        else:
            return jsonify({"success": False, "message": f"Gagal menambahkan catatan: {resp.text}"}), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "message": f"Terjadi kesalahan: {str(e)}"}), 500

@app.route('/edit-note', methods=['POST'])
def edit_note():
    if 'access_token' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    note_id = request.form.get('id')
    title = request.form.get('title')
    content = request.form.get('content')
    
    if not note_id or not title or not content:
        return jsonify({"success": False, "message": "Data tidak lengkap!"}), 400
    
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    try:
        resp = requests.put(
            f'{NOTES_SERVICE_URL}/notes/{note_id}', 
            json={"title": title, "content": content},
            headers=headers
        )
        if resp.status_code == 200:
            return jsonify({"success": True, "message": "Catatan berhasil diperbarui!"})
        else:
            return jsonify({"success": False, "message": f"Gagal memperbarui catatan: {resp.text}"}), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "message": f"Terjadi kesalahan: {str(e)}"}), 500

@app.route('/delete-note', methods=['POST'])
def delete_note():
    if 'access_token' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    note_id = request.form.get('id')
    
    if not note_id:
        return jsonify({"success": False, "message": "ID catatan tidak valid!"}), 400
    
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    try:
        resp = requests.delete(
            f'{NOTES_SERVICE_URL}/notes/{note_id}', 
            headers=headers
        )
        if resp.status_code == 200 or resp.status_code == 204:
            return jsonify({"success": True, "message": "Catatan berhasil dihapus!"})
        else:
            return jsonify({"success": False, "message": f"Gagal menghapus catatan: {resp.text}"}), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "message": f"Terjadi kesalahan: {str(e)}"}), 500

@app.route('/notifications')
def get_notifications():
    if 'access_token' not in session:
        return jsonify([])
    
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    try:
        resp = requests.get(f'{NOTIFY_SERVICE_URL}/notify', headers=headers)
        if resp.status_code == 200:
            return jsonify(resp.json())
        return jsonify([])
    except Exception as e:
        print(f"Error fetching notifications: {str(e)}")
        return jsonify([])

@app.route('/add-schedule', methods=['POST'])
def add_schedule():
    if 'access_token' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    title = request.form.get('title')
    time = request.form.get('time')
    location = request.form.get('location')
    description = request.form.get('description')

    # Basic validation
    if not title or not time:
        return jsonify({"success": False, "message": "Judul dan waktu jadwal harus diisi!"}), 400

    schedule_data = {
        "title": title,
        "time": time,
        "location": location,
        "description": description
    }
    
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    try:
        resp = requests.post(
            f'{SCHEDULE_SERVICE_URL}/schedule',
            json=schedule_data, # Send as JSON to the microservice
            headers=headers
        )
        if resp.status_code == 200 or resp.status_code == 201:
            return jsonify({"success": True, "message": "Jadwal berhasil ditambahkan!"})
        else:
            return jsonify({"success": False, "message": f"Gagal menambahkan jadwal: {resp.text}"}), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "message": f"Terjadi kesalahan saat menambahkan jadwal: {str(e)}"}), 500

@app.route('/edit-schedule', methods=['POST'])
def edit_schedule():
    if 'access_token' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    schedule_id = request.form.get('id')
    title = request.form.get('title')
    time = request.form.get('time')
    location = request.form.get('location')
    description = request.form.get('description')

    if not schedule_id or not title or not time:
        return jsonify({"success": False, "message": "ID jadwal, judul, dan waktu harus diisi!"}), 400

    update_data = {
        "title": title,
        "time": time,
        "location": location,
        "description": description
    }

    headers = {"Authorization": f"Bearer {session['access_token']}"}
    try:
        resp = requests.put(
            f"{SCHEDULE_SERVICE_URL}/schedule/{schedule_id}",
            json=update_data,
            headers=headers
        )

        if resp.status_code == 200:
            return jsonify({"success": True, "message": "Jadwal berhasil diperbarui!"})
        else:
            return jsonify({"success": False, "message": f"Gagal memperbarui jadwal: {resp.text}"}), resp.status_code

    except Exception as e:
        return jsonify({"success": False, "message": f"Terjadi kesalahan saat memperbarui jadwal: {str(e)}"}), 500

@app.route('/delete-schedule', methods=['POST'])
def delete_schedule():
    if 'access_token' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    try:
        data = request.get_json()
        if not data or 'id' not in data:
            return jsonify({"success": False, "message": "Schedule ID is required"}), 400

        schedule_id = data['id']
        headers = {"Authorization": f"Bearer {session['access_token']}"}
        
        response = requests.delete(
            f"{SCHEDULE_SERVICE_URL}/schedule/{schedule_id}",
            headers=headers
        )

        if response.status_code == 200:
            return jsonify({"success": True, "message": "Jadwal berhasil dihapus!"})
        return jsonify({"success": False, "message": "Failed to delete schedule"}), response.status_code

    except Exception as e:
        print(f"Error deleting schedule: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
