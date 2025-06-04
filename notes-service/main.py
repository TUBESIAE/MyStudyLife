from fastapi import FastAPI, Depends, HTTPException, status, Header
from typing import List, Optional
import sqlite3
from datetime import datetime
from models import NoteCreate, NoteOut
from utils import validate_token, get_health_status
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Health check endpoint
@app.get("/health")
async def health_check():
    return get_health_status()

async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = authorization.split(" ", 1)[1]
    return await validate_token(token)

@app.post("/notes", response_model=NoteOut)
async def create_note(note: NoteCreate, user: dict = Depends(get_current_user)):
    try:
        conn = get_db()
        c = conn.cursor()
        now = datetime.utcnow().isoformat()
        c.execute("INSERT INTO notes (user_id, title, content, created_at) VALUES (?, ?, ?, ?)", 
                 (user["id"], note.title, note.content, now))
        note_id = c.lastrowid
        conn.commit()
        c.execute("SELECT * FROM notes WHERE id=?", (note_id,))
        row = c.fetchone()
        conn.close()
        return NoteOut(id=row["id"], title=row["title"], content=row["content"], created_at=row["created_at"])
    except Exception as e:
        logger.error(f"Error in create_note: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/notes", response_model=List[NoteOut])
async def get_notes(user: dict = Depends(get_current_user)):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM notes WHERE user_id=? ORDER BY created_at DESC", (user["id"],))
        rows = c.fetchall()
        conn.close()
        return [NoteOut(id=row["id"], title=row["title"], content=row["content"], created_at=row["created_at"]) for row in rows]
    except Exception as e:
        logger.error(f"Error in get_notes: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/notes/{note_id}", response_model=NoteOut)
async def update_note(note_id: int, note: NoteCreate, user: dict = Depends(get_current_user)):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM notes WHERE id=? AND user_id=?", (note_id, user["id"]))
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
    except Exception as e:
        logger.error(f"Error in update_note: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/notes/{note_id}")
async def delete_note(note_id: int, user: dict = Depends(get_current_user)):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM notes WHERE id=? AND user_id=?", (note_id, user["id"]))
        row = c.fetchone()
        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="Note not found")
        c.execute("DELETE FROM notes WHERE id=?", (note_id,))
        conn.commit()
        conn.close()
        return {"msg": "Note deleted"}
    except Exception as e:
        logger.error(f"Error in delete_note: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/")
async def root():
    return {"message": "Notes Service is running"}
