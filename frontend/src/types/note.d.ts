export interface LessonNote {
  lesson_id: number
  content: string
  version: number
  updated_at?: string | null
}

export interface NoteSavePayload {
  content: string
  version: number
}

export interface NoteConflictDetail {
  version: number
  content: string
}

export interface NoteMarkers {
  lesson_ids: number[]
}
