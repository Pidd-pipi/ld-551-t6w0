<template>
  <section class="page learn-page">
    <div class="learn-main">
      <LessonPlayer :lesson="selectedLesson" @complete="complete" />
      <section class="note-panel">
        <header class="note-head">
          <h3>课时笔记</h3>
          <span v-if="serverNote" class="note-meta">
            版本 v{{ serverNote.version }}<template v-if="serverNote.updated_at"> · {{ formatTime(serverNote.updated_at) }}</template>
          </span>
        </header>
        <el-input
          v-model="draft"
          type="textarea"
          :rows="8"
          :placeholder="noteReadonly ? '报名课程后即可记录课时笔记（试看课时不支持笔记）' : '记录本课时的学习要点…'"
          :disabled="noteReadonly || noteLoading"
        />
        <div class="note-actions">
          <el-button type="primary" :loading="noteLoading" :disabled="noteReadonly || !dirty" @click="save">保存笔记</el-button>
          <el-button :disabled="noteReadonly || !dirty || noteLoading" @click="discard">放弃修改</el-button>
          <el-button text :loading="noteLoading" @click="reload">刷新</el-button>
        </div>
        <p v-if="noteReadonly" class="note-tip">仅已报名学员可在可见课时中读写笔记，试看内容不开放笔记。</p>
      </section>
    </div>
    <aside class="learn-side">
      <ProgressIndicator :percentage="progress?.progress || 0" type="circle" label="学习进度" />
      <ChapterTree
        :chapters="chapters"
        :noted-lesson-ids="noteStore.notedLessonIds"
        @select-lesson="selectLesson"
      />
    </aside>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import ChapterTree from '@/components/ChapterTree.vue'
import LessonPlayer from '@/components/LessonPlayer.vue'
import ProgressIndicator from '@/components/ProgressIndicator.vue'
import { useCourseStore } from '@/stores/courseStore'
import { useEnrollmentStore } from '@/stores/enrollmentStore'
import { getNoteConflict, useNoteStore } from '@/stores/noteStore'
import type { Lesson } from '@/types/lesson'
import type { LessonNote } from '@/types/note'

const route = useRoute()
const courseStore = useCourseStore()
const enrollmentStore = useEnrollmentStore()
const noteStore = useNoteStore()

const selectedLesson = ref<Lesson | null>(null)
const draft = ref('')
const serverNote = ref<LessonNote | null>(null)
const noteLoading = ref(false)
const noteReadonly = ref(false)

const chapters = computed(() => courseStore.chapters)
const progress = computed(() => enrollmentStore.progress)
const dirty = computed(() => serverNote.value !== null && draft.value !== serverNote.value.content)

async function complete(score?: number) {
  if (selectedLesson.value) await enrollmentStore.completeLesson(selectedLesson.value.id, score)
}

async function loadNote(lesson: Lesson) {
  noteLoading.value = true
  noteReadonly.value = false
  try {
    const note = await noteStore.fetchNote(lesson.id)
    serverNote.value = note
    draft.value = note.content
  } catch (error) {
    // 未报名（含仅试看）：笔记只读展示；其余错误由全局拦截器提示
    if (axios.isAxiosError(error) && error.response?.status === 403) {
      serverNote.value = { lesson_id: lesson.id, content: '', version: 0 }
      draft.value = ''
      noteReadonly.value = true
    }
  } finally {
    noteLoading.value = false
  }
}

async function reload() {
  if (!selectedLesson.value) return
  await loadNote(selectedLesson.value)
  ElMessage.success('已刷新为最新笔记')
}

function discard() {
  if (!serverNote.value) return
  draft.value = serverNote.value.content
}

function selectLesson(lesson: Lesson) {
  if (dirty.value) {
    ElMessage.warning('当前笔记有未保存修改，请先保存或放弃')
    return
  }
  selectedLesson.value = lesson
}

async function save() {
  if (!selectedLesson.value || !serverNote.value) return
  noteLoading.value = true
  try {
    const note = await noteStore.saveNote(selectedLesson.value.id, draft.value, serverNote.value.version)
    serverNote.value = note
    draft.value = note.content
    await noteStore.fetchNoteMarkers(Number(route.params.courseId))
    ElMessage.success('笔记已保存')
  } catch (error) {
    const conflict = getNoteConflict(error)
    if (conflict) {
      try {
        await ElMessageBox.confirm(
          '笔记在其他设备或标签页已被更新，当前版本已过期。加载最新内容将覆盖你本地未保存的修改，是否继续？',
          '笔记版本冲突',
          { confirmButtonText: '加载最新版本', cancelButtonText: '保留我的修改', type: 'warning' }
        )
        serverNote.value = {
          lesson_id: selectedLesson.value.id,
          content: conflict.content,
          version: conflict.version
        }
        draft.value = conflict.content
        await noteStore.fetchNoteMarkers(Number(route.params.courseId))
      } catch {
        // 用户选择保留本地修改，停留编辑
      }
    }
  } finally {
    noteLoading.value = false
  }
}

watch(selectedLesson, (lesson) => {
  if (lesson) void loadNote(lesson)
})

onMounted(async () => {
  const courseId = Number(route.params.courseId)
  await courseStore.fetchCourse(courseId)
  selectedLesson.value = courseStore.chapters[0]?.lessons[0] || null
  await enrollmentStore.fetchProgress(courseId)
  try {
    await noteStore.fetchNoteMarkers(courseId)
  } catch {
    // 未报名时标记接口不可用，章节树不展示笔记标记
  }
})

function formatTime(value: string): string {
  return new Date(value).toLocaleString()
}
</script>

<style scoped>
.learn-page {
  display: grid;
  grid-template-columns: minmax(0, 7fr) minmax(300px, 3fr);
  gap: 20px;
}

.learn-main {
  display: grid;
  gap: 16px;
}

.learn-side {
  display: grid;
  gap: 16px;
  align-content: start;
}

.note-panel {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  display: grid;
  gap: 12px;
}

.note-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.note-head h3 {
  margin: 0;
}

.note-meta {
  color: #6b7280;
  font-size: 12px;
}

.note-actions {
  display: flex;
  gap: 8px;
}

.note-tip {
  margin: 0;
  color: #b45309;
  font-size: 12px;
}
</style>
