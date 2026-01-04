<template>
  <header class="top-bar">
    <div class="top-bar-left">
      <button class="mobile-menu-btn" @click="emit('toggle-sidebar')">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="4" x2="20" y1="12" y2="12"/>
          <line x1="4" x2="20" y1="6" y2="6"/>
          <line x1="4" x2="20" y1="18" y2="18"/>
        </svg>
      </button>
      <span class="current-page">{{ currentPageTitle }}</span>
    </div>

    <div class="top-bar-right">
      <!-- GitHub Link -->
      <a 
        href="https://github.com/jbcodeforce/MyAIAssistant" 
        target="_blank" 
        rel="noopener noreferrer"
        class="icon-btn"
        title="View on GitHub"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
        </svg>
      </a>

      <!-- Dark Mode Toggle -->
      <button class="icon-btn" @click="toggleDarkMode" :title="isDarkMode ? 'Light mode' : 'Dark mode'">
        <svg v-if="isDarkMode" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="4"/>
          <path d="M12 2v2"/>
          <path d="M12 20v2"/>
          <path d="m4.93 4.93 1.41 1.41"/>
          <path d="m17.66 17.66 1.41 1.41"/>
          <path d="M2 12h2"/>
          <path d="M20 12h2"/>
          <path d="m6.34 17.66-1.41 1.41"/>
          <path d="m19.07 4.93-1.41 1.41"/>
        </svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>
        </svg>
      </button>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const emit = defineEmits(['toggle-sidebar'])
const route = useRoute()

const isDarkMode = ref(false)

const currentPageTitle = computed(() => {
  const titles = {
    '/': 'Dashboard',
    '/unclassified': 'Unclassified Tasks',
    '/archived': 'Archived Tasks',
    '/knowledge': 'Knowledge Base',
    '/documentation': 'Documentation'
  }
  return titles[route.path] || 'MyAIAssistant'
})

function toggleDarkMode() {
  isDarkMode.value = !isDarkMode.value
  document.documentElement.classList.toggle('dark', isDarkMode.value)
  localStorage.setItem('darkMode', isDarkMode.value ? 'true' : 'false')
}

onMounted(() => {
  // Load dark mode preference
  const savedDarkMode = localStorage.getItem('darkMode')
  if (savedDarkMode === 'true') {
    isDarkMode.value = true
    document.documentElement.classList.add('dark')
  }
})
</script>

<style scoped>
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 52px;
  width: 100%;
  padding: 0 1.25rem;
  background: white;
  border-bottom: 1px solid #e5e7eb;
}

:global(.dark) .top-bar {
  background: #1e293b;
  border-bottom-color: #334155;
}

.top-bar-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.mobile-menu-btn {
  display: none;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  color: #6b7280;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
}

.mobile-menu-btn:hover {
  background: #f3f4f6;
  color: #111827;
}

:global(.dark) .mobile-menu-btn:hover {
  background: #334155;
  color: #f1f5f9;
}

.current-page {
  font-size: 0.9375rem;
  font-weight: 600;
  color: #111827;
}

:global(.dark) .current-page {
  color: #f1f5f9;
}

.top-bar-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  color: #6b7280;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
  text-decoration: none;
}

.icon-btn:hover {
  background: #f3f4f6;
  color: #111827;
}

:global(.dark) .icon-btn {
  color: #94a3b8;
}

:global(.dark) .icon-btn:hover {
  background: #334155;
  color: #f1f5f9;
}

@media (max-width: 768px) {
  .mobile-menu-btn {
    display: flex;
  }
}
</style>
