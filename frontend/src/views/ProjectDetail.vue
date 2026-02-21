<template>
  <div class="project-detail-view">
    <div class="view-header">
      <div class="header-left">
        <router-link to="/projects" class="back-link">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m15 18-6-6 6-6"/>
          </svg>
          Back to Projects
        </router-link>
        <h2 v-if="project">{{ project.name }}</h2>
        <h2 v-else-if="loading">Loading...</h2>
      </div>
      <div class="header-actions" v-if="project">
        <button class="btn-secondary" @click="editProject">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
            <path d="m15 5 4 4"/>
          </svg>
          Edit
        </button>
        <router-link 
          :to="`/projects/${project.id}/todos`" 
          class="btn-primary"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9 11l3 3L22 4"/>
            <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
          </svg>
          View Todos
        </router-link>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <p>Loading project...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button @click="loadProject" class="btn-primary">Retry</button>
    </div>

    <div v-else-if="project" class="project-content">
      <div class="project-meta">
        <span :class="['status-badge', statusClass(project.status)]">
          {{ project.status }}
        </span>
        <router-link 
          v-if="organizationName"
          :to="`/organizations/${project.organization_id}`"
          class="meta-link"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
            <circle cx="9" cy="7" r="4"/>
            <path d="M22 21v-2a4 4 0 0 0-3-3.87"/>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
          {{ organizationName }}
        </router-link>
        <div class="meta-item">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect width="18" height="18" x="3" y="4" rx="2" ry="2"/>
            <line x1="16" x2="16" y1="2" y2="6"/>
            <line x1="8" x2="8" y1="2" y2="6"/>
            <line x1="3" x2="21" y1="10" y2="10"/>
          </svg>
          Created {{ formatDate(project.created_at) }}
        </div>
        <div class="meta-item" v-if="project.updated_at !== project.created_at">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"/>
            <path d="M21 3v5h-5"/>
          </svg>
          Updated {{ formatDate(project.updated_at) }}
        </div>
      </div>

      <div class="sections-grid">
        <div class="section-card full-width" v-if="project.description">
          <div class="section-header">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
            <h3>Description</h3>
          </div>
          <div class="section-content markdown-preview" v-html="renderedDescription"></div>
        </div>

        <div class="section-card full-width" v-if="project.tasks">
          <div class="section-header">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9 11l3 3L22 4"/>
              <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
            </svg>
            <h3>Notes</h3>
          </div>
          <div class="section-content markdown-preview" v-html="renderedTasks"></div>
        </div>

        <div class="section-card" v-if="project.past_steps && project.past_steps.length > 0">
          <div class="section-header">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
              <path d="M3 3v5h5"/>
            </svg>
            <h3>Past Steps</h3>
          </div>
          <div class="section-content">
            <div class="steps-list-view">
              <div v-for="(step, index) in project.past_steps" :key="index" class="step-view-item">
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
                    v-if="step.todo_id"
                    :to="{ path: `/projects/${project.id}/todos`, query: { highlight: step.todo_id } }"
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

        <div class="section-card" v-if="project.next_steps && project.next_steps.length > 0">
          <div class="section-header">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M5 12h14"/>
              <path d="m12 5 7 7-7 7"/>
            </svg>
            <h3>Next Steps</h3>
          </div>
          <div class="section-content">
            <div class="steps-list-view">
              <div v-for="(step, index) in project.next_steps" :key="index" class="step-view-item">
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
                    v-if="!step.todo_id"
                    @click="createTaskFromStep(step, index, 'next')"
                    class="step-create-task-btn"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M12 5v14"/>
                      <path d="M5 12h14"/>
                    </svg>
                    Create Task
                  </button>
                  <router-link 
                    v-else
                    :to="{ path: `/projects/${project.id}/todos`, query: { highlight: step.todo_id } }"
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
      </div>

      <div class="empty-content" v-if="!hasContent">
        <p>No content has been added to this project yet.</p>
        <button class="btn-primary" @click="editProject">Add Content</button>
      </div>
    </div>

    <!-- Edit Modal -->
    <Modal 
      :show="showEditModal" 
      title="Edit Project" 
      size="fullscreen" 
      @close="closeEditModal"
    >
      <form @submit.prevent="handleSubmit" class="project-form">
        <div class="form-group">
          <label for="name">Project Name *</label>
          <input 
            id="name" 
            v-model="formData.name" 
            type="text" 
            required 
            placeholder="Enter project name"
          />
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="organization">Organization</label>
            <select id="organization" v-model="formData.organization_id">
              <option :value="null">No organization</option>
              <option v-for="o in organizations" :key="o.id" :value="o.id">{{ o.name }}</option>
            </select>
          </div>

          <div class="form-group">
            <label for="status">Status</label>
            <select id="status" v-model="formData.status">
              <option value="Draft">Draft</option>
              <option value="Active">Active</option>
              <option value="On Hold">On Hold</option>
              <option value="Completed">Completed</option>
              <option value="Cancelled">Cancelled</option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label>Description</label>
          <div class="markdown-editor-container">
            <div class="editor-tabs">
              <button 
                type="button" 
                :class="['tab-btn', { active: descriptionTab === 'write' }]"
                @click="descriptionTab = 'write'"
              >
                Write
              </button>
              <button 
                type="button" 
                :class="['tab-btn', { active: descriptionTab === 'preview' }]"
                @click="descriptionTab = 'preview'"
              >
                Preview
              </button>
            </div>
            <textarea 
              v-if="descriptionTab === 'write'"
              v-model="formData.description" 
              class="markdown-textarea"
              rows="6"
              placeholder="## Project Overview

Describe the project goals, scope, and key deliverables."
            ></textarea>
            <div v-else class="markdown-preview form-preview" v-html="formRenderedDescription"></div>
          </div>
        </div>

        <div class="form-group">
          <label>Tasks</label>
          <div class="markdown-editor-container">
            <div class="editor-tabs">
              <button 
                type="button" 
                :class="['tab-btn', { active: tasksTab === 'write' }]"
                @click="tasksTab = 'write'"
              >
                Write
              </button>
              <button 
                type="button" 
                :class="['tab-btn', { active: tasksTab === 'preview' }]"
                @click="tasksTab = 'preview'"
              >
                Preview
              </button>
            </div>
            <textarea 
              v-if="tasksTab === 'write'"
              v-model="formData.tasks" 
              class="markdown-textarea"
              rows="6"
              placeholder="## Current Tasks

- [ ] Task 1
- [ ] Task 2"
            ></textarea>
            <div v-else class="markdown-preview form-preview" v-html="formRenderedTasks"></div>
          </div>
        </div>

        <!-- Steps Editor with Drag and Drop -->
        <div class="steps-editor-section">
          <div class="steps-header">
            <h4>Project Steps</h4>
            <p class="steps-hint">Drag steps between lists to move them. Click the grip handle to drag.</p>
          </div>
          
          <div class="steps-columns">
            <!-- Past Steps -->
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
                    <input 
                      type="text" 
                      v-model="step.what" 
                      placeholder="What was done?"
                      class="step-what-input"
                    />
                    <input 
                      type="text" 
                      v-model="step.who" 
                      placeholder="By whom?"
                      class="step-who-input"
                    />
                    <div class="step-task-selector">
                      <label>Linked Task (optional):</label>
                      <select v-model="step.todo_id">
                        <option :value="null">No task linked</option>
                        <option 
                          v-for="todo in projectTodos" 
                          :key="todo.id" 
                          :value="todo.id"
                        >
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

            <!-- Next Steps -->
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
                    <input 
                      type="text" 
                      v-model="step.what" 
                      placeholder="What needs to be done?"
                      class="step-what-input"
                    />
                    <input 
                      type="text" 
                      v-model="step.who" 
                      placeholder="By whom?"
                      class="step-who-input"
                    />
                    <div class="step-task-selector">
                      <label>Linked Task (optional):</label>
                      <select v-model="step.todo_id">
                        <option :value="null">No task linked</option>
                        <option 
                          v-for="todo in projectTodos" 
                          :key="todo.id" 
                          :value="todo.id"
                        >
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

      <template #footer>
        <button type="button" class="btn-secondary" @click="closeEditModal">Cancel</button>
        <button type="button" class="btn-primary" @click="handleSubmit" :disabled="!isFormValid">
          Update
        </button>
      </template>
    </Modal>

    <!-- Create Task from Step Modal -->
    <Modal 
      :show="showCreateTaskModal" 
      title="Create Task from Step" 
      size="large"
      @close="closeTaskModal"
    >
      <TodoForm
        :initial-data="taskFromStep?.initialData"
        @submit="handleTaskCreated"
        @cancel="closeTaskModal"
      />
    </Modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { marked } from 'marked'
import { projectsApi, organizationsApi, todosApi } from '@/services/api'
import Modal from '@/components/common/Modal.vue'
import TodoForm from '@/components/todo/TodoForm.vue'

const route = useRoute()
const router = useRouter()

const project = ref(null)
const organizations = ref([])
const loading = ref(false)
const error = ref(null)

// Edit modal state
const showEditModal = ref(false)
const formData = ref({
  name: '',
  description: '',
  organization_id: null,
  status: 'Draft',
  tasks: '',
  past_steps: [],
  next_steps: []
})

// Editor tabs
const descriptionTab = ref('write')
const tasksTab = ref('write')

// Drag and drop state
const isDragging = ref(false)
const dragSource = ref({ list: null, index: null })
const dragOverZone = ref(null)

// Task creation from step
const showCreateTaskModal = ref(false)
const taskFromStep = ref(null)  // { step, index, type: 'next' }

// Project todos for linking in edit mode
const projectTodos = ref([])

// Computed for rendered markdown (view mode)
const renderedDescription = computed(() => marked(project.value?.description || ''))
const renderedTasks = computed(() => marked(project.value?.tasks || ''))

// Computed for form rendered markdown
const formRenderedDescription = computed(() => marked(formData.value.description || ''))
const formRenderedTasks = computed(() => marked(formData.value.tasks || ''))

const organizationName = computed(() => {
  if (!project.value?.organization_id) return null
  const org = organizations.value.find(o => o.id === project.value.organization_id)
  return org?.name || null
})

const hasContent = computed(() => {
  if (!project.value) return false
  return project.value.description || 
         project.value.tasks || 
         (project.value.past_steps && project.value.past_steps.length > 0) || 
         (project.value.next_steps && project.value.next_steps.length > 0)
})

const isFormValid = computed(() => {
  return formData.value.name && formData.value.name.trim().length > 0
})

onMounted(async () => {
  await Promise.all([loadProject(), loadOrganizations()])
})

async function loadProject() {
  const id = route.params.id
  if (!id) {
    error.value = 'Project ID not provided'
    return
  }

  loading.value = true
  error.value = null
  try {
    const response = await projectsApi.get(id)
    project.value = response.data
  } catch (err) {
    if (err.response?.status === 404) {
      error.value = 'Project not found'
    } else {
      error.value = err.response?.data?.detail || 'Failed to load project'
    }
    console.error('Failed to load project:', err)
  } finally {
    loading.value = false
  }
}

async function loadOrganizations() {
  try {
    const response = await organizationsApi.list({ limit: 500 })
    organizations.value = response.data.organizations
  } catch (err) {
    console.error('Failed to load organizations:', err)
  }
}

async function loadProjectTodos() {
  if (!project.value?.id) return
  try {
    const response = await projectsApi.getTodos(project.value.id, { limit: 500 })
    projectTodos.value = response.data.todos
  } catch (err) {
    console.error('Failed to load project todos:', err)
    projectTodos.value = []
  }
}

function editProject() {
  // Deep copy the steps arrays to avoid mutating the original
  const pastSteps = Array.isArray(project.value.past_steps) 
    ? project.value.past_steps.map(s => ({ what: s.what || '', who: s.who || '', todo_id: s.todo_id || null }))
    : []
  const nextSteps = Array.isArray(project.value.next_steps)
    ? project.value.next_steps.map(s => ({ what: s.what || '', who: s.who || '', todo_id: s.todo_id || null }))
    : []
  
  formData.value = {
    name: project.value.name,
    description: project.value.description || '',
    organization_id: project.value.organization_id || null,
    status: project.value.status,
    tasks: project.value.tasks || '',
    past_steps: pastSteps,
    next_steps: nextSteps
  }
  resetTabs()
  loadProjectTodos()
  showEditModal.value = true
}

function resetTabs() {
  descriptionTab.value = 'write'
  tasksTab.value = 'write'
  // Reset drag state
  isDragging.value = false
  dragSource.value = { list: null, index: null }
  dragOverZone.value = null
}

function closeEditModal() {
  showEditModal.value = false
}

// Task creation from step functions
function createTaskFromStep(step, index, type) {
  taskFromStep.value = { 
    step: { ...step }, 
    index, 
    type,
    initialData: {
      title: step.what,
      project_id: project.value.id
    }
  }
  showCreateTaskModal.value = true
}

function closeTaskModal() {
  showCreateTaskModal.value = false
  taskFromStep.value = null
}

async function handleTaskCreated(newTodo) {
  if (!taskFromStep.value) return
  
  const { index, type } = taskFromStep.value
  
  // Update the step in the project
  const steps = type === 'next' ? project.value.next_steps : project.value.past_steps
  steps[index].todo_id = newTodo.id
  
  // Update the project on the server
  try {
    await projectsApi.update(project.value.id, {
      next_steps: type === 'next' ? steps : project.value.next_steps,
      past_steps: type === 'past' ? steps : project.value.past_steps
    })
    
    // Refresh the project to show the updated data
    await loadProject()
  } catch (err) {
    console.error('Failed to link task to step:', err)
  }
  
  closeTaskModal()
}

// Step management functions
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

// Drag and drop handlers
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
  
  // Get the step from source list
  const sourceArray = sourceList === 'past' ? formData.value.past_steps : formData.value.next_steps
  const targetArray = targetList === 'past' ? formData.value.past_steps : formData.value.next_steps
  
  // Remove from source
  const [step] = sourceArray.splice(sourceIndex, 1)
  
  // Add to target
  targetArray.push(step)
  
  handleDragEnd()
}

async function handleSubmit() {
  if (!isFormValid.value) return
  
  try {
    const payload = { ...formData.value }
    if (payload.organization_id === null) {
      delete payload.organization_id
    }
    
    // Filter out empty steps (where 'what' is empty)
    payload.past_steps = payload.past_steps
      .filter(s => s.what && s.what.trim())
      .map(s => ({ what: s.what.trim(), who: (s.who || '').trim() }))
    
    payload.next_steps = payload.next_steps
      .filter(s => s.what && s.what.trim())
      .map(s => ({ what: s.what.trim(), who: (s.who || '').trim() }))
    
    // Send null if arrays are empty
    if (payload.past_steps.length === 0) payload.past_steps = null
    if (payload.next_steps.length === 0) payload.next_steps = null
    
    const response = await projectsApi.update(project.value.id, payload)
    project.value = response.data
    closeEditModal()
  } catch (err) {
    console.error('Failed to update project:', err)
    alert(err.response?.data?.detail || 'Failed to update project')
  }
}

function statusClass(status) {
  return status.toLowerCase().replace(' ', '-')
}

function formatDate(dateString) {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}
</script>

<style scoped>
.project-detail-view {
  min-height: calc(100vh - 52px);
  background: #f9fafb;
  padding: 2rem;
  width: 100%;
}

:global(.dark) .project-detail-view {
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

.project-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.875rem;
  color: #6b7280;
}

:global(.dark) .meta-item {
  color: #94a3b8;
}

.meta-item svg {
  color: #9ca3af;
}

.meta-link {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.875rem;
  color: #6b7280;
  text-decoration: none;
  transition: color 0.15s;
}

.meta-link:hover {
  color: #2563eb;
}

:global(.dark) .meta-link {
  color: #94a3b8;
}

:global(.dark) .meta-link:hover {
  color: #60a5fa;
}

.meta-link svg {
  color: #9ca3af;
}

.meta-link:hover svg {
  color: #2563eb;
}

:global(.dark) .meta-link:hover svg {
  color: #60a5fa;
}

/* Status badges */
.status-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.status-badge.completed {
  background: #dcfce7;
  color: #166534;
}

.status-badge.active {
  background: #dbeafe;
  color: #1e40af;
}

.status-badge.draft {
  background: #f3f4f6;
  color: #374151;
}

.status-badge.on-hold {
  background: #fef3c7;
  color: #92400e;
}

.status-badge.cancelled {
  background: #fee2e2;
  color: #991b1b;
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

.loading-state p,
.error-state p {
  font-size: 1.125rem;
  color: #6b7280;
}

.project-content {
  width: 100%;
}

.sections-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
}

.section-card {
  background: white;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

:global(.dark) .section-card {
  background: #1e293b;
  border-color: #334155;
}

.section-card.full-width {
  grid-column: 1 / -1;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem 1.25rem;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

:global(.dark) .section-header {
  background: #0f172a;
  border-bottom-color: #334155;
}

.section-header svg {
  color: #6366f1;
}

.section-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #111827;
}

:global(.dark) .section-header h3 {
  color: #f1f5f9;
}

.section-content {
  padding: 1.25rem;
}

.empty-content {
  text-align: center;
  padding: 3rem 2rem;
  background: white;
  border-radius: 12px;
  border: 2px dashed #e5e7eb;
}

:global(.dark) .empty-content {
  background: #1e293b;
  border-color: #334155;
}

.empty-content p {
  margin: 0 0 1rem 0;
  color: #6b7280;
}

/* Buttons */
.btn-primary,
.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  text-decoration: none;
}

.btn-primary {
  background-color: #2563eb;
  color: white;
}

.btn-primary:hover {
  background-color: #1d4ed8;
}

.btn-primary:disabled {
  background-color: #93c5fd;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: white;
  color: #374151;
  border: 1px solid #d1d5db;
}

:global(.dark) .btn-secondary {
  background-color: #1e293b;
  color: #f1f5f9;
  border-color: #334155;
}

.btn-secondary:hover {
  background-color: #f9fafb;
}

:global(.dark) .btn-secondary:hover {
  background-color: #334155;
}

/* Markdown Preview */
.markdown-preview {
  line-height: 1.6;
  font-size: 0.9375rem;
  color: #374151;
}

:global(.dark) .markdown-preview {
  color: #e2e8f0;
}

.markdown-preview :deep(h1) {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 0.75rem 0;
  padding-bottom: 0.375rem;
  border-bottom: 1px solid #e5e7eb;
}

:global(.dark) .markdown-preview :deep(h1) {
  border-bottom-color: #334155;
}

.markdown-preview :deep(h2) {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 1.25rem 0 0.625rem 0;
  color: #1e40af;
}

:global(.dark) .markdown-preview :deep(h2) {
  color: #60a5fa;
}

.markdown-preview :deep(h3) {
  font-size: 1.0625rem;
  font-weight: 600;
  margin: 1rem 0 0.5rem 0;
}

.markdown-preview :deep(p) {
  margin: 0 0 0.75rem 0;
}

.markdown-preview :deep(ul),
.markdown-preview :deep(ol) {
  padding-left: 1.5rem;
  margin: 0 0 1rem 0;
}

.markdown-preview :deep(li) {
  margin: 0.25rem 0;
}

.markdown-preview :deep(strong) {
  font-weight: 600;
}

.markdown-preview :deep(code) {
  background: #f3f4f6;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  font-family: ui-monospace, monospace;
  font-size: 0.875em;
}

:global(.dark) .markdown-preview :deep(code) {
  background: #334155;
}

.markdown-preview :deep(pre) {
  background: #1f2937;
  color: #f9fafb;
  padding: 1rem;
  border-radius: 8px;
  overflow-x: auto;
  margin: 1rem 0;
}

.markdown-preview :deep(pre code) {
  background: none;
  padding: 0;
  color: inherit;
}

.markdown-preview :deep(blockquote) {
  border-left: 4px solid #2563eb;
  padding-left: 1rem;
  margin: 1rem 0;
  color: #4b5563;
  font-style: italic;
}

:global(.dark) .markdown-preview :deep(blockquote) {
  color: #94a3b8;
}

.markdown-preview :deep(input[type="checkbox"]) {
  margin-right: 0.375rem;
}

/* Form styles */
.project-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
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

/* Markdown Editor */
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

.tab-btn:hover {
  color: #374151;
  background: rgba(0, 0, 0, 0.02);
}

:global(.dark) .tab-btn:hover {
  color: #f1f5f9;
  background: rgba(255, 255, 255, 0.02);
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

.markdown-textarea {
  width: 100%;
  padding: 0.75rem;
  border: none;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.8125rem;
  line-height: 1.6;
  resize: vertical;
  min-height: 100px;
  background: white;
}

:global(.dark) .markdown-textarea {
  background: #1e293b;
  color: #f1f5f9;
}

.markdown-textarea:focus {
  outline: none;
}

.markdown-textarea::placeholder {
  color: #9ca3af;
}

.markdown-preview.form-preview {
  padding: 0.75rem;
  min-height: 100px;
  max-height: 300px;
  overflow-y: auto;
  background: white;
}

:global(.dark) .markdown-preview.form-preview {
  background: #1e293b;
}

/* Steps View Styles */
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

/* Steps Editor Styles */
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
  .project-detail-view {
    padding: 1rem;
  }

  .view-header {
    flex-direction: column;
    gap: 1rem;
  }

  .header-actions {
    width: 100%;
  }

  .project-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .sections-grid {
    grid-template-columns: 1fr;
  }

  .section-card.full-width {
    grid-column: 1;
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .steps-columns {
    grid-template-columns: 1fr;
  }
}
</style>

