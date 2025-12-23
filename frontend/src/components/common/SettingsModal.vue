<template>
  <Modal :show="show" title="Preferences" :wide="true" @close="handleClose">
    <div class="settings-form">
      <div v-if="loading" class="loading-state">
        <p>Loading settings...</p>
      </div>

      <div v-else-if="error" class="error-state">
        <p class="error-message">{{ error }}</p>
        <button class="btn-secondary" @click="loadSettings">Retry</button>
      </div>

      <form v-else @submit.prevent="handleSubmit">
        <!-- LLM Configuration Section -->
        <div class="settings-section">
          <h4 class="section-title">LLM Configuration</h4>
          <div class="form-group">
            <label for="llm_name">LLM Provider</label>
            <input
              id="llm_provider"
              v-model="form.llm_provider"
              type="text"
              placeholder="e.g., openai, anthropic, ollama"
              class="form-input"
            />
            <span class="form-hint">The model provider to use for AI responses</span>
          </div>
          <div class="form-group">
            <label for="llm_name">LLM Name</label>
            <input
              id="llm_name"
              v-model="form.llm_name"
              type="text"
              placeholder="e.g., gpt-4, claude-3-sonnet, ollama/llama2"
              class="form-input"
            />
            <span class="form-hint">The model name to use for AI responses</span>
          </div>

          <div class="form-group">
            <label for="llm_api_endpoint">API Endpoint</label>
            <input
              id="llm_api_endpoint"
              v-model="form.llm_api_endpoint"
              type="url"
              placeholder="https://api.openai.com/v1"
              class="form-input"
            />
            <span class="form-hint">Base URL for the LLM API service</span>
          </div>

          <div class="form-group">
            <label for="api_key">API Key</label>
            <div class="password-input-wrapper">
              <input
                id="api_key"
                v-model="form.api_key"
                :type="showApiKey ? 'text' : 'password'"
                placeholder="sk-..."
                class="form-input"
              />
              <button 
                type="button" 
                class="toggle-password-btn"
                @click="showApiKey = !showApiKey"
                :title="showApiKey ? 'Hide API key' : 'Show API key'"
              >
                <svg v-if="showApiKey" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                  <line x1="1" y1="1" x2="23" y2="23"/>
                </svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                  <circle cx="12" cy="12" r="3"/>
                </svg>
              </button>
            </div>
            <span class="form-hint">API key for authenticating with the LLM service</span>
          </div>

          <div class="form-group">
            <label for="default_temperature">Default Temperature</label>
            <div class="range-input-wrapper">
              <input
                id="default_temperature"
                v-model.number="form.default_temperature"
                type="range"
                min="0"
                max="2"
                step="0.1"
                class="form-range"
              />
              <span class="range-value">{{ form.default_temperature?.toFixed(1) ?? '0.7' }}</span>
            </div>
            <span class="form-hint">Controls randomness in responses (0 = deterministic, 2 = creative)</span>
          </div>
        </div>

        <!-- RAG Configuration Section -->
        <div class="settings-section">
          <h4 class="section-title">RAG Configuration</h4>
          
          <div class="form-row">
            <div class="form-group">
              <label for="chunk_size">Chunk Size</label>
              <input
                id="chunk_size"
                v-model.number="form.chunk_size"
                type="number"
                min="100"
                max="10000"
                placeholder="1000"
                class="form-input"
              />
              <span class="form-hint">Size of text chunks for indexing</span>
            </div>

            <div class="form-group">
              <label for="overlap">Overlap</label>
              <input
                id="overlap"
                v-model.number="form.overlap"
                type="number"
                min="0"
                max="1000"
                placeholder="200"
                class="form-input"
              />
              <span class="form-hint">Overlap between chunks</span>
            </div>

            <div class="form-group">
              <label for="min_chunk_size">Min Chunk Size</label>
              <input
                id="min_chunk_size"
                v-model.number="form.min_chunk_size"
                type="number"
                min="10"
                max="5000"
                placeholder="100"
                class="form-input"
              />
              <span class="form-hint">Minimum chunk size</span>
            </div>
          </div>
        </div>

        <!-- Form Actions -->
        <div class="form-actions">
          <button type="button" class="btn-secondary" @click="handleClose">
            Cancel
          </button>
          <button type="submit" class="btn-primary" :disabled="saving">
            {{ saving ? 'Saving...' : 'Save Settings' }}
          </button>
        </div>

        <p v-if="saveError" class="save-error">{{ saveError }}</p>
        <p v-if="saveSuccess" class="save-success">Settings saved.</p>
      </form>
    </div>
  </Modal>
</template>

<script setup>
import { ref, watch } from 'vue'
import Modal from '@/components/common/Modal.vue'
import { settingsApi } from '@/services/api'

const props = defineProps({
  show: {
    type: Boolean,
    required: true
  }
})

const emit = defineEmits(['close'])

const loading = ref(false)
const saving = ref(false)
const error = ref(null)
const saveError = ref(null)
const saveSuccess = ref(false)
const showApiKey = ref(false)

const form = ref({
  llm_provider: '',
  llm_name: '',
  llm_api_endpoint: '',
  api_key: '',
  default_temperature: 0.7,
  chunk_size: 1000,
  overlap: 200,
  min_chunk_size: 100
})

watch(() => props.show, (newVal) => {
  if (newVal) {
    loadSettings()
  }
})

async function loadSettings() {
  loading.value = true
  error.value = null
  saveError.value = null
  saveSuccess.value = false
  
  try {
    const response = await settingsApi.getFull()
    const settings = response.data
    
    form.value = {
      llm_provider: settings.llm_provider || '',
      llm_name: settings.llm_name || '',
      llm_api_endpoint: settings.llm_api_endpoint || '',
      api_key: settings.api_key || '',
      default_temperature: settings.default_temperature ?? 0.7,
      chunk_size: settings.chunk_size ?? 1000,
      overlap: settings.overlap ?? 200,
      min_chunk_size: settings.min_chunk_size ?? 100
    }
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to load settings'
    console.error('Failed to load settings:', err)
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  saving.value = true
  saveError.value = null
  saveSuccess.value = false
  
  try {
    // Build update payload with only non-empty values
    const payload = {}
    
    if (form.value.llm_provider) payload.llm_provider = form.value.llm_provider
    if (form.value.llm_name) payload.llm_name = form.value.llm_name
    if (form.value.llm_api_endpoint) payload.llm_api_endpoint = form.value.llm_api_endpoint
    if (form.value.api_key) payload.api_key = form.value.api_key
    if (form.value.default_temperature !== null) payload.default_temperature = form.value.default_temperature
    if (form.value.chunk_size) payload.chunk_size = form.value.chunk_size
    if (form.value.overlap !== null) payload.overlap = form.value.overlap
    if (form.value.min_chunk_size) payload.min_chunk_size = form.value.min_chunk_size
    
    await settingsApi.update(payload)
    saveSuccess.value = true
    
    // Hide success message after 2 seconds
    setTimeout(() => {
      saveSuccess.value = false
    }, 2000)
  } catch (err) {
    saveError.value = err.response?.data?.detail || 'Failed to save settings'
    console.error('Failed to save settings:', err)
  } finally {
    saving.value = false
  }
}

function handleClose() {
  showApiKey.value = false
  emit('close')
}
</script>

<style scoped>
.settings-form {
  min-height: 200px;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  gap: 1rem;
}

.error-message {
  color: #dc2626;
}

.settings-section {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

:global(.dark) .settings-section {
  border-bottom-color: #334155;
}

.settings-section:last-of-type {
  border-bottom: none;
  margin-bottom: 0;
}

.section-title {
  margin: 0 0 1.25rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: #374151;
}

:global(.dark) .section-title {
  color: #e2e8f0;
}

.form-group {
  margin-bottom: 1.25rem;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

:global(.dark) .form-group label {
  color: #e2e8f0;
}

.form-input {
  width: 100%;
  padding: 0.625rem 0.875rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.9375rem;
  background: white;
  color: #111827;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.form-input:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

:global(.dark) .form-input {
  background: #1e293b;
  border-color: #475569;
  color: #f1f5f9;
}

:global(.dark) .form-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

.form-hint {
  display: block;
  margin-top: 0.375rem;
  font-size: 0.75rem;
  color: #6b7280;
}

:global(.dark) .form-hint {
  color: #94a3b8;
}

.password-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.password-input-wrapper .form-input {
  padding-right: 2.75rem;
}

.toggle-password-btn {
  position: absolute;
  right: 0.625rem;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: #6b7280;
  cursor: pointer;
  border-radius: 4px;
  transition: color 0.15s;
}

.toggle-password-btn:hover {
  color: #374151;
}

:global(.dark) .toggle-password-btn {
  color: #94a3b8;
}

:global(.dark) .toggle-password-btn:hover {
  color: #e2e8f0;
}

.range-input-wrapper {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.form-range {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  appearance: none;
  background: #e5e7eb;
  cursor: pointer;
}

.form-range::-webkit-slider-thumb {
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

:global(.dark) .form-range {
  background: #475569;
}

:global(.dark) .form-range::-webkit-slider-thumb {
  background: #3b82f6;
  border-color: #1e293b;
}

.range-value {
  min-width: 2.5rem;
  text-align: center;
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

:global(.dark) .range-value {
  color: #e2e8f0;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

@media (max-width: 600px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e5e7eb;
}

:global(.dark) .form-actions {
  border-top-color: #334155;
}

.btn-primary {
  background-color: #2563eb;
  color: white;
  border: none;
  padding: 0.625rem 1.25rem;
  border-radius: 6px;
  font-weight: 500;
  font-size: 0.9375rem;
  cursor: pointer;
  transition: background-color 0.15s;
}

.btn-primary:hover:not(:disabled) {
  background-color: #1d4ed8;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
  padding: 0.625rem 1.25rem;
  border-radius: 6px;
  font-weight: 500;
  font-size: 0.9375rem;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-secondary:hover {
  background-color: #e5e7eb;
}

:global(.dark) .btn-secondary {
  background-color: #334155;
  color: #e2e8f0;
  border-color: #475569;
}

:global(.dark) .btn-secondary:hover {
  background-color: #475569;
}

.save-error {
  margin-top: 1rem;
  padding: 0.75rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
  color: #dc2626;
  font-size: 0.875rem;
  text-align: center;
}

:global(.dark) .save-error {
  background: rgba(220, 38, 38, 0.1);
  border-color: rgba(220, 38, 38, 0.3);
}

.save-success {
  margin-top: 1rem;
  padding: 0.75rem;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 6px;
  color: #16a34a;
  font-size: 0.875rem;
  text-align: center;
}

:global(.dark) .save-success {
  background: rgba(22, 163, 74, 0.1);
  border-color: rgba(22, 163, 74, 0.3);
}
</style>

