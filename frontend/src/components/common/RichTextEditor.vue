<template>
  <div class="rich-text-editor">
    <div v-if="editor" class="editor-toolbar">
      <div class="toolbar-group">
        <button
          type="button"
          :class="{ active: editor.isActive('bold') }"
          @click="editor.chain().focus().toggleBold().run()"
          title="Bold"
        >
          <span class="toolbar-icon">B</span>
        </button>
        <button
          type="button"
          :class="{ active: editor.isActive('italic') }"
          @click="editor.chain().focus().toggleItalic().run()"
          title="Italic"
        >
          <span class="toolbar-icon italic">I</span>
        </button>
        <button
          type="button"
          :class="{ active: editor.isActive('strike') }"
          @click="editor.chain().focus().toggleStrike().run()"
          title="Strikethrough"
        >
          <span class="toolbar-icon strike">S</span>
        </button>
      </div>

      <div class="toolbar-divider"></div>

      <div class="toolbar-group">
        <button
          type="button"
          :class="{ active: editor.isActive('heading', { level: 1 }) }"
          @click="editor.chain().focus().toggleHeading({ level: 1 }).run()"
          title="Heading 1"
        >
          <span class="toolbar-icon">H1</span>
        </button>
        <button
          type="button"
          :class="{ active: editor.isActive('heading', { level: 2 }) }"
          @click="editor.chain().focus().toggleHeading({ level: 2 }).run()"
          title="Heading 2"
        >
          <span class="toolbar-icon">H2</span>
        </button>
        <button
          type="button"
          :class="{ active: editor.isActive('heading', { level: 3 }) }"
          @click="editor.chain().focus().toggleHeading({ level: 3 }).run()"
          title="Heading 3"
        >
          <span class="toolbar-icon">H3</span>
        </button>
      </div>

      <div class="toolbar-divider"></div>

      <div class="toolbar-group">
        <button
          type="button"
          :class="{ active: editor.isActive('bulletList') }"
          @click="editor.chain().focus().toggleBulletList().run()"
          title="Bullet List"
        >
          <span class="toolbar-icon">•</span>
        </button>
        <button
          type="button"
          :class="{ active: editor.isActive('orderedList') }"
          @click="editor.chain().focus().toggleOrderedList().run()"
          title="Ordered List"
        >
          <span class="toolbar-icon">1.</span>
        </button>
        <button
          type="button"
          :class="{ active: editor.isActive('taskList') }"
          @click="editor.chain().focus().toggleTaskList().run()"
          title="Task List (Checkboxes)"
        >
          <span class="toolbar-icon checkbox-icon">☑</span>
        </button>
      </div>

      <div class="toolbar-divider"></div>

      <div class="toolbar-group">
        <button
          type="button"
          :class="{ active: editor.isActive('blockquote') }"
          @click="editor.chain().focus().toggleBlockquote().run()"
          title="Quote"
        >
          <span class="toolbar-icon">"</span>
        </button>
        <button
          type="button"
          :class="{ active: editor.isActive('code') }"
          @click="editor.chain().focus().toggleCode().run()"
          title="Inline Code"
        >
          <span class="toolbar-icon code">&lt;/&gt;</span>
        </button>
      </div>
    </div>

    <editor-content :editor="editor" class="editor-content" />
  </div>
</template>

<script setup>
import { watch, onBeforeUnmount } from 'vue'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import TaskList from '@tiptap/extension-task-list'
import TaskItem from '@tiptap/extension-task-item'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: 'Enter description...'
  }
})

const emit = defineEmits(['update:modelValue'])

const editor = useEditor({
  content: props.modelValue,
  extensions: [
    StarterKit,
    TaskList,
    TaskItem.configure({
      nested: true,
    }),
  ],
  onUpdate: ({ editor }) => {
    const html = editor.getHTML()
    // Emit empty string if content is just an empty paragraph
    emit('update:modelValue', html === '<p></p>' ? '' : html)
  }
})

// Watch for external changes to modelValue
watch(
  () => props.modelValue,
  (newValue) => {
    if (editor.value && newValue !== editor.value.getHTML()) {
      editor.value.commands.setContent(newValue || '', false)
    }
  }
)

onBeforeUnmount(() => {
  if (editor.value) {
    editor.value.destroy()
  }
})
</script>

<style scoped>
.rich-text-editor {
  border: 1px solid #d1d5db;
  border-radius: 6px;
  overflow: hidden;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.rich-text-editor:focus-within {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.editor-toolbar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  flex-wrap: wrap;
}

.toolbar-group {
  display: flex;
  gap: 2px;
}

.toolbar-divider {
  width: 1px;
  height: 24px;
  background: #d1d5db;
  margin: 0 4px;
}

.editor-toolbar button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  border: none;
  background: transparent;
  border-radius: 4px;
  cursor: pointer;
  color: #374151;
  transition: all 0.15s;
}

.editor-toolbar button:hover {
  background: #e5e7eb;
}

.editor-toolbar button.active {
  background: #2563eb;
  color: white;
}

.toolbar-icon {
  font-weight: 700;
  font-size: 13px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.toolbar-icon.italic {
  font-style: italic;
}

.toolbar-icon.strike {
  text-decoration: line-through;
}

.toolbar-icon.code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 11px;
  font-weight: 500;
}

.editor-content {
  min-height: 120px;
  max-height: 300px;
  overflow-y: auto;
}

.editor-content :deep(.tiptap) {
  padding: 12px;
  outline: none;
  min-height: 120px;
}

.editor-content :deep(.tiptap p) {
  margin: 0 0 0.5em 0;
}

.editor-content :deep(.tiptap p:last-child) {
  margin-bottom: 0;
}

.editor-content :deep(.tiptap h1) {
  font-size: 1.5em;
  font-weight: 700;
  margin: 0 0 0.5em 0;
}

.editor-content :deep(.tiptap h2) {
  font-size: 1.25em;
  font-weight: 600;
  margin: 0 0 0.5em 0;
}

.editor-content :deep(.tiptap h3) {
  font-size: 1.1em;
  font-weight: 600;
  margin: 0 0 0.5em 0;
}

.editor-content :deep(.tiptap ul) {
  list-style-type: disc;
  padding-left: 1.5em;
  margin: 0 0 0.5em 0;
}

.editor-content :deep(.tiptap ol) {
  list-style-type: decimal;
  padding-left: 1.5em;
  margin: 0 0 0.5em 0;
}

.editor-content :deep(.tiptap li) {
  margin: 0.25em 0;
  display: list-item;
}

.editor-content :deep(.tiptap blockquote) {
  border-left: 3px solid #d1d5db;
  padding-left: 1em;
  margin: 0.5em 0;
  color: #6b7280;
}

.editor-content :deep(.tiptap code) {
  background: #f3f4f6;
  padding: 0.1em 0.3em;
  border-radius: 3px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.9em;
}

.editor-content :deep(.tiptap pre) {
  background: #1f2937;
  color: #f9fafb;
  padding: 0.75em 1em;
  border-radius: 6px;
  overflow-x: auto;
  margin: 0.5em 0;
}

.editor-content :deep(.tiptap pre code) {
  background: none;
  padding: 0;
  color: inherit;
}

/* Task List (Checkbox) Styles */
.editor-content :deep(.tiptap ul[data-type="taskList"]) {
  list-style: none;
  padding-left: 0;
  margin: 0 0 0.5em 0;
}

.editor-content :deep(.tiptap ul[data-type="taskList"] li) {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  margin: 0.25em 0;
}

.editor-content :deep(.tiptap ul[data-type="taskList"] li > label) {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  user-select: none;
  margin-top: 0.15em;
}

.editor-content :deep(.tiptap ul[data-type="taskList"] li > label input[type="checkbox"]) {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: #2563eb;
}

.editor-content :deep(.tiptap ul[data-type="taskList"] li > div) {
  flex: 1;
  min-width: 0;
}

.editor-content :deep(.tiptap ul[data-type="taskList"] li[data-checked="true"] > div) {
  text-decoration: line-through;
  color: #9ca3af;
}

/* Nested task lists */
.editor-content :deep(.tiptap ul[data-type="taskList"] ul[data-type="taskList"]) {
  margin-left: 1.5rem;
  margin-top: 0.25em;
  margin-bottom: 0;
}

.toolbar-icon.checkbox-icon {
  font-size: 14px;
}
</style>

