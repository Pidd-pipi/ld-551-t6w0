import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { LessonNote, LessonNoteMarks } from '@/types/note'
import request from '@/utils/request'

export const useNoteStore = defineStore('note', () => {
  const notedLessonIds = ref<number[]>([])

  async function fetchNote(lessonId: number) {
    return await request.get<unknown, LessonNote>(`/lessons/${lessonId}/note`)
  }

  async function saveNote(lessonId: number, content: string, version: number) {
    return await request.put<unknown, LessonNote>(`/lessons/${lessonId}/note`, { content, version })
  }

  async function fetchCourseNoteMarks(courseId: number) {
    try {
      const data = await request.get<unknown, LessonNoteMarks>(`/courses/${courseId}/notes`)
      notedLessonIds.value = data.lesson_ids
    } catch {
      notedLessonIds.value = []
    }
  }

  return { notedLessonIds, fetchNote, saveNote, fetchCourseNoteMarks }
})
