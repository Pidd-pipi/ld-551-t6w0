from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.exceptions.course import CourseNotFoundException
from app.exceptions.note import NoteAccessException, NoteConflictException
from app.models.chapter import Chapter
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.note import LessonNote
from app.models.user import User


class NoteService:
    @staticmethod
    def _get_authorized_enrollment(db: Session, user: User, lesson_id: int) -> Enrollment:
        """课时存在且学员已报名对应课程时，才允许读写笔记（试看不授予笔记权限）。"""
        lesson = db.get(Lesson, lesson_id)
        if not lesson:
            raise CourseNotFoundException("课时不存在")
        chapter = db.get(Chapter, lesson.chapter_id)
        enrollment = db.query(Enrollment).filter_by(user_id=user.id, course_id=chapter.course_id).first()
        if not enrollment:
            raise NoteAccessException()
        return enrollment

    @staticmethod
    def get_note(db: Session, user: User, lesson_id: int) -> LessonNote | None:
        NoteService._get_authorized_enrollment(db, user, lesson_id)
        return db.query(LessonNote).filter_by(user_id=user.id, lesson_id=lesson_id).first()

    @staticmethod
    def save_note(db: Session, user: User, lesson_id: int, content: str, expected_version: int) -> LessonNote:
        NoteService._get_authorized_enrollment(db, user, lesson_id)
        note = db.query(LessonNote).filter_by(user_id=user.id, lesson_id=lesson_id).first()

        if note is None:
            if expected_version != 0:
                raise NoteConflictException(version=0, content="")
            note = LessonNote(user_id=user.id, lesson_id=lesson_id, content=content, version=1)
            db.add(note)
            try:
                db.commit()
            except IntegrityError:
                # 并发下另一请求已抢先创建（一人一课一份的唯一约束）
                db.rollback()
                note = db.query(LessonNote).filter_by(user_id=user.id, lesson_id=lesson_id).first()
                raise NoteConflictException(version=note.version, content=note.content) from None
            db.refresh(note)
            return note

        if note.version != expected_version:
            raise NoteConflictException(version=note.version, content=note.content)

        # 条件更新：仅当数据库中版本仍是期望版本时才写入，形成新版本
        result = db.execute(
            update(LessonNote)
            .where(LessonNote.id == note.id, LessonNote.version == expected_version)
            .values(content=content, version=expected_version + 1)
        )
        if result.rowcount != 1:
            db.rollback()
            latest = db.query(LessonNote).filter_by(id=note.id).first()
            raise NoteConflictException(version=latest.version, content=latest.content)
        db.commit()
        db.refresh(note)
        return note

    @staticmethod
    def list_noted_lesson_ids(db: Session, user: User, course_id: int) -> list[int]:
        enrollment = db.query(Enrollment).filter_by(user_id=user.id, course_id=course_id).first()
        if not enrollment:
            raise NoteAccessException()
        rows = (
            db.query(LessonNote.lesson_id)
            .join(Lesson, Lesson.id == LessonNote.lesson_id)
            .join(Chapter, Chapter.id == Lesson.chapter_id)
            .filter(
                LessonNote.user_id == user.id,
                Chapter.course_id == course_id,
                LessonNote.content != "",
            )
            .all()
        )
        return [row[0] for row in rows]
