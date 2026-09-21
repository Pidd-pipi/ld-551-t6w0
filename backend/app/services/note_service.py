from datetime import UTC, datetime

from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.constants.enums import CourseStatus
from app.exceptions.course import CourseNotFoundException
from app.exceptions.note import NoteAccessDeniedException, NoteConflictException
from app.models.chapter import Chapter
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.lesson_note import LessonNote
from app.models.user import User
from app.schemas.lesson_note import LessonNoteSave
from app.services.audit_service import AuditService


class NoteService:
    @staticmethod
    def _check_access(db: Session, user: User, lesson_id: int) -> Lesson:
        lesson = db.get(Lesson, lesson_id)
        if not lesson:
            raise CourseNotFoundException("课时不存在")
        course = lesson.chapter.course
        if course.status != CourseStatus.PUBLISHED:
            raise NoteAccessDeniedException("课时当前不可见")
        enrollment = db.query(Enrollment).filter_by(user_id=user.id, course_id=course.id).first()
        if not enrollment:
            raise NoteAccessDeniedException("报名课程后才能使用课时笔记")
        return lesson

    @staticmethod
    def get_note(db: Session, user: User, lesson_id: int) -> LessonNote | None:
        NoteService._check_access(db, user, lesson_id)
        return db.query(LessonNote).filter_by(user_id=user.id, lesson_id=lesson_id).first()

    @staticmethod
    def save_note(db: Session, user: User, lesson_id: int, payload: LessonNoteSave, ip_address: str | None = None) -> LessonNote:
        NoteService._check_access(db, user, lesson_id)
        note = db.query(LessonNote).filter_by(user_id=user.id, lesson_id=lesson_id).first()
        if note is None:
            if payload.version != 0:
                raise NoteConflictException(current_version=None)
            note = LessonNote(user_id=user.id, lesson_id=lesson_id, content=payload.content, version=1)
            db.add(note)
            action = "CREATE"
        else:
            if note.version != payload.version:
                raise NoteConflictException(current_version=note.version)
            result = db.execute(
                update(LessonNote)
                .where(LessonNote.id == note.id, LessonNote.version == payload.version)
                .values(content=payload.content, version=LessonNote.version + 1, updated_at=datetime.now(UTC))
            )
            if result.rowcount == 0:
                db.rollback()
                raise NoteConflictException()
            note.content = payload.content
            action = "UPDATE"
        try:
            db.flush()
            AuditService.record(
                db,
                user_id=user.id,
                action=action,
                entity="LessonNote",
                entity_id=str(note.id),
                after_data={"lesson_id": lesson_id, "version": note.version},
                ip_address=ip_address,
            )
            db.commit()
        except IntegrityError:
            db.rollback()
            raise NoteConflictException() from None
        db.refresh(note)
        return note

    @staticmethod
    def list_noted_lesson_ids(db: Session, user: User, course_id: int) -> list[int]:
        enrollment = db.query(Enrollment).filter_by(user_id=user.id, course_id=course_id).first()
        if not enrollment:
            raise NoteAccessDeniedException("报名课程后才能查看课时笔记")
        rows = (
            db.query(LessonNote.lesson_id)
            .join(Lesson, LessonNote.lesson_id == Lesson.id)
            .join(Chapter, Lesson.chapter_id == Chapter.id)
            .filter(Chapter.course_id == course_id, LessonNote.user_id == user.id, LessonNote.content != "")
            .all()
        )
        return [row[0] for row in rows]
