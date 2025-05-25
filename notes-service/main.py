from fastapi import FastAPI, Depends, HTTPException, status
from typing import List, Optional
import sqlite3
import jwt
from datetime import datetime, timedelta
from models import NoteCreate, NoteOut

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

app = FastAPI()

def get_db():
    conn = sqlite3.connect("notes.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        content TEXT,
        created_at TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

# Auth helper

def get_current_user(token: str = Depends(lambda: None)):
    from fastapi import Header
    def _get_token(authorization: Optional[str] = Header(None)):
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid token")
        return authorization.split(" ", 1)[1]
    token = _get_token()
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/notes", response_model=NoteOut)
def create_note(note: NoteCreate, user_id: int = Depends(get_current_user)):
    conn = get_db()
    c = conn.cursor()
    now = datetime.utcnow().isoformat()
    c.execute("INSERT INTO notes (user_id, title, content, created_at) VALUES (?, ?, ?, ?)", (user_id, note.title, note.content, now))
    note_id = c.lastrowid
    conn.commit()
    c.execute("SELECT * FROM notes WHERE id=?", (note_id,))
    row = c.fetchone()
    conn.close()
    return NoteOut(id=row["id"], title=row["title"], content=row["content"], created_at=row["created_at"])

@app.get("/notes", response_model=List[NoteOut])
def get_notes(user_id: int = Depends(get_current_user)):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM notes WHERE user_id=? ORDER BY created_at DESC", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [NoteOut(id=row["id"], title=row["title"], content=row["content"], created_at=row["created_at"]) for row in rows]

@app.put("/notes/{note_id}", response_model=NoteOut)
def update_note(note_id: int, note: NoteCreate, user_id: int = Depends(get_current_user)):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM notes WHERE id=? AND user_id=?", (note_id, user_id))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Note not found")
    c.execute("UPDATE notes SET title=?, content=? WHERE id=?", (note.title, note.content, note_id))
    conn.commit()
    c.execute("SELECT * FROM notes WHERE id=?", (note_id,))
    row = c.fetchone()
    conn.close()
    return NoteOut(id=row["id"], title=row["title"], content=row["content"], created_at=row["created_at"])

@app.delete("/notes/{note_id}")
def delete_note(note_id: int, user_id: int = Depends(get_current_user)):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM notes WHERE id=? AND user_id=?", (note_id, user_id))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Note not found")
    c.execute("DELETE FROM notes WHERE id=?", (note_id,))
    conn.commit()
    conn.close()
    return {"msg": "Note deleted"}
