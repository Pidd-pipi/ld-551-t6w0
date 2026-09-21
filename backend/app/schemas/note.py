from datetime import datetime

from pydantic import BaseModel, Field

MAX_NOTE_LENGTH = 20000


class NoteSaveRequest(BaseModel):
    content: str = Field("", max_length=MAX_NOTE_LENGTH)
    version: int = Field(0, ge=0)


class NoteResponse(BaseModel):
    lesson_id: int
    content: str
    version: int
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class NoteMarkersResponse(BaseModel):
    lesson_ids: list[int]
