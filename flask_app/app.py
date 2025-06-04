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
            notes = resp.json().get('notes', [])
    except Exception:
        pass
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
