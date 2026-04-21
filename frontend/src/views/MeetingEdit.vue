<template>
  <div class="meeting-edit-view">
    <div class="view-header">
      <div class="header-left">
        <router-link to="/meetings" class="back-link">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m15 18-6-6 6-6"/>
          </svg>
          Back to meeting notes
        </router-link>
        <h2 v-if="meeting">{{ meeting.meeting_id }}</h2>
        <h2 v-else-if="loading">Loading...</h2>
        <h2 v-else>Edit Meeting Note</h2>
      </div>
      <div class="header-actions" v-if="meeting">
        <div class="preview-toggle-wrap">
          <button
            type="button"
            :class="['toggle-btn', { active: !fullPagePreview }]"
            @click="fullPagePreview = false"
            title="Edit mode"
          >
            Edit
          </button>
          <button
            type="button"
            :class="['toggle-btn', { active: fullPagePreview }]"
            @click="fullPagePreview = true"
            title="Preview full page"
          >
            Preview
          </button>
        </div>
        <span class="save-status" v-if="saving">Saving...</span>
        <span class="save-status saved" v-else-if="lastSavedAt">
          Saved {{ formatTime(lastSavedAt) }}
        </span>
        <span class="save-status error" v-else-if="lastSaveError" :title="lastSaveError">
          Save failed
        </span>
        <button
          v-if="!fullPagePreview"
          type="button"
          class="btn-primary"
          @click="saveNow"
          :disabled="saving"
        >
          Save
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <p>Loading meeting note...</p>
    </div>

    <div v-else-if="loadError" class="error-state">
      <p>{{ loadError }}</p>
      <button @click="loadMeeting" class="btn-primary">Retry</button>
    </div>

    <div v-else-if="meeting && fullPagePreview" class="full-page-preview">
      <div class="preview-section">
        <h3 class="preview-section-title">Meeting ID</h3>
        <p class="preview-name">{{ meeting.meeting_id }}</p>
      </div>
      <div class="preview-section" v-if="meeting.org_id">
        <h3 class="preview-section-title">Organization</h3>
        <p class="preview-name">{{ getOrganizationName(meeting.org_id) }}</p>
      </div>
      <div class="preview-section" v-if="meeting.project_id">
        <h3 class="preview-section-title">Project</h3>
        <p class="preview-name">{{ getProjectName(meeting.project_id) }}</p>
      </div>
      <div class="preview-section" v-if="formData.presents">
        <h3 class="preview-section-title">Attendees</h3>
        <p class="preview-name">{{ formData.presents }}</p>
      </div>
      <div class="preview-section" v-if="formData.content">
        <h3 class="preview-section-title">Meeting Notes</h3>
        <div class="markdown-preview form-preview" v-html="formRenderedContent"></div>
      </div>
      <div class="preview-section" v-if="formData.past_steps?.length">
        <h3 class="preview-section-title">Past Steps</h3>
        <div class="steps-list-view">
          <div v-for="(step, index) in formData.past_steps" :key="'pv-past-' + index" class="step-view-item">
            <div class="step-number">{{ index + 1 }}</div>
            <div class="step-content">
              <div class="step-what">{{ step.what }}</div>
              <div class="step-who" v-if="step.who">
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
                {{ step.who }}
              </div>
              <router-link
                v-if="step.todo_id && formData.project_id"
                :to="{ path: `/projects/${formData.project_id}/todos`, query: { highlight: step.todo_id } }"
                class="step-task-link"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/>
                  <circle cx="12" cy="12" r="3"/>
                </svg>
                View Task
              </router-link>
            </div>
          </div>
        </div>
      </div>
      <div class="preview-section" v-if="formData.next_steps?.length">
        <h3 class="preview-section-title">Next Steps</h3>
        <div class="steps-list-view">
          <div v-for="(step, index) in formData.next_steps" :key="'pv-next-' + index" class="step-view-item">
            <div class="step-number">{{ index + 1 }}</div>
            <div class="step-content">
              <div class="step-what">{{ step.what }}</div>
              <div class="step-who" v-if="step.who">
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
                {{ step.who }}
              </div>
              <button
                v-if="formData.project_id && !step.todo_id"
                type="button"
                @click="createTaskFromStep(step, index)"
                class="step-create-task-btn"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 5v14"/>
                  <path d="M5 12h14"/>
                </svg>
                Create Task
              </button>
              <router-link
                v-else-if="step.todo_id && formData.project_id"
                :to="{ path: `/projects/${formData.project_id}/todos`, query: { highlight: step.todo_id } }"
                class="step-task-link"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/>
                  <circle cx="12" cy="12" r="3"/>
                </svg>
                View Task
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </div>

    <form v-else-if="meeting" @submit.prevent="saveNow" class="meeting-form">
      <div class="form-group">
        <label>Meeting ID</label>
        <p class="read-only-value">{{ meeting.meeting_id }}</p>
      </div>

      <div class="form-row">
        <div class="form-group">
          <label for="org_id">Organization</label>
          <select id="org_id" v-model="formData.org_id">
            <option :value="null">None</option>
            <option v-for="org in organizations" :key="org.id" :value="org.id">
              {{ org.name }}
            </option>
          </select>
        </div>
        <div class="form-group">
          <label for="project_id">Project</label>
          <select id="project_id" v-model="formData.project_id">
            <option :value="null">None</option>
            <option v-for="project in filteredProjects" :key="project.id" :value="project.id">
              {{ project.name }}
            </option>
          </select>
        </div>
      </div>

      <div class="form-group">
        <label for="presents">Attendees</label>
        <input
          id="presents"
          v-model="formData.presents"
          type="text"
          placeholder="e.g., John Doe, Jane Smith"
        />
        <span class="form-hint">Comma or semicolon separated</span>
      </div>

      <div class="form-group">
        <label>Meeting Notes (Markdown)</label>
        <div class="markdown-editor-container">
          <div class="editor-tabs">
            <button type="button" :class="['tab-btn', { active: editorTab === 'write' }]" @click="editorTab = 'write'">Write</button>
            <button type="button" :class="['tab-btn', { active: editorTab === 'preview' }]" @click="editorTab = 'preview'">Preview</button>
            <button type="button" class="tab-btn insert-image-btn" @click="triggerImageUpload" title="Insert image">Image</button>
          </div>
          <input ref="imageFileInput" type="file" accept="image/png,image/jpeg,image/gif,image/webp" class="hidden-file-input" @change="onImageFileSelected" />
          <textarea
            v-if="editorTab === 'write'"
            ref="contentInput"
            v-model="formData.content"
            class="markdown-textarea"
            rows="15"
            placeholder="# Meeting Title\n\n## Agenda\n..."
          />
          <div v-else class="markdown-preview form-preview" v-html="formRenderedContent"></div>
        </div>
      </div>

      <!-- Meeting steps (same UX as ProjectDetail project steps) -->
      <div class="steps-editor-section">
        <div class="steps-header">
          <h4>Meeting Steps</h4>
          <p class="steps-hint">Drag steps between lists to move them. Click the grip handle to drag.</p>
        </div>

        <div class="steps-columns">
          <div class="steps-column">
            <div class="steps-column-header past">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
                <path d="M3 3v5h5"/>
              </svg>
              Past Steps
              <span class="step-count">{{ formData.past_steps.length }}</span>
            </div>

            <div
              class="steps-drop-zone"
              :class="{ 'drag-over': dragOverZone === 'past' }"
              @dragover.prevent="handleDragOver($event, 'past')"
              @dragleave="handleDragLeave"
              @drop="handleDrop($event, 'past')"
            >
              <div v-if="formData.past_steps.length === 0" class="empty-drop-zone">
                <span>No past steps yet</span>
                <span class="drop-hint">Drop steps here or add new</span>
              </div>

              <div
                v-for="(step, index) in formData.past_steps"
                :key="'past-' + index"
                class="step-item"
                :class="{ dragging: isDragging && dragSource.list === 'past' && dragSource.index === index }"
                draggable="true"
                @dragstart="handleDragStart($event, 'past', index)"
                @dragend="handleDragEnd"
              >
                <div class="step-drag-handle">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="9" cy="5" r="1"/><circle cx="9" cy="12" r="1"/><circle cx="9" cy="19" r="1"/>
                    <circle cx="15" cy="5" r="1"/><circle cx="15" cy="12" r="1"/><circle cx="15" cy="19" r="1"/>
                  </svg>
                </div>
                <div class="step-fields">
                  <input type="text" v-model="step.what" placeholder="What was done?" class="step-what-input" />
                  <input type="text" v-model="step.who" placeholder="By whom?" class="step-who-input" />
                  <div class="step-task-selector">
                    <label>Linked Task (optional):</label>
                    <select v-model="step.todo_id">
                      <option :value="null">No task linked</option>
                      <option v-for="todo in projectTodos" :key="todo.id" :value="todo.id">
                        {{ todo.title }}
                      </option>
                    </select>
                  </div>
                </div>
                <button type="button" class="step-remove-btn" @click="removeStep('past', index)" title="Remove step">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
                  </svg>
                </button>
              </div>
            </div>

            <button type="button" class="add-step-btn" @click="addStep('past')">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 5v14"/><path d="M5 12h14"/>
              </svg>
              Add Past Step
            </button>
          </div>

          <div class="steps-column">
            <div class="steps-column-header next">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 12h14"/>
                <path d="m12 5 7 7-7 7"/>
              </svg>
              Next Steps
              <span class="step-count">{{ formData.next_steps.length }}</span>
            </div>

            <div
              class="steps-drop-zone"
              :class="{ 'drag-over': dragOverZone === 'next' }"
              @dragover.prevent="handleDragOver($event, 'next')"
              @dragleave="handleDragLeave"
              @drop="handleDrop($event, 'next')"
            >
              <div v-if="formData.next_steps.length === 0" class="empty-drop-zone">
                <span>No next steps yet</span>
                <span class="drop-hint">Drop steps here or add new</span>
              </div>

              <div
                v-for="(step, index) in formData.next_steps"
                :key="'next-' + index"
                class="step-item"
                :class="{ dragging: isDragging && dragSource.list === 'next' && dragSource.index === index }"
                draggable="true"
                @dragstart="handleDragStart($event, 'next', index)"
                @dragend="handleDragEnd"
              >
                <div class="step-drag-handle">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="9" cy="5" r="1"/><circle cx="9" cy="12" r="1"/><circle cx="9" cy="19" r="1"/>
                    <circle cx="15" cy="5" r="1"/><circle cx="15" cy="12" r="1"/><circle cx="15" cy="19" r="1"/>
                  </svg>
                </div>
                <div class="step-fields">
                  <input type="text" v-model="step.what" placeholder="What needs to be done?" class="step-what-input" />
                  <input type="text" v-model="step.who" placeholder="By whom?" class="step-who-input" />
                  <div class="step-task-selector">
                    <label>Linked Task (optional):</label>
                    <select v-model="step.todo_id">
                      <option :value="null">No task linked</option>
                      <option v-for="todo in projectTodos" :key="todo.id" :value="todo.id">
                        {{ todo.title }}
                      </option>
                    </select>
                  </div>
                </div>
                <button type="button" class="step-remove-btn" @click="removeStep('next', index)" title="Remove step">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
                  </svg>
                </button>
              </div>
            </div>

            <button type="button" class="add-step-btn" @click="addStep('next')">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 5v14"/><path d="M5 12h14"/>
              </svg>
              Add Next Step
            </button>
          </div>
        </div>
      </div>
    </form>

    <Modal :show="showCreateTaskModal" title="Create Task from Step" size="large" @close="closeTaskModal">
      <TodoForm :initial-data="taskFromStep?.initialData" @submit="handleTaskCreated" @cancel="closeTaskModal" />
    </Modal>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useMeetingRefStore } from '@/stores/meetingRefStore'
import { uploadNotesImage, projectsApi } from '@/services/api'
import { insertMarkdownAtCursor, renderMarkdownForNotes, meetingNotesContextBaseFromFileRef } from '@/utils/markdownNotes'
import Modal from '@/components/common/Modal.vue'
import TodoForm from '@/components/todo/TodoForm.vue'

const route = useRoute()
const store = useMeetingRefStore()

const meeting = ref(null)
const loading = ref(false)
const loadError = ref(null)

const formData = ref({
  org_id: null,
  project_id: null,
  presents: '',
  content: '',
  past_steps: [],
  next_steps: []
})

const editorTab = ref('write')
const fullPagePreview = ref(false)
const saving = ref(false)
const lastSaveError = ref(null)
const lastSavedAt = ref(null)
const initialLoadDone = ref(false)
const imageFileInput = ref(null)
const contentInput = ref(null)

const isDragging = ref(false)
const dragSource = ref({ list: null, index: null })
const dragOverZone = ref(null)

const showCreateTaskModal = ref(false)
const taskFromStep = ref(null)

const projectTodos = ref([])

const DEBOUNCE_MS = 2500
let debounceTimer = null

const meetingId = computed(() => route.params.id)

const organizations = computed(() => store.organizations)
const filteredProjects = computed(() => {
  if (!formData.value.org_id) return store.projects
  return store.projects.filter(p => p.organization_id === formData.value.org_id)
})

const notesImagesContextBase = computed(() =>
  meeting.value?.file_ref ? meetingNotesContextBaseFromFileRef(meeting.value.file_ref) : ''
)
const formRenderedContent = computed(() =>
  renderMarkdownForNotes(formData.value.content || '', notesImagesContextBase.value)
)

function normalizeStepsFromApi(steps) {
  if (!Array.isArray(steps)) return []
  return steps.map((s) => ({
    what: s.what || '',
    who: s.who || '',
    todo_id: s.todo_id ?? null
  }))
}

function normalizeStepsForPayload(steps) {
  if (!Array.isArray(steps)) return null
  const out = steps
    .filter((s) => s.what && String(s.what).trim())
    .map((s) => {
      const row = {
        what: String(s.what).trim(),
        who: (s.who && String(s.who).trim()) || ''
      }
      if (s.todo_id != null) row.todo_id = s.todo_id
      return row
    })
  return out.length ? out : null
}

function getOrganizationName(orgId) {
  return store.getOrganizationName(orgId)
}

function getProjectName(projectId) {
  return store.getProjectName(projectId)
}

async function loadProjectTodos() {
  const pid = formData.value.project_id
  if (!pid) {
    projectTodos.value = []
    return
  }
  try {
    const res = await projectsApi.getTodos(pid, { limit: 500 })
    projectTodos.value = res.data.todos || []
  } catch (err) {
    console.error('Failed to load project todos:', err)
    projectTodos.value = []
  }
}

function triggerImageUpload() {
  if (!meeting.value?.file_ref) return
  imageFileInput.value?.click()
}

async function onImageFileSelected(event) {
  const file = event.target?.files?.[0]
  event.target.value = ''
  if (!file || !meeting.value?.file_ref) return
  try {
    const result = await uploadNotesImage(file, 'meeting', { file_ref: meeting.value.file_ref })
    const insert = `![](${result.path})`
    const el = contentInput.value
    const setValue = (v) => {
      formData.value.content = v
    }
    if (el) insertMarkdownAtCursor(el, insert, setValue)
    else formData.value.content = (formData.value.content || '') + insert
  } catch (err) {
    console.error('Image upload failed:', err)
  }
}

async function loadMeeting() {
  const id = meetingId.value
  if (!id) {
    loadError.value = 'Missing meeting ID'
    return
  }
  loading.value = true
  loadError.value = null
  try {
    await Promise.all([store.fetchOrganizations(), store.fetchProjects()])
    const item = await store.getItem(id)
    meeting.value = item
    const contentResult = await store.getContent(id)
    formData.value = {
      org_id: item.org_id ?? null,
      project_id: item.project_id ?? null,
      presents: item.attendees || '',
      content: contentResult.content || '',
      past_steps: normalizeStepsFromApi(item.past_steps),
      next_steps: normalizeStepsFromApi(item.next_steps)
    }
    await loadProjectTodos()
    initialLoadDone.value = true
  } catch (err) {
    loadError.value = err.response?.data?.detail || 'Failed to load meeting note'
    console.error('Failed to load meeting:', err)
  } finally {
    loading.value = false
  }
}

function performSave() {
  if (!meeting.value) return
  saving.value = true
  lastSaveError.value = null
  store
    .updateItem(meeting.value.id, {
      org_id: formData.value.org_id,
      project_id: formData.value.project_id,
      attendees: formData.value.presents?.trim() || null,
      content: formData.value.content,
      past_steps: normalizeStepsForPayload(formData.value.past_steps),
      next_steps: normalizeStepsForPayload(formData.value.next_steps)
    })
    .then((updated) => {
      if (updated) meeting.value = updated
      lastSavedAt.value = new Date()
    })
    .catch((err) => {
      lastSaveError.value = err.response?.data?.detail || err.message
    })
    .finally(() => {
      saving.value = false
    })
}

function saveNow() {
  if (debounceTimer) {
    clearTimeout(debounceTimer)
    debounceTimer = null
  }
  performSave()
}

function debouncedSave() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    debounceTimer = null
    performSave()
  }, DEBOUNCE_MS)
}

function addStep(listType) {
  const newStep = { what: '', who: '', todo_id: null }
  if (listType === 'past') {
    formData.value.past_steps.push(newStep)
  } else {
    formData.value.next_steps.push(newStep)
  }
}

function removeStep(listType, index) {
  if (listType === 'past') {
    formData.value.past_steps.splice(index, 1)
  } else {
    formData.value.next_steps.splice(index, 1)
  }
}

function handleDragStart(event, listType, index) {
  isDragging.value = true
  dragSource.value = { list: listType, index }
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', JSON.stringify({ list: listType, index }))
}

function handleDragEnd() {
  isDragging.value = false
  dragSource.value = { list: null, index: null }
  dragOverZone.value = null
}

function handleDragOver(event, targetList) {
  event.preventDefault()
  dragOverZone.value = targetList
}

function handleDragLeave() {
  dragOverZone.value = null
}

function handleDrop(event, targetList) {
  event.preventDefault()
  dragOverZone.value = null

  const data = JSON.parse(event.dataTransfer.getData('text/plain'))
  const sourceList = data.list
  const sourceIndex = data.index

  const sourceArray = sourceList === 'past' ? formData.value.past_steps : formData.value.next_steps
  const targetArray = targetList === 'past' ? formData.value.past_steps : formData.value.next_steps

  const [step] = sourceArray.splice(sourceIndex, 1)
  targetArray.push(step)

  handleDragEnd()
}

function createTaskFromStep(step, index) {
  taskFromStep.value = {
    step: { ...step },
    index,
    initialData: {
      title: step.what,
      project_id: formData.value.project_id
    }
  }
  showCreateTaskModal.value = true
}

function closeTaskModal() {
  showCreateTaskModal.value = false
  taskFromStep.value = null
}

function handleTaskCreated(newTodo) {
  if (!taskFromStep.value) return
  const { index } = taskFromStep.value
  const next = [...formData.value.next_steps]
  if (next[index]) {
    next[index] = { ...next[index], todo_id: newTodo.id }
    formData.value.next_steps = next
  }
  saveNow()
  closeTaskModal()
}

watch(
  formData,
  () => {
    if (!initialLoadDone.value || !meeting.value) return
    debouncedSave()
  },
  { deep: true }
)

watch(
  () => formData.value.project_id,
  () => {
    loadProjectTodos()
  }
)

watch(meetingId, (newId, oldId) => {
  if (newId && newId !== oldId) {
    initialLoadDone.value = false
    loadMeeting()
  }
})

onMounted(() => {
  loadMeeting()
})

function formatTime(date) {
  if (!date) return ''
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}
</script>

<style scoped>
.meeting-edit-view {
  min-height: calc(100vh - 52px);
  background: #f9fafb;
  padding: 2rem;
  width: 100%;
}

:global(.dark) .meeting-edit-view {
  background: #0f172a;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  color: #6b7280;
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  transition: color 0.15s;
}

.back-link:hover {
  color: #2563eb;
}

:global(.dark) .back-link {
  color: #94a3b8;
}

:global(.dark) .back-link:hover {
  color: #60a5fa;
}

.view-header h2 {
  margin: 0;
  font-size: 1.875rem;
  font-weight: 700;
  color: #111827;
}

:global(.dark) .view-header h2 {
  color: #f1f5f9;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.save-status {
  font-size: 0.875rem;
  color: #6b7280;
}

.save-status.saved {
  color: #059669;
}

:global(.dark) .save-status.saved {
  color: #34d399;
}

.save-status.error {
  color: #dc2626;
}

:global(.dark) .save-status.error {
  color: #f87171;
}

.preview-toggle-wrap {
  display: flex;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  overflow: hidden;
  background: white;
}

:global(.dark) .preview-toggle-wrap {
  border-color: #334155;
  background: #1e293b;
}

.preview-toggle-wrap .toggle-btn {
  padding: 0.5rem 0.75rem;
  border: none;
  background: transparent;
  color: #6b7280;
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.preview-toggle-wrap .toggle-btn:hover {
  background: #f3f4f6;
  color: #374151;
}

:global(.dark) .preview-toggle-wrap .toggle-btn:hover {
  background: #334155;
  color: #f1f5f9;
}

.preview-toggle-wrap .toggle-btn.active {
  background: #e0e7ff;
  color: #3730a3;
}

:global(.dark) .preview-toggle-wrap .toggle-btn.active {
  background: #312e81;
  color: #a5b4fc;
}

.full-page-preview {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  max-width: 48rem;
}

.preview-section {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1rem 1.25rem;
}

:global(.dark) .preview-section {
  background: #1e293b;
  border-color: #334155;
}

.preview-section-title {
  margin: 0 0 0.5rem 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
}

:global(.dark) .preview-section-title {
  color: #94a3b8;
}

.preview-name {
  margin: 0;
  font-size: 1.125rem;
  color: #111827;
}

:global(.dark) .preview-name {
  color: #f1f5f9;
}

.full-page-preview .markdown-preview.form-preview {
  padding: 0;
  min-height: 0;
  max-height: none;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  gap: 1rem;
}

.meeting-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  max-width: 56rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.form-group label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

:global(.dark) .form-group label {
  color: #94a3b8;
}

.read-only-value {
  margin: 0;
  padding: 0.5rem 0;
  font-size: 1rem;
  color: #6b7280;
  font-family: ui-monospace, monospace;
}

.form-group input,
.form-group select {
  padding: 0.625rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.9375rem;
  transition: border-color 0.15s, box-shadow 0.15s;
}

:global(.dark) .form-group input,
:global(.dark) .form-group select {
  background: #1e293b;
  border-color: #334155;
  color: #f1f5f9;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-hint {
  font-size: 0.75rem;
  color: #6b7280;
}

.markdown-editor-container {
  border: 1px solid #d1d5db;
  border-radius: 8px;
  overflow: hidden;
}

:global(.dark) .markdown-editor-container {
  border-color: #334155;
}

.editor-tabs {
  display: flex;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

:global(.dark) .editor-tabs {
  background: #0f172a;
  border-bottom-color: #334155;
}

.tab-btn {
  padding: 0.5rem 0.875rem;
  border: none;
  background: transparent;
  color: #6b7280;
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  border-bottom: 2px solid transparent;
}

.tab-btn.active {
  color: #2563eb;
  border-bottom-color: #2563eb;
  background: white;
}

:global(.dark) .tab-btn.active {
  background: #1e293b;
  color: #60a5fa;
}

.insert-image-btn {
  margin-left: auto;
}

.hidden-file-input {
  position: absolute;
  width: 0;
  height: 0;
  opacity: 0;
  pointer-events: none;
}

.markdown-textarea {
  width: 100%;
  padding: 0.75rem;
  border: none;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.8125rem;
  line-height: 1.6;
  resize: vertical;
  min-height: 200px;
  background: white;
}

:global(.dark) .markdown-textarea {
  background: #1e293b;
  color: #f1f5f9;
}

.markdown-preview.form-preview {
  padding: 0.75rem;
  min-height: 100px;
  max-height: 500px;
  overflow-y: auto;
  background: white;
  line-height: 1.6;
  font-size: 0.875rem;
  color: #374151;
}

:global(.dark) .markdown-preview.form-preview {
  background: #1e293b;
  color: #e2e8f0;
}

.markdown-preview.form-preview :deep(h1) {
  font-size: 1.25rem;
  margin: 0 0 0.5rem 0;
}

.markdown-preview.form-preview :deep(h2) {
  font-size: 1.125rem;
  margin: 0.75rem 0 0.375rem 0;
}

.markdown-preview.form-preview :deep(h3) {
  font-size: 1rem;
  margin: 0.5rem 0 0.25rem 0;
}

.markdown-preview.form-preview :deep(p) {
  margin: 0 0 0.5rem 0;
}

.markdown-preview.form-preview :deep(ul) {
  list-style-type: disc;
  list-style-position: outside;
  padding-left: 1.25rem;
  margin: 0 0 0.5rem 0;
}

.markdown-preview.form-preview :deep(ol) {
  list-style-type: decimal;
  list-style-position: outside;
  padding-left: 1.25rem;
  margin: 0 0 0.5rem 0;
}

.markdown-preview.form-preview :deep(li) {
  display: list-item;
}

.markdown-preview.form-preview :deep(strong) {
  font-weight: 600;
}

.markdown-preview.form-preview :deep(code) {
  background: #f3f4f6;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  font-family: ui-monospace, monospace;
  font-size: 0.875em;
}

:global(.dark) .markdown-preview.form-preview :deep(code) {
  background: #334155;
}

.markdown-preview.form-preview :deep(pre) {
  background: #1f2937;
  color: #f9fafb;
  padding: 0.75rem;
  border-radius: 8px;
  overflow-x: auto;
  margin: 0.5rem 0;
}

.markdown-preview.form-preview :deep(pre code) {
  background: none;
  padding: 0;
  color: inherit;
}

.markdown-preview.form-preview :deep(blockquote) {
  border-left: 4px solid #2563eb;
  padding-left: 1rem;
  margin: 0.5rem 0;
  color: #4b5563;
}

:global(.dark) .markdown-preview.form-preview :deep(blockquote) {
  color: #94a3b8;
}

.markdown-preview.form-preview :deep(a) {
  color: #2563eb;
  text-decoration: underline;
  cursor: pointer;
}

.markdown-preview.form-preview :deep(a:hover) {
  color: #1d4ed8;
}

:global(.dark) .markdown-preview.form-preview :deep(a) {
  color: #60a5fa;
}

:global(.dark) .markdown-preview.form-preview :deep(a:hover) {
  color: #93c5fd;
}

.markdown-preview.form-preview :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
}

.btn-primary {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  background-color: #2563eb;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #1d4ed8;
}

.btn-primary:disabled {
  background-color: #93c5fd;
  cursor: not-allowed;
}

/* Steps view (preview), aligned with ProjectDetail */
.steps-list-view {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.step-view-item {
  display: flex;
  gap: 0.75rem;
  padding: 0.875rem;
  background: #f9fafb;
  border-radius: 8px;
  border-left: 3px solid #3b82f6;
}

:global(.dark) .step-view-item {
  background: #0f172a;
  border-left-color: #60a5fa;
}

.step-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.75rem;
  height: 1.75rem;
  background: #3b82f6;
  color: white;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  flex-shrink: 0;
}

.step-content {
  flex: 1;
}

.step-what {
  font-size: 0.9375rem;
  color: #111827;
  line-height: 1.5;
}

:global(.dark) .step-what {
  color: #f1f5f9;
}

.step-who {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  margin-top: 0.375rem;
  font-size: 0.8125rem;
  color: #6b7280;
}

:global(.dark) .step-who {
  color: #94a3b8;
}

.step-who svg {
  opacity: 0.7;
}

.step-task-link {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  margin-top: 0.5rem;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  color: #2563eb;
  background: #eff6ff;
  border-radius: 4px;
  text-decoration: none;
  transition: all 0.15s;
}

.step-task-link:hover {
  background: #dbeafe;
  color: #1d4ed8;
}

:global(.dark) .step-task-link {
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
}

:global(.dark) .step-task-link:hover {
  background: rgba(59, 130, 246, 0.25);
  color: #93c5fd;
}

.step-create-task-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  margin-top: 0.5rem;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  color: #16a34a;
  background: #f0fdf4;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s;
}

.step-create-task-btn:hover {
  background: #dcfce7;
  color: #15803d;
}

:global(.dark) .step-create-task-btn {
  background: rgba(22, 163, 74, 0.15);
  color: #4ade80;
}

:global(.dark) .step-create-task-btn:hover {
  background: rgba(22, 163, 74, 0.25);
  color: #86efac;
}

.step-task-link svg,
.step-create-task-btn svg {
  flex-shrink: 0;
}

/* Steps editor */
.steps-editor-section {
  margin-top: 0.5rem;
}

.steps-header {
  margin-bottom: 1rem;
}

.steps-header h4 {
  margin: 0 0 0.25rem 0;
  font-size: 0.9375rem;
  font-weight: 600;
  color: #374151;
}

:global(.dark) .steps-header h4 {
  color: #f1f5f9;
}

.steps-hint {
  margin: 0;
  font-size: 0.75rem;
  color: #6b7280;
}

.steps-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.steps-column {
  display: flex;
  flex-direction: column;
}

.steps-column-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 0.75rem;
  font-size: 0.8125rem;
  font-weight: 600;
  border-radius: 8px 8px 0 0;
  color: white;
}

.steps-column-header.past {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
}

.steps-column-header.next {
  background: linear-gradient(135deg, #10b981, #059669);
}

.step-count {
  margin-left: auto;
  padding: 0.125rem 0.5rem;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 9999px;
  font-size: 0.6875rem;
}

.steps-drop-zone {
  flex: 1;
  min-height: 150px;
  padding: 0.75rem;
  background: #f9fafb;
  border: 2px dashed #e5e7eb;
  border-top: none;
  border-radius: 0 0 8px 8px;
  transition: all 0.2s;
}

:global(.dark) .steps-drop-zone {
  background: #1e293b;
  border-color: #334155;
}

.steps-drop-zone.drag-over {
  background: #eff6ff;
  border-color: #3b82f6;
  border-style: solid;
}

:global(.dark) .steps-drop-zone.drag-over {
  background: rgba(59, 130, 246, 0.1);
  border-color: #3b82f6;
}

.empty-drop-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 120px;
  color: #9ca3af;
  font-size: 0.8125rem;
  text-align: center;
}

.drop-hint {
  font-size: 0.6875rem;
  margin-top: 0.25rem;
  opacity: 0.7;
}

.step-item {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 0.625rem;
  margin-bottom: 0.5rem;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  transition: all 0.2s;
  cursor: grab;
}

:global(.dark) .step-item {
  background: #0f172a;
  border-color: #334155;
}

.step-item:hover {
  border-color: #d1d5db;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

:global(.dark) .step-item:hover {
  border-color: #475569;
}

.step-item.dragging {
  opacity: 0.5;
  transform: scale(0.98);
}

.step-drag-handle {
  padding: 0.25rem;
  color: #9ca3af;
  cursor: grab;
  flex-shrink: 0;
}

.step-drag-handle:active {
  cursor: grabbing;
}

.step-fields {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.step-what-input,
.step-who-input {
  width: 100%;
  padding: 0.375rem 0.5rem;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  font-size: 0.8125rem;
  transition: border-color 0.15s;
}

:global(.dark) .step-what-input,
:global(.dark) .step-who-input {
  background: #1e293b;
  border-color: #334155;
  color: #f1f5f9;
}

.step-what-input {
  font-weight: 500;
}

.step-who-input {
  font-size: 0.75rem;
  color: #6b7280;
}

:global(.dark) .step-who-input {
  color: #94a3b8;
}

.step-what-input:focus,
.step-who-input:focus {
  outline: none;
  border-color: #3b82f6;
}

.step-what-input::placeholder,
.step-who-input::placeholder {
  color: #9ca3af;
}

.step-task-selector {
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid #e5e7eb;
}

:global(.dark) .step-task-selector {
  border-top-color: #334155;
}

.step-task-selector label {
  display: block;
  font-size: 0.75rem;
  color: #6b7280;
  margin-bottom: 0.25rem;
  font-weight: 500;
}

:global(.dark) .step-task-selector label {
  color: #94a3b8;
}

.step-task-selector select {
  width: 100%;
  padding: 0.375rem 0.5rem;
  font-size: 0.875rem;
  color: #374151;
  background: #ffffff;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s;
}

:global(.dark) .step-task-selector select {
  background: #0f172a;
  color: #f1f5f9;
  border-color: #334155;
}

.step-task-selector select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.step-remove-btn {
  padding: 0.25rem;
  border: none;
  background: transparent;
  color: #9ca3af;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s;
  flex-shrink: 0;
}

.step-remove-btn:hover {
  background: #fee2e2;
  color: #dc2626;
}

:global(.dark) .step-remove-btn:hover {
  background: rgba(220, 38, 38, 0.2);
}

.add-step-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.375rem;
  width: 100%;
  padding: 0.5rem;
  margin-top: 0.5rem;
  border: 1px dashed #d1d5db;
  border-radius: 6px;
  background: transparent;
  color: #6b7280;
  font-size: 0.8125rem;
  cursor: pointer;
  transition: all 0.15s;
}

:global(.dark) .add-step-btn {
  border-color: #475569;
  color: #94a3b8;
}

.add-step-btn:hover {
  background: #f3f4f6;
  border-color: #9ca3af;
  color: #374151;
}

:global(.dark) .add-step-btn:hover {
  background: #334155;
  border-color: #64748b;
  color: #f1f5f9;
}

@media (max-width: 768px) {
  .meeting-edit-view {
    padding: 1rem;
  }
  .form-row {
    grid-template-columns: 1fr;
  }
  .steps-columns {
    grid-template-columns: 1fr;
  }
}
</style>
