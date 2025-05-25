from sqlalchemy.orm import Session
from models import Note
import datetime

def create_note(db: Session, user_id: int, title: str, content: str):
    note = Note(user_id=user_id, title=title, content=content)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note

def get_notes(db: Session, user_id: int):
    return db.query(Note).filter(Note.user_id == user_id).order_by(Note.created_at.desc()).all()

def get_note(db: Session, note_id: int, user_id: int):
    return db.query(Note).filter(Note.id == note_id, Note.user_id == user_id).first()

def update_note(db: Session, note_id: int, user_id: int, title: str, content: str):
    note = get_note(db, note_id, user_id)
    if note:
        note.title = title
        note.content = content
        db.commit()
        db.refresh(note)
    return note

def delete_note(db: Session, note_id: int, user_id: int):
    note = get_note(db, note_id, user_id)
    if note:
        db.delete(note)
        db.commit()
    return note