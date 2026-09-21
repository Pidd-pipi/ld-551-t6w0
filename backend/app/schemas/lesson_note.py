from datetime import datetime

from pydantic import BaseModel, Field


class LessonNoteSave(BaseModel):
    content: str = Field(default="", max_length=10000)
    version: int = Field(ge=0)


class LessonNoteResponse(BaseModel):
    lesson_id: int
    content: str
    version: int
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class LessonNoteMarksResponse(BaseModel):
    lesson_ids: list[int]
