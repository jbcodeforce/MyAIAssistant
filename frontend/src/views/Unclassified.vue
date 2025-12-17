<template>
  <div class="unclassified-view">
    <div class="view-header">
      <div>
        <h2>Unclassified Todos</h2>
        <p class="view-description">
          Todos without urgency or importance classification
        </p>
      </div>
      <button @click="openCreateModal" class="btn-primary">
        + New Todo
      </button>
    </div>

    <div v-if="loading" class="loading-state">
      <p>Loading todos...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button @click="loadUnclassified" class="btn-primary">Retry</button>
    </div>

    <div v-else class="todos-list-container">
      <div v-if="unclassifiedTodos.length === 0" class="empty-state">
        <p>No unclassified todos</p>
        <p class="empty-state-hint">
          All todos have been classified with urgency and importance
        </p>
      </div>

      <div v-else class="todos-grid">
        <TodoCard
          v-for="todo in sortedTodos"
          :key="todo.id"
          :todo="todo"
          @click="handleEdit(todo)"
          @edit="handleEdit"
          @delete="handleDelete"
          @plan="handlePlan"
        />
      </div>

      <div v-if="hasMore" class="load-more">
        <button @click="loadMore" class="btn-secondary">
          Load More
        </button>
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

    <TaskPlanModal
      :show="showPlanModal"
      :todo="planningTodo || {}"
      @close="closePlanModal"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useTodoStore } from '@/stores/todoStore'
import { useUiStore } from '@/stores/uiStore'
import TodoCard from '@/components/todo/TodoCard.vue'
import TodoForm from '@/components/todo/TodoForm.vue'
import Modal from '@/components/common/Modal.vue'
import TaskPlanModal from '@/components/todo/TaskPlanModal.vue'

const todoStore = useTodoStore()
const uiStore = useUiStore()

const unclassifiedTodos = ref([])
const totalCount = ref(0)
const currentSkip = ref(0)
const limit = 20

const loading = computed(() => todoStore.loading)
const error = computed(() => todoStore.error)

const showCreateModal = computed(() => uiStore.showCreateModal)
const showEditModal = computed(() => uiStore.showEditModal)

const editingTodo = ref(null)
const planningTodo = ref(null)
const showPlanModal = ref(false)

const sortedTodos = computed(() => {
  return [...unclassifiedTodos.value].sort((a, b) => {
    const dateA = new Date(a.created_at)
    const dateB = new Date(b.created_at)
    return dateB - dateA
  })
})

const hasMore = computed(() => {
  return unclassifiedTodos.value.length < totalCount.value
})

onMounted(() => {
  loadUnclassified()
})

async function loadUnclassified() {
  try {
    const response = await todoStore.fetchUnclassifiedTodos({
      skip: 0,
      limit
    })
    unclassifiedTodos.value = response.todos
    totalCount.value = response.total
    currentSkip.value = response.todos.length
  } catch (err) {
    console.error('Failed to load unclassified todos:', err)
  }
}

async function loadMore() {
  try {
    const response = await todoStore.fetchUnclassifiedTodos({
      skip: currentSkip.value,
      limit
    })
    unclassifiedTodos.value = [...unclassifiedTodos.value, ...response.todos]
    currentSkip.value = unclassifiedTodos.value.length
  } catch (err) {
    console.error('Failed to load more todos:', err)
  }
}

async function handleCreate(todoData) {
  try {
    await todoStore.createTodo(todoData)
    closeCreateModal()
    await loadUnclassified()
  } catch (err) {
    console.error('Failed to create todo:', err)
  }
}

async function handleUpdate(todoData) {
  try {
    if (editingTodo.value) {
      await todoStore.updateTodo(editingTodo.value.id, todoData)
      closeEditModal()
      await loadUnclassified()
    }
  } catch (err) {
    console.error('Failed to update todo:', err)
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
      await loadUnclassified()
    } catch (err) {
      console.error('Failed to delete todo:', err)
    }
  }
}

function openCreateModal() {
  uiStore.openCreateModal()
}

function closeCreateModal() {
  uiStore.closeCreateModal()
}

function closeEditModal() {
  uiStore.closeEditModal()
  editingTodo.value = null
}

function handlePlan(todo) {
  planningTodo.value = todo
  showPlanModal.value = true
}

function closePlanModal() {
  showPlanModal.value = false
  planningTodo.value = null
}
</script>

<style scoped>
.unclassified-view {
  min-height: calc(100vh - 52px);
  background: #f9fafb;
  padding: 2rem;
  width: 100%;
}

:global(.dark) .unclassified-view {
  background: #0f172a;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
}

.view-header h2 {
  margin: 0 0 0.5rem 0;
  font-size: 1.875rem;
  font-weight: 700;
  color: #111827;
}

.view-description {
  margin: 0;
  color: #6b7280;
  font-size: 1rem;
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

.todos-list-container {
  width: 100%;
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  background: white;
  border-radius: 12px;
  border: 2px dashed #e5e7eb;
}

.empty-state p {
  margin: 0;
  font-size: 1.125rem;
  color: #6b7280;
}

.empty-state-hint {
  margin-top: 0.5rem;
  font-size: 0.875rem;
  color: #9ca3af;
}

.todos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1rem;
  width: 100%;
}

.load-more {
  display: flex;
  justify-content: center;
  margin-top: 2rem;
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
  background-color: white;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-secondary:hover {
  background-color: #f9fafb;
}

@media (max-width: 768px) {
  .unclassified-view {
    padding: 1rem;
  }

  .view-header {
    flex-direction: column;
    gap: 1rem;
  }

  .todos-grid {
    grid-template-columns: 1fr;
  }
}
</style>

