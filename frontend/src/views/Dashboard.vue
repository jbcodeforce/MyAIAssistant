<template>
  <div class="dashboard">
    <div v-if="loading" class="loading-state">
      <p>{{ loadingMessage }}</p>
    </div>

    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button @click="loadTodos" class="btn-primary">Retry</button>
    </div>

    <div v-else class="dashboard-content">
      <div class="dashboard-header">
        <div>
          <h2>Tasks Dashboard</h2>
          <p class="view-description">Organize tasks by urgency and importance</p>
        </div>
        <form class="dashboard-search" @submit.prevent="runSearch">
          <input
            v-model="searchTerm"
            type="text"
            class="search-input"
            placeholder="Search tasks by title or description"
            maxlength="200"
            aria-label="Search tasks"
          />
          <button type="submit" class="btn-search">Search</button>
          <button
            v-if="searchTerm.trim()"
            type="button"
            class="btn-search-clear"
            @click="clearSearch"
          >
            Clear
          </button>
        </form>
        <div class="dashboard-header-actions">
          <router-link to="/weekly-todo" class="btn-weekly-todo">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect width="18" height="18" x="3" y="4" rx="2" ry="2"/>
              <line x1="16" x2="16" y1="2" y2="6"/>
              <line x1="8" x2="8" y1="2" y2="6"/>
              <line x1="3" x2="21" y1="10" y2="10"/>
            </svg>
            Weekly Todo
          </router-link>
          <button class="btn-agent-chat" @click="showGenericChatModal = true">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            Chat with agent
          </button>
          <button class="btn-new-todo" @click="uiStore.openCreateModal()">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 5v14"/>
              <path d="M5 12h14"/>
            </svg>
            New Todo
          </button>
        </div>
      </div>

      <!-- Search results: table view when user has run a search -->
      <div v-if="hasActiveSearch" class="search-results-section">
        <div class="section-header">
          <h3>Search results ({{ todoStore.todos.length }})</h3>
          <p class="section-description">Tasks matching "{{ searchTerm.trim() }}"</p>
        </div>
        <div class="search-results-table-wrapper">
          <table class="search-results-table">
            <thead>
              <tr>
                <th>Title</th>
                <th>Description</th>
                <th>Status</th>
                <th>Urgency</th>
                <th>Importance</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="todo in todoStore.todos"
                :key="todo.id"
                class="search-result-row"
              >
                <td class="col-title">{{ todo.title }}</td>
                <td class="col-description">{{ truncatedDescription(todo.description) }}</td>
                <td>{{ todo.status }}</td>
                <td>{{ todo.urgency || '–' }}</td>
                <td>{{ todo.importance || '–' }}</td>
                <td class="col-actions">
                  <button
                    type="button"
                    class="btn-view"
                    @click="handleView(todo)"
                  >
                    View
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-if="todoStore.todos.length === 0" class="search-no-results">
          No tasks match your search. Try a different term or clear to see all tasks.
        </p>
      </div>

      <!-- Matrix and unclassified: shown when not searching -->
      <template v-else>
        <TodoCanvas
          :urgent-important-todos="todoStore.urgentImportant"
          :urgent-not-important-todos="todoStore.urgentNotImportant"
          :not-urgent-important-todos="todoStore.notUrgentImportant"
          :not-urgent-not-important-todos="todoStore.notUrgentNotImportant"
          :projects="projects"
          @update="handleUpdatePriority"
          @view="handleView"
          @edit="handleEdit"
          @delete="handleDelete"
          @chat="handleChat"
          @plan="handlePlan"
        />

        <!-- Unclassified Open/Started Todos -->
        <div v-if="unclassifiedOpenTodos.length > 0" class="unclassified-section">
        <div class="section-header">
          <h3>Unclassified Open/Started Todos</h3>
          <p class="section-description">Drag these todos to the matrix above to classify them</p>
        </div>
        <div class="todos-grid">
          <TodoCard
            v-for="todo in unclassifiedOpenTodos"
            :key="todo.id"
            :todo="todo"
            :projects="projects"
            @view="handleView"
            @edit="handleEdit"
            @delete="handleDelete"
            @chat="handleChat"
            @plan="handlePlan"
          />
        </div>
      </div>
      </template>
    </div>

    <Modal
      :show="showCreateModal"
      title="Create New Todo"
      size="large"
      @close="closeCreateModal"
    >
      <TodoForm
        @submit="handleCreate"
        @cancel="closeCreateModal"
      />
    </Modal>

    <Modal
      :show="showEditModal"
      title="Edit Todo"
      size="large"
      @close="closeEditModal"
    >
      <TodoForm
        v-if="editingTodo"
        :initial-data="editingTodo"
        :is-edit="true"
        @submit="handleUpdate"
        @cancel="closeEditModal"
      />
    </Modal>

    <ChatModal
      :show="showChatModal"
      :todo="chattingTodo || {}"
      @close="closeChatModal"
    />

    <TaskPlanModal
      :show="showPlanModal"
      :todo="planningTodo || {}"
      @close="closePlanModal"
    />

    <TaskDetailModal
      :show="showDetailModal"
      :todo="viewingTodo || {}"
      :projects="projects"
      @close="closeDetailModal"
      @edit="handleDetailEdit"
      @chat="handleDetailChat"
      @plan="handleDetailPlan"
    />

    <GenericChatModal
      :show="showGenericChatModal"
      @close="showGenericChatModal = false"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useTodoStore } from '@/stores/todoStore'
import { useUiStore } from '@/stores/uiStore'
import { projectsApi } from '@/services/api'
import TodoCanvas from '@/components/todo/TodoCanvas.vue'
import TodoCard from '@/components/todo/TodoCard.vue'
import TodoForm from '@/components/todo/TodoForm.vue'
import Modal from '@/components/common/Modal.vue'
import ChatModal from '@/components/chat/ChatModal.vue'
import GenericChatModal from '@/components/chat/GenericChatModal.vue'
import TaskPlanModal from '@/components/todo/TaskPlanModal.vue'
import TaskDetailModal from '@/components/todo/TaskDetailModal.vue'

const todoStore = useTodoStore()
const uiStore = useUiStore()
const projects = ref([])
const searchTerm = ref('')
const hasSearched = ref(false)

const loading = computed(() => todoStore.loading)
const error = computed(() => todoStore.error)

const loadingMessage = computed(() => {
  const term = searchTerm.value?.trim()
  return term ? `Searching for "${term}"...` : 'Loading todos...'
})

const hasActiveSearch = computed(
  () => hasSearched.value && searchTerm.value?.trim().length > 0
)

const showCreateModal = computed(() => uiStore.showCreateModal)
const showEditModal = computed(() => uiStore.showEditModal)
const showChatModal = ref(false)
const showGenericChatModal = ref(false)
const showPlanModal = ref(false)
const showDetailModal = ref(false)

const editingTodo = ref(null)
const chattingTodo = ref(null)
const planningTodo = ref(null)
const viewingTodo = ref(null)

const unclassifiedOpenTodos = computed(() => {
  return todoStore.todos.filter(todo => 
    (todo.status === 'Open' || todo.status === 'Started') &&
    (!todo.urgency || !todo.importance)
  )
})

onMounted(async () => {
  await Promise.all([loadTodos(), loadProjects()])
})

async function loadTodos() {
  try {
    const params = { status: 'Open,Started', limit: 500 }
    const term = searchTerm.value?.trim()
    if (term) params.search = term
    await todoStore.fetchTodos(params)
  } catch (err) {
    console.error('Failed to load todos:', err)
  }
}

function runSearch() {
  hasSearched.value = true
  loadTodos()
}

function clearSearch() {
  searchTerm.value = ''
  hasSearched.value = false
  loadTodos()
}

function truncatedDescription(description) {
  if (!description) return '–'
  const maxLen = 80
  return description.length <= maxLen ? description : description.slice(0, maxLen) + '…'
}

async function loadProjects() {
  try {
    const response = await projectsApi.list({ limit: 500 })
    projects.value = response.data.projects
  } catch (err) {
    console.error('Failed to load projects:', err)
  }
}

async function handleCreate(todoData) {
  try {
    await todoStore.createTodo(todoData)
    closeCreateModal()
  } catch (err) {
    console.error('Failed to create todo:', err)
  }
}

async function handleUpdate(todoData) {
  try {
    if (editingTodo.value) {
      await todoStore.updateTodo(editingTodo.value.id, todoData)
      closeEditModal()
    }
  } catch (err) {
    console.error('Failed to update todo:', err)
  }
}

async function handleUpdatePriority({ id, urgency, importance }) {
  try {
    await todoStore.updateTodo(id, { urgency, importance })
  } catch (err) {
    console.error('Failed to update todo priority:', err)
  }
}

function handleEdit(todo) {
  editingTodo.value = todo
  uiStore.openEditModal(todo.id)
}

async function handleDelete(todo) {
  if (confirm(`Delete "${todo.title}"?`)) {
    try {
      await todoStore.deleteTodo(todo.id)
    } catch (err) {
      console.error('Failed to delete todo:', err)
    }
  }
}

function closeCreateModal() {
  uiStore.closeCreateModal()
}

function closeEditModal() {
  uiStore.closeEditModal()
  editingTodo.value = null
}

function handleChat(todo) {
  chattingTodo.value = todo
  showChatModal.value = true
}

function closeChatModal() {
  showChatModal.value = false
  chattingTodo.value = null
}

function handlePlan(todo) {
  planningTodo.value = todo
  showPlanModal.value = true
}

function closePlanModal() {
  showPlanModal.value = false
  planningTodo.value = null
}

function handleView(todo) {
  viewingTodo.value = todo
  showDetailModal.value = true
}

function closeDetailModal() {
  showDetailModal.value = false
  viewingTodo.value = null
}

function handleDetailEdit(todo) {
  closeDetailModal()
  handleEdit(todo)
}

function handleDetailChat(todo) {
  closeDetailModal()
  handleChat(todo)
}

function handleDetailPlan(todo) {
  closeDetailModal()
  handlePlan(todo)
}

defineExpose({
  openCreateModal: () => uiStore.openCreateModal()
})
</script>

<style scoped>
.dashboard {
  min-height: calc(100vh - 52px);
  background: #f9fafb;
  width: 100%;
}

:global(.dark) .dashboard {
  background: #0f172a;
}

.dashboard-content {
  width: 100%;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 2rem 2rem 1rem;
  gap: 1rem;
  flex-wrap: wrap;
}

.dashboard-search {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
  min-width: 200px;
  max-width: 400px;
}

.search-input {
  flex: 1;
  padding: 0.5rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.875rem;
  color: #111827;
  background: #fff;
}

.search-input::placeholder {
  color: #94a3b8;
}

.search-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

:global(.dark) .search-input {
  background: #1e293b;
  border-color: #475569;
  color: #f1f5f9;
}

:global(.dark) .search-input::placeholder {
  color: #64748b;
}

.btn-search {
  padding: 0.5rem 1rem;
  background: #334155;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
}

.btn-search:hover {
  background: #475569;
}

.btn-search-clear {
  padding: 0.5rem 0.75rem;
  background: transparent;
  color: #64748b;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.875rem;
  cursor: pointer;
  white-space: nowrap;
}

.btn-search-clear:hover {
  color: #475569;
  border-color: #cbd5e1;
}

:global(.dark) .btn-search-clear {
  color: #94a3b8;
  border-color: #475569;
}

:global(.dark) .btn-search-clear:hover {
  color: #e2e8f0;
  border-color: #64748b;
}

.dashboard-header-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.btn-weekly-todo {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1rem;
  background: #f1f5f9;
  color: #334155;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.2s;
}

.btn-weekly-todo:hover {
  background: #e2e8f0;
  border-color: #cbd5e1;
  color: #1e293b;
}

:global(.dark) .btn-weekly-todo {
  background: #334155;
  color: #e2e8f0;
  border-color: #475569;
}

:global(.dark) .btn-weekly-todo:hover {
  background: #475569;
  border-color: #64748b;
}

.btn-weekly-todo svg {
  width: 18px;
  height: 18px;
}

.btn-agent-chat {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1rem;
  background: #f1f5f9;
  color: #334155;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-agent-chat:hover {
  background: #e2e8f0;
  border-color: #cbd5e1;
}

:global(.dark) .btn-agent-chat {
  background: #334155;
  color: #e2e8f0;
  border-color: #475569;
}

:global(.dark) .btn-agent-chat:hover {
  background: #475569;
  border-color: #64748b;
}

.btn-agent-chat svg {
  width: 18px;
  height: 18px;
}

.dashboard-header h2 {
  margin: 0 0 0.5rem 0;
  font-size: 1.875rem;
  font-weight: 700;
  color: #111827;
}

:global(.dark) .dashboard-header h2 {
  color: #f1f5f9;
}

.view-description {
  margin: 0;
  color: #6b7280;
  font-size: 1rem;
}

.btn-new-todo {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1rem;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-new-todo:hover {
  background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.35);
}

.btn-new-todo svg {
  width: 18px;
  height: 18px;
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

.btn-primary {
  background-color: #2563eb;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-primary:hover {
  background-color: #1d4ed8;
}

.search-results-section {
  margin: 0 2rem 2rem;
}

.search-results-table-wrapper {
  overflow-x: auto;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #fff;
}

:global(.dark) .search-results-table-wrapper {
  border-color: #334155;
  background: #1e293b;
}

.search-results-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.search-results-table th {
  text-align: left;
  padding: 0.75rem 1rem;
  font-weight: 600;
  color: #475569;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}

:global(.dark) .search-results-table th {
  color: #94a3b8;
  background: #0f172a;
  border-bottom-color: #334155;
}

.search-results-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #e2e8f0;
  color: #334155;
}

:global(.dark) .search-results-table td {
  border-bottom-color: #334155;
  color: #e2e8f0;
}

.search-result-row:hover {
  background: #f1f5f9;
}

:global(.dark) .search-result-row:hover {
  background: #334155;
}

.search-results-table .col-title {
  font-weight: 500;
  max-width: 240px;
}

.search-results-table .col-description {
  max-width: 320px;
  color: #64748b;
}

:global(.dark) .search-results-table .col-description {
  color: #94a3b8;
}

.search-results-table .col-actions {
  white-space: nowrap;
  text-align: right;
}

.btn-view {
  padding: 0.375rem 0.75rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
}

.btn-view:hover {
  background: #2563eb;
}

.search-no-results {
  margin: 1.5rem 0 0;
  color: #64748b;
  font-size: 0.9375rem;
}

:global(.dark) .search-no-results {
  color: #94a3b8;
}

.unclassified-section {
  margin: 2rem 0;
  padding: 0 2rem 2rem;
}

.section-header {
  margin-bottom: 1.5rem;
}

.section-header h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: #111827;
}

.section-description {
  margin: 0;
  color: #6b7280;
  font-size: 0.875rem;
}

.todos-grid {
  display: grid;
  width: 100%;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1rem;
}

@media (max-width: 768px) {
  .unclassified-section {
    padding: 0 1rem 2rem;
  }

  .todos-grid {
    grid-template-columns: 1fr;
  }
}
</style>

