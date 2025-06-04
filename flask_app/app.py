from flask import Flask, render_template, request, redirect, url_for, session, flash
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
        resp = requests.get(f'{SCHEDULE_SERVICE_URL}/schedules', headers=headers)
        if resp.status_code == 200:
            schedules = resp.json().get('schedules', [])
    except Exception:
        pass
    # Ambil data notifikasi
    try:
        resp = requests.get(f'{NOTIFY_SERVICE_URL}/notifications', headers=headers)
        if resp.status_code == 200:
            notifications = resp.json().get('notifications', [])
    except Exception:
        pass
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
