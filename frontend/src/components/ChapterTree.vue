<template>
  <el-tree
    class="chapter-tree"
    :data="treeData"
    node-key="key"
    default-expand-all
    draggable
    :allow-drop="allowDrop"
    @node-click="handleClick"
  >
    <template #default="{ data }">
      <span class="tree-node">
        <span class="node-label">
          <el-icon v-if="data.lesson && notedLessonIds.includes(data.lesson.id)" class="note-icon" title="本课时有笔记">
            <EditPen />
          </el-icon>
          <span>{{ data.label }}</span>
        </span>
        <el-tag v-if="data.lesson?.is_free" size="small" type="warning">试看</el-tag>
      </span>
    </template>
  </el-tree>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { EditPen } from '@element-plus/icons-vue'
import type { Chapter } from '@/types/chapter'
import type { Lesson } from '@/types/lesson'

const props = withDefaults(defineProps<{ chapters: Chapter[]; notedLessonIds?: number[] }>(), {
  notedLessonIds: () => []
})
const emit = defineEmits<{ selectLesson: [lesson: Lesson] }>()

const treeData = computed(() =>
  props.chapters.map((chapter) => ({
    key: `chapter-${chapter.id}`,
    label: `${chapter.sort_order}. ${chapter.title}`,
    children: chapter.lessons.map((lesson) => ({
      key: `lesson-${lesson.id}`,
      label: `${lesson.sort_order}. ${lesson.title} · ${lesson.duration}分钟`,
      lesson
    }))
  }))
)

function allowDrop() {
  return true
}

function handleClick(data: { lesson?: Lesson }) {
  if (data.lesson) emit('selectLesson', data.lesson)
}
</script>

<style scoped>
.chapter-tree {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 8px;
}

.tree-node {
  width: 100%;
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.node-label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.note-icon {
  color: #2563eb;
}
</style>
