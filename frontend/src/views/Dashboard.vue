<template>
  <div class="dashboard">
    <div v-if="loading" class="loading-state">
      <p>Loading todos...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button @click="loadTodos" class="btn-primary">Retry</button>
    </div>

    <div v-else class="dashboard-content">
      <div class="dashboard-header">
        <div>
          <h2>Dashboard</h2>
          <p class="view-description">Organize tasks by urgency and importance</p>
        </div>
        <button class="btn-new-todo" @click="uiStore.openCreateModal()">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 5v14"/>
            <path d="M5 12h14"/>
          </svg>
          New Todo
        </button>
      </div>

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
    </div>

    <Modal
      :show="showCreateModal"
      title="Create New Todo"
      :wide="true"
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
      :wide="true"
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
import TaskPlanModal from '@/components/todo/TaskPlanModal.vue'
import TaskDetailModal from '@/components/todo/TaskDetailModal.vue'

const todoStore = useTodoStore()
const uiStore = useUiStore()
const projects = ref([])

const loading = computed(() => todoStore.loading)
const error = computed(() => todoStore.error)

const showCreateModal = computed(() => uiStore.showCreateModal)
const showEditModal = computed(() => uiStore.showEditModal)
const showChatModal = ref(false)
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
    await todoStore.fetchTodos({ 
      status: 'Open,Started',
      limit: 500 
    })
  } catch (err) {
    console.error('Failed to load todos:', err)
  }
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

