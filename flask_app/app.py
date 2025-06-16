from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
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
                return redirect(url_for('dashboard'))
            else:
                flash('Login gagal! Username/password salah.', 'danger')
        except Exception as e:
            flash('Gagal terhubung ke Auth Service.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            resp = requests.post(f'{AUTH_SERVICE_URL}/register', json={"username": username, "password": password})
            if resp.ok:
                flash('Registrasi berhasil! Silakan login.', 'success')
                return redirect(url_for('login'))
            else:
                flash(resp.json().get('error', 'Registrasi gagal!'), 'danger')
        except Exception as e:
            flash('Gagal terhubung ke Auth Service.', 'danger')
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
            flash('Session habis, silakan login ulang.', 'warning')
            return redirect(url_for('login'))
    except Exception as e:
        flash('Gagal terhubung ke Auth Service.', 'danger')
        return redirect(url_for('login'))
    # Ambil data notes
    try:
        resp = requests.get(f'{NOTES_SERVICE_URL}/notes', headers=headers)
        if resp.status_code == 200:
            notes = resp.json()
    except Exception as e:
        flash(f'Gagal mengambil data catatan: {str(e)}', 'danger')
    # Ambil data schedule
    try:
        resp = requests.get(f'{SCHEDULE_SERVICE_URL}/schedule', headers=headers)
        if resp.status_code == 200:
            schedules = resp.json()  # Remove .get('schedules', [])
    except Exception as e:
        flash(f'Gagal mengambil jadwal: {str(e)}', 'danger')
        schedules = []
    # Ambil data notifikasi
    try:
        resp = requests.get(f'{NOTIFY_SERVICE_URL}/notify', headers=headers)
        if resp.status_code == 200:
            notifications = resp.json()  # Remove .get('notifications', [])
    except Exception as e:
        flash(f'Gagal mengambil notifikasi: {str(e)}', 'danger')
        notifications = []
    return render_template('dashboard.html', user=user, notes=notes, schedules=schedules, notifications=notifications)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Notes CRUD operations
@app.route('/add-note', methods=['POST'])
def add_note():
    if 'access_token' not in session:
        return redirect(url_for('login'))
    
    title = request.form.get('title')
    content = request.form.get('content')
    
    if not title or not content:
        flash('Judul dan isi catatan harus diisi!', 'warning')
        return redirect(url_for('dashboard'))
    
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    try:
        resp = requests.post(
            f'{NOTES_SERVICE_URL}/notes', 
            json={"title": title, "content": content},
            headers=headers
        )
        if resp.status_code == 201 or resp.status_code == 200:
            flash('Catatan berhasil ditambahkan!', 'success')
        else:
            flash(f'Gagal menambahkan catatan: {resp.text}', 'danger')
    except Exception as e:
        flash(f'Terjadi kesalahan: {str(e)}', 'danger')
    
    return redirect(url_for('dashboard'))

@app.route('/edit-note', methods=['POST'])
def edit_note():
    if 'access_token' not in session:
        return redirect(url_for('login'))
    
    note_id = request.form.get('id')
    title = request.form.get('title')
    content = request.form.get('content')
    
    if not note_id or not title or not content:
        flash('Data tidak lengkap!', 'warning')
        return redirect(url_for('dashboard'))
    
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    try:
        resp = requests.put(
            f'{NOTES_SERVICE_URL}/notes/{note_id}', 
            json={"title": title, "content": content},
            headers=headers
        )
        if resp.status_code == 200:
            flash('Catatan berhasil diperbarui!', 'success')
        else:
            flash(f'Gagal memperbarui catatan: {resp.text}', 'danger')
    except Exception as e:
        flash(f'Terjadi kesalahan: {str(e)}', 'danger')
    
    return redirect(url_for('dashboard'))

@app.route('/delete-note', methods=['POST'])
def delete_note():
    if 'access_token' not in session:
        return redirect(url_for('login'))
    
    note_id = request.form.get('id')
    
    if not note_id:
        flash('ID catatan tidak valid!', 'warning')
        return redirect(url_for('dashboard'))
    
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    try:
        resp = requests.delete(
            f'{NOTES_SERVICE_URL}/notes/{note_id}', 
            headers=headers
        )
        if resp.status_code == 200 or resp.status_code == 204:
            flash('Catatan berhasil dihapus!', 'success')
        else:
            flash(f'Gagal menghapus catatan: {resp.text}', 'danger')
    except Exception as e:
        flash(f'Terjadi kesalahan: {str(e)}', 'danger')
    
    return redirect(url_for('dashboard'))

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
        return jsonify({"success": False, "message": "Unauthorized"})
    
    data = request.get_json()
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    try:
        resp = requests.post(
            f'{SCHEDULE_SERVICE_URL}/schedule',
            json=data,
            headers=headers
        )
        if resp.status_code == 200:
            return jsonify({"success": True, "data": resp.json()})
        return jsonify({"success": False, "message": resp.text})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
    
@app.route('/edit-schedule', methods=['POST'])
def edit_schedule():
    if 'access_token' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400

        schedule_id = data.get('id')
        if not schedule_id:
            return jsonify({"success": False, "message": "Schedule ID is required"}), 400

        headers = {"Authorization": f"Bearer {session['access_token']}"}
        
        update_data = {
            "title": data.get('title'),
            "time": data.get('time'),
            "location": data.get('location'),
            "description": data.get('description')
        }

        response = requests.put(
            f"{SCHEDULE_SERVICE_URL}/schedule/{schedule_id}",
            json=update_data,
            headers=headers
        )

        if response.status_code == 200:
            return jsonify({"success": True, "data": response.json()})
        return jsonify({"success": False, "message": response.text}), response.status_code

    except Exception as e:
        print(f"Error updating schedule: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

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
            return jsonify({"success": True})
        return jsonify({"success": False, "message": "Failed to delete schedule"}), response.status_code

    except Exception as e:
        print(f"Error deleting schedule: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
