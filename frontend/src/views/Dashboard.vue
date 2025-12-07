<template>
  <div class="dashboard">
    <div v-if="loading" class="loading-state">
      <p>Loading todos...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button @click="loadTodos" class="btn-primary">Retry</button>
    </div>

    <div v-else>
      <TodoCanvas
        :urgent-important-todos="todoStore.urgentImportant"
        :urgent-not-important-todos="todoStore.urgentNotImportant"
        :not-urgent-important-todos="todoStore.notUrgentImportant"
        :not-urgent-not-important-todos="todoStore.notUrgentNotImportant"
        @update="handleUpdatePriority"
        @edit="handleEdit"
        @delete="handleDelete"
        @chat="handleChat"
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
            @edit="handleEdit"
            @delete="handleDelete"
            @chat="handleChat"
          />
        </div>
      </div>
    </div>

    <Modal
      :show="showCreateModal"
      title="Create New Todo"
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
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useTodoStore } from '@/stores/todoStore'
import { useUiStore } from '@/stores/uiStore'
import TodoCanvas from '@/components/todo/TodoCanvas.vue'
import TodoCard from '@/components/todo/TodoCard.vue'
import TodoForm from '@/components/todo/TodoForm.vue'
import Modal from '@/components/common/Modal.vue'
import ChatModal from '@/components/chat/ChatModal.vue'

const todoStore = useTodoStore()
const uiStore = useUiStore()

const loading = computed(() => todoStore.loading)
const error = computed(() => todoStore.error)

const showCreateModal = computed(() => uiStore.showCreateModal)
const showEditModal = computed(() => uiStore.showEditModal)
const showChatModal = ref(false)

const editingTodo = ref(null)
const chattingTodo = ref(null)

const unclassifiedOpenTodos = computed(() => {
  return todoStore.todos.filter(todo => 
    (todo.status === 'Open' || todo.status === 'Started') &&
    (!todo.urgency || !todo.importance)
  )
})

onMounted(() => {
  loadTodos()
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

defineExpose({
  openCreateModal: () => uiStore.openCreateModal()
})
</script>

<style scoped>
.dashboard {
  min-height: calc(100vh - 80px);
  background: #f9fafb;
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
  max-width: 1400px;
  margin: 2rem auto;
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

