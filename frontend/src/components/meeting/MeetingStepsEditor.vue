<template>
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
          <span class="step-count">{{ pastSteps.length }}</span>
        </div>

        <div
          class="steps-drop-zone"
          :class="{ 'drag-over': dragOverZone === 'past' }"
          @dragover.prevent="handleDragOver($event, 'past')"
          @dragleave="handleDragLeave"
          @drop="handleDrop($event, 'past')"
        >
          <div v-if="pastSteps.length === 0" class="empty-drop-zone">
            <span>No past steps yet</span>
            <span class="drop-hint">Drop steps here or add new</span>
          </div>

          <div
            v-for="(step, index) in pastSteps"
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
              <div v-if="showTaskLinking" class="step-task-selector">
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
          <span class="step-count">{{ nextSteps.length }}</span>
        </div>

        <div
          class="steps-drop-zone"
          :class="{ 'drag-over': dragOverZone === 'next' }"
          @dragover.prevent="handleDragOver($event, 'next')"
          @dragleave="handleDragLeave"
          @drop="handleDrop($event, 'next')"
        >
          <div v-if="nextSteps.length === 0" class="empty-drop-zone">
            <span>No next steps yet</span>
            <span class="drop-hint">Drop steps here or add new</span>
          </div>

          <div
            v-for="(step, index) in nextSteps"
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
              <div v-if="showTaskLinking" class="step-task-selector">
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
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  pastSteps: {
    type: Array,
    required: true
  },
  nextSteps: {
    type: Array,
    required: true
  },
  projectTodos: {
    type: Array,
    default: () => []
  },
  showTaskLinking: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:pastSteps', 'update:nextSteps'])

const isDragging = ref(false)
const dragSource = ref({ list: null, index: null })
const dragOverZone = ref(null)

function addStep(listType) {
  const newStep = { what: '', who: '', todo_id: null }
  if (listType === 'past') {
    emit('update:pastSteps', [...props.pastSteps, newStep])
  } else {
    emit('update:nextSteps', [...props.nextSteps, newStep])
  }
}

function removeStep(listType, index) {
  if (listType === 'past') {
    const next = [...props.pastSteps]
    next.splice(index, 1)
    emit('update:pastSteps', next)
  } else {
    const next = [...props.nextSteps]
    next.splice(index, 1)
    emit('update:nextSteps', next)
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

  const past = [...props.pastSteps]
  const next = [...props.nextSteps]
  const sourceArray = sourceList === 'past' ? past : next
  const targetArray = targetList === 'past' ? past : next

  const [step] = sourceArray.splice(sourceIndex, 1)
  targetArray.push(step)

  emit('update:pastSteps', past)
  emit('update:nextSteps', next)
  handleDragEnd()
}
</script>

<style scoped>
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
  .steps-columns {
    grid-template-columns: 1fr;
  }
}
</style>
