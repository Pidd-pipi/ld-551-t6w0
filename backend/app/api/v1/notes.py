from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.lesson_note import LessonNoteMarksResponse, LessonNoteResponse, LessonNoteSave
from app.services.note_service import NoteService

router = APIRouter(tags=["notes"])


@router.get("/lessons/{lesson_id}/note", response_model=LessonNoteResponse)
def get_note(lesson_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    note = NoteService.get_note(db, user, lesson_id)
    if note is None:
        return LessonNoteResponse(lesson_id=lesson_id, content="", version=0, updated_at=None)
    return note


@router.put("/lessons/{lesson_id}/note", response_model=LessonNoteResponse)
def save_note(
    lesson_id: int,
    payload: LessonNoteSave,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return NoteService.save_note(db, user, lesson_id, payload, request.client.host if request.client else None)


@router.get("/courses/{course_id}/notes", response_model=LessonNoteMarksResponse)
def list_course_note_marks(course_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return LessonNoteMarksResponse(lesson_ids=NoteService.list_noted_lesson_ids(db, user, course_id))
