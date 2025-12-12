<template>
  <div class="documentation-view">
    <div class="docs-header">
      <div class="docs-title">
        <h2>Documentation</h2>
        <p class="docs-description">Project documentation and implementation guides</p>
      </div>
      <div class="docs-actions">
        <button class="btn-icon" @click="openInNewTab" title="Open in new tab">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
            <polyline points="15 3 21 3 21 9"/>
            <line x1="10" x2="21" y1="14" y2="3"/>
          </svg>
        </button>
        <button class="btn-icon" @click="refreshDocs" title="Refresh">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
            <path d="M3 3v5h5"/>
            <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/>
            <path d="M16 16h5v5"/>
          </svg>
        </button>
      </div>
    </div>
    <div class="docs-container">
      <iframe 
        ref="docsFrame"
        :src="docsUrl"
        class="docs-iframe"
        @load="onFrameLoad"
      ></iframe>
      <div v-if="loading" class="loading-overlay">
        <div class="loading-spinner"></div>
        <p>Loading documentation...</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const docsFrame = ref(null)
const loading = ref(true)
const docsUrl = '/docs/index.html'

function onFrameLoad() {
  loading.value = false
}

function openInNewTab() {
  window.open(docsUrl, '_blank')
}

function refreshDocs() {
  loading.value = true
  if (docsFrame.value) {
    docsFrame.value.src = docsUrl
  }
}

onMounted(() => {
  // Initial loading state is true, will be set to false on iframe load
})
</script>

<style scoped>
.documentation-view {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 52px);
  background: #1a1a2e;
}

.docs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background: #16213e;
  border-bottom: 1px solid #0f3460;
}

.docs-title h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: #e8e8e8;
  font-family: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
}

.docs-description {
  margin: 0.25rem 0 0;
  font-size: 0.875rem;
  color: #7f8c9b;
}

.docs-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  background: rgba(255, 255, 255, 0.05);
  color: #7f8c9b;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-icon:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #e8e8e8;
}

.docs-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.docs-iframe {
  width: 100%;
  height: 100%;
  border: none;
  background: white;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #1a1a2e;
  gap: 1rem;
}

.loading-overlay p {
  color: #7f8c9b;
  font-size: 0.875rem;
  margin: 0;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #0f3460;
  border-top-color: #4f8cff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 768px) {
  .docs-header {
    padding: 1rem;
  }

  .docs-title h2 {
    font-size: 1.25rem;
  }
}
</style>

