import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'
import type { LessonNote, NoteConflictDetail, NoteMarkers } from '@/types/note'
import request from '@/utils/request'

/** 判断失败是否为 409 版本冲突，并取出服务端最新内容。 */
export function getNoteConflict(error: unknown): NoteConflictDetail | null {
  if (axios.isAxiosError(error) && error.response?.status === 409) {
    return (error.response.data?.detail as NoteConflictDetail) ?? null
  }
  return null
}

export const useNoteStore = defineStore('note', () => {
  const notesByLesson = ref<Record<number, LessonNote>>({})
  const notedLessonIds = ref<number[]>([])

  async function fetchNote(lessonId: number): Promise<LessonNote> {
    const note = await request.get<unknown, LessonNote>(`/lessons/${lessonId}/note`)
    notesByLesson.value[lessonId] = note
    return note
  }

  /** 携带当前版本保存；过期版本抛出 409 且不覆盖，调用方按冲突提示处理。 */
  async function saveNote(lessonId: number, content: string, version: number): Promise<LessonNote> {
    const note = await request.put<unknown, LessonNote>(`/lessons/${lessonId}/note`, { content, version })
    notesByLesson.value[lessonId] = note
    return note
  }

  async function fetchNoteMarkers(courseId: number): Promise<number[]> {
    const data = await request.get<unknown, NoteMarkers>(`/enrollments/${courseId}/note-markers`)
    notedLessonIds.value = data.lesson_ids
    return data.lesson_ids
  }

  function hasNote(lessonId: number): boolean {
    return notedLessonIds.value.includes(lessonId)
  }

  return { notesByLesson, notedLessonIds, fetchNote, saveNote, fetchNoteMarkers, hasNote }
})
