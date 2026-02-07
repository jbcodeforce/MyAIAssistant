<template>
  <form @submit.prevent="handleSubmit" class="todo-form">
    <div class="form-group">
      <label for="title">Title</label>
      <input
        id="title"
        v-model="form.title"
        type="text"
        required
        placeholder="Enter todo title"
        class="form-input"
      />
    </div>

    <div class="form-group">
      <label for="description">Description</label>
      <RichTextEditor
        v-model="form.description"
        placeholder="Enter description (optional)"
      />
    </div>

    <div class="form-row">
      <div class="form-group">
        <label for="status">Status</label>
        <select id="status" v-model="form.status" class="form-input">
          <option value="Open">Open</option>
          <option value="Started">Started</option>
          <option value="Completed">Completed</option>
          <option value="Cancelled">Cancelled</option>
        </select>
      </div>

      <div class="form-group">
        <label for="category">Category</label>
        <input
          id="category"
          v-model="form.category"
          type="text"
          placeholder="e.g., Work, Personal"
          class="form-input"
        />
      </div>
    </div>

    <div class="form-row">
      <div class="form-group">
        <label for="urgency">Urgency</label>
        <select id="urgency" v-model="form.urgency" class="form-input">
          <option :value="null">Unclassified</option>
          <option value="Urgent">Urgent</option>
          <option value="Not Urgent">Not Urgent</option>
        </select>
      </div>

      <div class="form-group">
        <label for="importance">Importance</label>
        <select id="importance" v-model="form.importance" class="form-input">
          <option :value="null">Unclassified</option>
          <option value="Important">Important</option>
          <option value="Not Important">Not Important</option>
        </select>
      </div>
    </div>

    <div class="form-row">
      <div class="form-group">
        <label for="project">Project</label>
        <select id="project" v-model="form.project_id" class="form-input" :disabled="loadingProjects">
          <option :value="null">No project</option>
          <option v-for="project in projects" :key="project.id" :value="project.id">
            {{ project.name }}
          </option>
        </select>
      </div>

      <div class="form-group form-group-asset">
        <label for="asset_id">Asset</label>
        <select id="asset_id" v-model="form.asset_id" class="form-input" :disabled="loadingAssets">
          <option :value="null">No asset</option>
          <option v-for="asset in assets" :key="asset.id" :value="asset.id">
            {{ asset.name }}
          </option>
        </select>
      </div>
    </div>

    <div class="form-group">
      <label for="due_date">Due Date</label>
      <input
        id="due_date"
        v-model="form.due_date"
        type="datetime-local"
        class="form-input"
      />
    </div>

    <div class="form-actions">
      <button type="button" @click="$emit('cancel')" class="btn-secondary">
        Cancel
      </button>
      <button type="submit" class="btn-primary">
        {{ isEdit ? 'Update' : 'Create' }} Todo
      </button>
    </div>
  </form>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import RichTextEditor from '@/components/common/RichTextEditor.vue'
import { projectsApi, assetsApi } from '@/services/api'

const props = defineProps({
  initialData: {
    type: Object,
    default: null
  },
  isEdit: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['submit', 'cancel'])

const projects = ref([])
const loadingProjects = ref(false)
const assets = ref([])
const loadingAssets = ref(false)

const form = ref({
  title: '',
  description: '',
  status: 'Open',
  urgency: null,
  importance: null,
  category: '',
  project_id: null,
  asset_id: null,
  due_date: ''
})

onMounted(async () => {
  await Promise.all([loadProjects(), loadAssets()])
})

async function loadProjects() {
  loadingProjects.value = true
  try {
    const response = await projectsApi.list({ limit: 500 })
    projects.value = response.data.projects
  } catch (err) {
    console.error('Failed to load projects:', err)
  } finally {
    loadingProjects.value = false
  }
}

async function loadAssets() {
  loadingAssets.value = true
  try {
    const response = await assetsApi.list({ limit: 500 })
    assets.value = response.data.assets
  } catch (err) {
    console.error('Failed to load assets:', err)
  } finally {
    loadingAssets.value = false
  }
}

watch(
  () => props.initialData,
  (newData) => {
    if (newData) {
      form.value = {
        title: newData.title || '',
        description: newData.description || '',
        status: newData.status || 'Open',
        urgency: newData.urgency || null,
        importance: newData.importance || null,
        category: newData.category || '',
        project_id: newData.project_id || null,
        asset_id: newData.asset_id || null,
        due_date: newData.due_date ? formatDateTimeLocal(newData.due_date) : ''
      }
    }
  },
  { immediate: true }
)

function formatDateTimeLocal(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}`
}

function handleSubmit() {
  const submitData = {
    ...form.value,
    due_date: form.value.due_date || null,
    category: form.value.category || null,
    project_id: form.value.project_id || null,
    asset_id: form.value.asset_id || null
  }
  
  if (submitData.urgency === '') submitData.urgency = null
  if (submitData.importance === '') submitData.importance = null
  
  emit('submit', submitData)
}
</script>

<style scoped>
.todo-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

/* Asset select: prevent clipping; ensure full width within grid cell */
.form-group-asset {
  min-width: 0;
}

.form-group-asset .form-input {
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
}

label {
  font-weight: 600;
  color: #374151;
  font-size: 0.875rem;
}

.form-input {
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 1rem;
  transition: all 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

textarea.form-input {
  resize: vertical;
  font-family: inherit;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

.btn-primary,
.btn-secondary {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-primary {
  background-color: #2563eb;
  color: white;
}

.btn-primary:hover {
  background-color: #1d4ed8;
}

.btn-secondary {
  background-color: #f3f4f6;
  color: #374151;
}

.btn-secondary:hover {
  background-color: #e5e7eb;
}

@media (max-width: 640px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}

/* When modal is ~800px (wide), give Project/Asset row more room so Asset select is not clipped */
@media (max-width: 860px) {
  .form-row:has(.form-group-asset) {
    grid-template-columns: 1fr;
  }
}
</style>

