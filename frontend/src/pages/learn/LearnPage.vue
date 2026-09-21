<template>
  <section class="page learn-page">
    <LessonPlayer :lesson="selectedLesson" @complete="complete" />
    <aside class="learn-side">
      <ProgressIndicator :percentage="progress?.progress || 0" type="circle" label="学习进度" />
      <ChapterTree :chapters="chapters" :noted-lesson-ids="notedLessonIds" @select-lesson="selectLesson" />
      <section class="note-panel">
        <header class="note-header">
          <span>课时笔记</span>
          <el-tag v-if="noteVersion > 0" size="small" type="info">v{{ noteVersion }}</el-tag>
        </header>
        <el-alert
          v-if="noteConflict"
          class="note-conflict"
          type="warning"
          :closable="false"
          title="笔记已在其他窗口更新，继续保存将被拦截"
        >
          <el-button size="small" type="warning" plain @click="discardAndRefresh">放弃修改并刷新</el-button>
        </el-alert>
        <el-input v-model="noteContent" type="textarea" :rows="6" placeholder="记录本节课的笔记" :disabled="noteConflict" />
        <el-button type="primary" :loading="noteSaving" :disabled="noteConflict || !selectedLesson" @click="saveNote">
          保存笔记
        </el-button>
      </section>
    </aside>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import ChapterTree from '@/components/ChapterTree.vue'
import LessonPlayer from '@/components/LessonPlayer.vue'
import ProgressIndicator from '@/components/ProgressIndicator.vue'
import { useCourseStore } from '@/stores/courseStore'
import { useEnrollmentStore } from '@/stores/enrollmentStore'
import { useNoteStore } from '@/stores/noteStore'
import type { Lesson } from '@/types/lesson'

const route = useRoute()
const courseStore = useCourseStore()
const enrollmentStore = useEnrollmentStore()
const noteStore = useNoteStore()
const selectedLesson = ref<Lesson | null>(null)
const noteContent = ref('')
const noteVersion = ref(0)
const noteSaving = ref(false)
const noteConflict = ref(false)
const chapters = computed(() => courseStore.chapters)
const progress = computed(() => enrollmentStore.progress)
const notedLessonIds = computed(() => noteStore.notedLessonIds)
const courseId = Number(route.params.courseId)

async function complete(score?: number) {
  if (selectedLesson.value) await enrollmentStore.completeLesson(selectedLesson.value.id, score)
}

async function loadNote(lessonId: number) {
  const note = await noteStore.fetchNote(lessonId)
  noteContent.value = note.content
  noteVersion.value = note.version
  noteConflict.value = false
}

async function selectLesson(lesson: Lesson) {
  selectedLesson.value = lesson
  await loadNote(lesson.id)
}

async function saveNote() {
  if (!selectedLesson.value) return
  noteSaving.value = true
  try {
    const saved = await noteStore.saveNote(selectedLesson.value.id, noteContent.value, noteVersion.value)
    noteVersion.value = saved.version
    noteConflict.value = false
    ElMessage.success('笔记已保存')
    await noteStore.fetchCourseNoteMarks(courseId)
  } catch (error: unknown) {
    if ((error as { response?: { status?: number } })?.response?.status === 409) {
      noteConflict.value = true
    }
  } finally {
    noteSaving.value = false
  }
}

async function discardAndRefresh() {
  if (!selectedLesson.value) return
  await loadNote(selectedLesson.value.id)
  ElMessage.info('已放弃本地修改，恢复为最新笔记')
}

onMounted(async () => {
  await courseStore.fetchCourse(courseId)
  selectedLesson.value = courseStore.chapters[0]?.lessons[0] || null
  await enrollmentStore.fetchProgress(courseId)
  await noteStore.fetchCourseNoteMarks(courseId)
  if (selectedLesson.value) await loadNote(selectedLesson.value.id)
})
</script>

<style scoped>
.learn-page {
  display: grid;
  grid-template-columns: minmax(0, 7fr) minmax(300px, 3fr);
  gap: 20px;
}

.learn-side {
  display: grid;
  gap: 16px;
  align-content: start;
}

.note-panel {
  display: grid;
  gap: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px;
}

.note-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.note-conflict {
  margin-bottom: 4px;
}
</style>
