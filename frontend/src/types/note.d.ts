export interface LessonNote {
  lesson_id: number
  content: string
  version: number
  updated_at: string | null
}

export interface LessonNoteMarks {
  lesson_ids: number[]
}
