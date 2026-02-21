<template>
  <div class="weekly-todo-view">
    <div class="view-header">
      <div>
        <h2>Weekly Todo</h2>
        <p class="view-description">
          Define weekly todos and allocate time per day (Monday–Sunday)
        </p>
      </div>
      <div class="header-actions">
        <button class="btn-primary" @click="openCreateModal">Create todo</button>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <p>Loading...</p>
    </div>
    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button class="btn-primary" @click="loadAll">Retry</button>
    </div>
    <template v-else>
      <!-- Table of weekly todos -->
      <div class="table-section">
        <div class="section-header">
          <h3>Weekly todos</h3>
        </div>
        <div v-if="weeklyTodos.length === 0" class="empty-state">
          <p>No weekly todos yet. Create one to get started.</p>
        </div>
        <div v-else class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Title</th>
                <th>Description</th>
                <th>Linked task</th>
                <th class="col-actions">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in weeklyTodos"
                :key="item.id"
                draggable="true"
                class="draggable-row"
                @dragstart="onDragStart($event, item)"
              >
                <td class="col-title">{{ item.title }}</td>
                <td class="col-desc">{{ truncate(item.description, 60) }}</td>
                <td>{{ item.todo_id ? `Todo #${item.todo_id}` : '–' }}</td>
                <td class="col-actions">
                  <button type="button" class="btn-sm" @click="openEditModal(item)">Edit</button>
                  <button type="button" class="btn-sm danger" @click="handleDelete(item)">Delete</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Week calendar -->
      <div class="calendar-section">
        <div class="section-header week-nav">
          <button type="button" class="btn-nav" @click="prevWeek">&larr; Previous</button>
          <h3 class="week-label">{{ weekLabel }}</h3>
          <button type="button" class="btn-nav" @click="nextWeek">Next &rarr;</button>
        </div>
        <div class="week-grid">
          <div
            v-for="day in dayColumns"
            :key="day.key"
            class="day-column"
            :class="{ 'drop-target': dragOverDay === day.key }"
            @dragover.prevent="onDragOver(day.key)"
            @dragleave="onDragLeave"
            @drop.prevent="onDrop(day.key, $event)"
          >
            <div class="day-header">{{ day.label }}</div>
            <div class="day-content">
              <div
                v-for="entry in getEntriesForDay(day.key)"
                :key="entry.id"
                class="allocation-entry"
                @dblclick="editTodoFromEntry(entry)"
              >
                <span class="entry-title">{{ entry.title }}</span>
                <span class="entry-mins">{{ entry.minutes }} min</span>
              </div>
              <div v-if="getEntriesForDay(day.key).length === 0" class="day-empty">
                No time allocated
              </div>
              <button
                type="button"
                class="btn-add-time"
                @click="openAddTime(day.key)"
              >
                Add time
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Create / Edit modal -->
    <Modal
      :show="showFormModal"
      :title="editingId ? 'Edit weekly todo' : 'Create weekly todo'"
      @close="closeFormModal"
    >
      <form @submit.prevent="submitForm" class="weekly-form">
        <div class="form-group">
          <label for="wt-title">Title</label>
          <input id="wt-title" v-model="form.title" type="text" required placeholder="Title" class="form-input" />
        </div>
        <div class="form-group">
          <label for="wt-desc">Description</label>
          <textarea id="wt-desc" v-model="form.description" rows="2" placeholder="Optional" class="form-input"></textarea>
        </div>
        <div class="form-group">
          <label for="wt-todo">Link to task</label>
          <select id="wt-todo" v-model="form.todo_id" class="form-input">
            <option :value="null">None</option>
            <option v-for="t in todosForLink" :key="t.id" :value="t.id">{{ t.title }}</option>
          </select>
        </div>
        <div class="form-actions">
          <button type="button" class="btn-secondary" @click="closeFormModal">Cancel</button>
          <button type="submit" class="btn-primary" :disabled="isTitleEmpty">{{ editingId ? 'Update' : 'Create' }}</button>
        </div>
      </form>
    </Modal>

    <!-- Add time to day modal -->
    <Modal
      :show="showAddTimeModal"
      title="Add time to day"
      @close="showAddTimeModal = false"
    >
      <form v-if="addTimeDay" @submit.prevent="submitAddTime" class="weekly-form">
        <div class="form-group">
          <label>Weekly todo</label>
          <select v-model="addTimeTodoId" required class="form-input">
            <option value="">Select...</option>
            <option v-for="w in weeklyTodos" :key="w.id" :value="w.id">{{ w.title }}</option>
          </select>
        </div>
        <div class="form-group">
          <label>Minutes</label>
          <input v-model.number="addTimeMinutes" type="number" min="0" step="15" class="form-input" required />
        </div>
        <div class="form-actions">
          <button type="button" class="btn-secondary" @click="showAddTimeModal = false">Cancel</button>
          <button type="submit" class="btn-primary">Save</button>
        </div>
      </form>
    </Modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { weeklyTodosApi } from '@/services/api'
import { todosApi } from '@/services/api'
import Modal from '@/components/common/Modal.vue'

const weeklyTodos = ref([])
const allocations = ref([])
const loading = ref(true)
const error = ref(null)
const weekKey = ref(getWeekKey(new Date()))

const showFormModal = ref(false)
const editingId = ref(null)
const form = ref({ title: '', description: '', todo_id: null })

const isTitleEmpty = computed(() => {
  return !form.value.title || form.value.title.trim().length === 0
})

const todosForLink = ref([])
const showAddTimeModal = ref(false)
const addTimeDay = ref(null)
const addTimeTodoId = ref(null)
const addTimeMinutes = ref(30)

const dragOverDay = ref(null)
const DEFAULT_DROP_MINUTES = 60

const DAY_KEYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
const DAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

function getWeekKey(date) {
  const d = new Date(date)
  d.setHours(0, 0, 0, 0)
  const day = d.getDay()
  const diff = d.getDate() - (day === 0 ? 6 : day - 1)
  const monday = new Date(d)
  monday.setDate(diff)
  const y = monday.getFullYear()
  const m = String(monday.getMonth() + 1).padStart(2, '0')
  const dayNum = String(monday.getDate()).padStart(2, '0')
  return `${y}-${m}-${dayNum}`
}

function getMondayOfWeek(key) {
  const [y, m, day] = key.split('-').map(Number)
  return new Date(y, m - 1, day)
}

const weekLabel = computed(() => {
  const monday = getMondayOfWeek(weekKey.value)
  const sun = new Date(monday)
  sun.setDate(monday.getDate() + 6)
  const fmt = (d) => d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
  return `${fmt(monday)} – ${fmt(sun)}`
})

const dayColumns = computed(() => {
  const monday = getMondayOfWeek(weekKey.value)
  return DAY_KEYS.map((key, i) => {
    const d = new Date(monday)
    d.setDate(monday.getDate() + i)
    const label = `${DAY_LABELS[i]} ${d.getDate()}`
    return { key, label }
  })
})

const todoById = computed(() => {
  const map = {}
  weeklyTodos.value.forEach((w) => { map[w.id] = w })
  return map
})

function getEntriesForDay(dayKey) {
  const out = []
  allocations.value.forEach((a) => {
    const minutes = a[dayKey] || 0
    if (minutes > 0) {
      const wt = todoById.value[a.weekly_todo_id]
      out.push({
        id: `${a.weekly_todo_id}-${dayKey}`,
        weekly_todo_id: a.weekly_todo_id,
        title: wt ? wt.title : `#${a.weekly_todo_id}`,
        minutes
      })
    }
  })
  return out
}

function editTodoFromEntry(entry) {
  const item = todoById.value[entry.weekly_todo_id]
  if (item) openEditModal(item)
}

function truncate(str, maxLen) {
  if (!str) return '–'
  return str.length <= maxLen ? str : str.slice(0, maxLen) + '…'
}

async function loadAll() {
  loading.value = true
  error.value = null
  try {
    const [listRes, allocRes] = await Promise.all([
      weeklyTodosApi.list({ limit: 500 }),
      weeklyTodosApi.getAllocations(weekKey.value)
    ])
    weeklyTodos.value = listRes.data.weekly_todos || []
    allocations.value = allocRes.data.allocations || []
  } catch (e) {
    error.value = e.response?.data?.detail || e.message || 'Failed to load'
  } finally {
    loading.value = false
  }
}

async function loadTodosForLink() {
  try {
    const res = await todosApi.list({ status: 'Open,Started', limit: 200 })
    todosForLink.value = res.data.todos || []
  } catch (_) {
    todosForLink.value = []
  }
}

onMounted(() => { loadAll(); loadTodosForLink() })
watch(weekKey, () => { loadAll() })

function prevWeek() {
  const monday = getMondayOfWeek(weekKey.value)
  const prev = new Date(monday)
  prev.setDate(prev.getDate() - 7)
  weekKey.value = getWeekKey(prev)
}

function nextWeek() {
  const monday = getMondayOfWeek(weekKey.value)
  const next = new Date(monday)
  next.setDate(next.getDate() + 7)
  weekKey.value = getWeekKey(next)
}

function openCreateModal() {
  editingId.value = null
  form.value = { title: '', description: '', todo_id: null }
  showFormModal.value = true
}

function openEditModal(item) {
  editingId.value = item.id
  form.value = {
    title: item.title,
    description: item.description || '',
    todo_id: item.todo_id ?? null
  }
  showFormModal.value = true
}

function closeFormModal() {
  showFormModal.value = false
  editingId.value = null
}

async function submitForm() {
  try {
    if (editingId.value) {
      await weeklyTodosApi.update(editingId.value, form.value)
    } else {
      await weeklyTodosApi.create(form.value)
    }
    closeFormModal()
    await loadAll()
  } catch (e) {
    error.value = e.response?.data?.detail || e.message || 'Failed to save'
  }
}

async function handleDelete(item) {
  if (!confirm(`Delete "${item.title}"?`)) return
  try {
    await weeklyTodosApi.delete(item.id)
    await loadAll()
  } catch (e) {
    error.value = e.response?.data?.detail || e.message || 'Failed to delete'
  }
}

function openAddTime(dayKey) {
  addTimeDay.value = dayKey
  addTimeTodoId.value = weeklyTodos.value.length ? weeklyTodos.value[0].id : null
  addTimeMinutes.value = 30
  showAddTimeModal.value = true
}

async function submitAddTime() {
  if (!addTimeDay.value || !addTimeTodoId.value) return
  try {
    await setAllocationForDay(addTimeTodoId.value, addTimeDay.value, addTimeMinutes.value)
    showAddTimeModal.value = false
    await loadAll()
  } catch (e) {
    error.value = e.response?.data?.detail || e.message || 'Failed to save allocation'
  }
}

async function setAllocationForDay(weeklyTodoId, dayKey, minutesToAdd) {
  const existing = allocations.value.find((a) => a.weekly_todo_id === weeklyTodoId)
  const payload = existing
    ? {
        mon: existing.mon ?? 0,
        tue: existing.tue ?? 0,
        wed: existing.wed ?? 0,
        thu: existing.thu ?? 0,
        fri: existing.fri ?? 0,
        sat: existing.sat ?? 0,
        sun: existing.sun ?? 0
      }
    : { mon: 0, tue: 0, wed: 0, thu: 0, fri: 0, sat: 0, sun: 0 }
  payload[dayKey] = (payload[dayKey] || 0) + minutesToAdd
  await weeklyTodosApi.setAllocation(weeklyTodoId, weekKey.value, payload)
}

function onDragStart(e, item) {
  e.dataTransfer.effectAllowed = 'copy'
  e.dataTransfer.setData('application/json', JSON.stringify({ weekly_todo_id: item.id }))
  e.dataTransfer.setData('text/plain', item.title)
}

function onDragOver(dayKey) {
  dragOverDay.value = dayKey
}

function onDragLeave() {
  dragOverDay.value = null
}

async function onDrop(dayKey, e) {
  dragOverDay.value = null
  try {
    const raw = e.dataTransfer.getData('application/json')
    const data = raw ? JSON.parse(raw) : null
    const weeklyTodoId = data?.weekly_todo_id
    if (!weeklyTodoId) return
    await setAllocationForDay(weeklyTodoId, dayKey, DEFAULT_DROP_MINUTES)
    await loadAll()
  } catch (e) {
    error.value = e.response?.data?.detail || e.message || 'Failed to add time'
  }
}
</script>

<style scoped>
.weekly-todo-view {
  min-height: calc(100vh - 52px);
  background: #f9fafb;
  padding: 0 2rem 2rem;
}

:global(.dark) .weekly-todo-view {
  background: #0f172a;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 2rem 0 1rem;
  gap: 1rem;
  flex-wrap: wrap;
}

.view-header h2 {
  margin: 0 0 0.25rem 0;
  font-size: 1.875rem;
  font-weight: 700;
  color: #111827;
}

:global(.dark) .view-header h2 {
  color: #f1f5f9;
}

.view-description {
  margin: 0;
  color: #6b7280;
  font-size: 1rem;
}

:global(.dark) .view-description {
  color: #94a3b8;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.btn-primary {
  padding: 0.625rem 1rem;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
}

.btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
}

.btn-primary:disabled {
  background: #9ca3af;
  cursor: not-allowed;
  opacity: 0.6;
}

.btn-secondary {
  padding: 0.5rem 1rem;
  background: #e2e8f0;
  color: #334155;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  cursor: pointer;
}

.btn-secondary:hover {
  background: #cbd5e1;
}

:global(.dark) .btn-secondary {
  background: #475569;
  color: #e2e8f0;
}

.table-section {
  margin-bottom: 2rem;
}

.section-header {
  margin-bottom: 1rem;
}

.section-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #111827;
}

:global(.dark) .section-header h3 {
  color: #f1f5f9;
}

.week-nav {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1.5rem;
}

.week-label {
  min-width: 220px;
  text-align: center;
}

.btn-nav {
  padding: 0.5rem 1rem;
  background: #e2e8f0;
  color: #334155;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  cursor: pointer;
}

.btn-nav:hover {
  background: #cbd5e1;
}

:global(.dark) .btn-nav {
  background: #475569;
  color: #e2e8f0;
}

.table-wrapper {
  overflow-x: auto;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #fff;
}

:global(.dark) .table-wrapper {
  border-color: #334155;
  background: #1e293b;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.data-table th {
  text-align: left;
  padding: 0.75rem 1rem;
  font-weight: 600;
  color: #475569;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}

:global(.dark) .data-table th {
  color: #94a3b8;
  background: #0f172a;
  border-bottom-color: #334155;
}

.data-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #e2e8f0;
  color: #334155;
}

:global(.dark) .data-table td {
  border-bottom-color: #334155;
  color: #e2e8f0;
}

.data-table tr:hover {
  background: #f1f5f9;
}

:global(.dark) .data-table tr:hover {
  background: #334155;
}

.draggable-row {
  cursor: grab;
}

.draggable-row:active {
  cursor: grabbing;
}

.col-title {
  font-weight: 500;
}

.col-desc {
  color: #64748b;
  max-width: 280px;
}

:global(.dark) .col-desc {
  color: #94a3b8;
}

.col-actions {
  white-space: nowrap;
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  margin-right: 0.5rem;
  font-size: 0.8125rem;
  border-radius: 6px;
  border: 1px solid #cbd5e1;
  background: #fff;
  color: #334155;
  cursor: pointer;
}

.btn-sm:hover {
  background: #f1f5f9;
}

.btn-sm.danger {
  border-color: #fca5a5;
  color: #b91c1c;
}

.btn-sm.danger:hover {
  background: #fef2f2;
}

.loading-state,
.error-state,
.empty-state {
  padding: 2rem;
  text-align: center;
  color: #6b7280;
}

:global(.dark) .loading-state,
:global(.dark) .error-state,
:global(.dark) .empty-state {
  color: #94a3b8;
}

.calendar-section {
  margin-top: 1.5rem;
}

.week-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 0.75rem;
}

.day-column {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #fff;
  min-height: 200px;
  transition: background 0.15s, border-color 0.15s;
}

.day-column.drop-target {
  background: #eff6ff;
  border-color: #3b82f6;
}

:global(.dark) .day-column {
  border-color: #334155;
  background: #1e293b;
}

:global(.dark) .day-column.drop-target {
  background: #1e3a5f;
  border-color: #60a5fa;
}

.day-header {
  padding: 0.5rem 0.75rem;
  font-weight: 600;
  font-size: 0.8125rem;
  color: #475569;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  border-radius: 8px 8px 0 0;
}

:global(.dark) .day-header {
  color: #94a3b8;
  background: #0f172a;
  border-bottom-color: #334155;
}

.day-content {
  padding: 0.5rem 0.75rem;
}

.allocation-entry {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.35rem 0;
  font-size: 0.8125rem;
  border-bottom: 1px solid #f1f5f9;
  cursor: pointer;
}

.allocation-entry:hover {
  background: #f8fafc;
}

:global(.dark) .allocation-entry:hover {
  background: #334155;
}

:global(.dark) .allocation-entry {
  border-bottom-color: #334155;
}

.entry-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 80%;
}

.entry-mins {
  color: #64748b;
  flex-shrink: 0;
}

.day-empty {
  font-size: 0.8125rem;
  color: #94a3b8;
  padding: 0.5rem 0;
}

.btn-add-time {
  margin-top: 0.5rem;
  padding: 0.35rem 0.5rem;
  font-size: 0.75rem;
  background: #f1f5f9;
  color: #475569;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  width: 100%;
}

.btn-add-time:hover {
  background: #e2e8f0;
}

:global(.dark) .btn-add-time {
  background: #334155;
  color: #94a3b8;
}

.weekly-form .form-group {
  margin-bottom: 1rem;
}

.weekly-form label {
  display: block;
  margin-bottom: 0.35rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

:global(.dark) .weekly-form label {
  color: #e2e8f0;
}

.weekly-form .form-input {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.875rem;
  background: #fff;
  color: #111827;
}

:global(.dark) .weekly-form .form-input {
  background: #1e293b;
  border-color: #475569;
  color: #f1f5f9;
}

.weekly-form .form-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  margin-top: 1.25rem;
}

@media (max-width: 900px) {
  .week-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .week-grid {
    grid-template-columns: 1fr;
  }
}
</style>
