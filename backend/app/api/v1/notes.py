from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.note import NoteResponse, NoteSaveRequest
from app.services.note_service import NoteService

router = APIRouter(prefix="/lessons", tags=["lesson-notes"])


@router.get("/{lesson_id}/note", response_model=NoteResponse)
def get_note(lesson_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    note = NoteService.get_note(db, user, lesson_id)
    if not note:
        return NoteResponse(lesson_id=lesson_id, content="", version=0)
    return note


@router.put("/{lesson_id}/note", response_model=NoteResponse)
def save_note(lesson_id: int, payload: NoteSaveRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    note = NoteService.save_note(db, user, lesson_id, payload.content, payload.version)
    return NoteResponse(lesson_id=lesson_id, content=note.content, version=note.version, updated_at=note.updated_at)
