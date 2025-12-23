<template>
  <aside class="sidebar" :class="{ collapsed: collapsed }">
    <div class="sidebar-header">
      <div class="logo" v-show="!collapsed">
        <span class="logo-text">MyAIAssistant</span>
      </div>
      <button class="collapse-btn" @click="emit('toggle')" :title="collapsed ? 'Expand' : 'Collapse'">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline v-if="collapsed" points="9 18 15 12 9 6"/>
          <polyline v-else points="15 18 9 12 15 6"/>
        </svg>
      </button>
    </div>

    <nav class="sidebar-nav">
      <!-- Dashboard -->
      <router-link to="/" class="nav-item" active-class="active" exact>
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect width="7" height="9" x="3" y="3" rx="1"/>
          <rect width="7" height="5" x="14" y="3" rx="1"/>
          <rect width="7" height="9" x="14" y="12" rx="1"/>
          <rect width="7" height="5" x="3" y="16" rx="1"/>
        </svg>
        <span class="nav-label">Dashboard</span>
      </router-link>

      <!-- Tasks with submenu -->
      <div class="nav-group">
        <button 
          class="nav-item nav-group-toggle" 
          :class="{ expanded: tasksExpanded, 'has-active': isTasksActive }"
          @click="tasksExpanded = !tasksExpanded"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9 11l3 3L22 4"/>
            <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
          </svg>
          <span class="nav-label">Tasks</span>
          <svg class="expand-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </button>
        <div class="nav-submenu" v-show="tasksExpanded && !collapsed">
          <router-link to="/unclassified" class="nav-subitem" active-class="active">
            <span class="nav-label">Unclassified</span>
          </router-link>
          <router-link to="/archived" class="nav-subitem" active-class="active">
            <span class="nav-label">Archived</span>
          </router-link>
          <router-link to="/projects" class="nav-subitem" active-class="active">
            <span class="nav-label">Projects</span>
          </router-link>
        </div>
      </div>

      <!-- Organizations -->
      <router-link to="/organizations" class="nav-item" active-class="active">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
          <circle cx="9" cy="7" r="4"/>
          <path d="M22 21v-2a4 4 0 0 0-3-3.87"/>
          <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
        </svg>
        <span class="nav-label">Organizations</span>
      </router-link>

      <!-- Knowledge -->
      <router-link to="/knowledge" class="nav-item" active-class="active">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/>
        </svg>
        <span class="nav-label">Knowledge</span>
      </router-link>

      <!-- Documentation -->
      <router-link to="/documentation" class="nav-item" active-class="active">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
          <polyline points="14 2 14 8 20 8"/>
          <line x1="16" x2="8" y1="13" y2="13"/>
          <line x1="16" x2="8" y1="17" y2="17"/>
          <line x1="10" x2="8" y1="9" y2="9"/>
        </svg>
        <span class="nav-label">Docs</span>
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <button class="new-todo-btn" @click="emit('create')" :title="collapsed ? 'New Todo' : ''">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 5v14"/>
          <path d="M5 12h14"/>
        </svg>
        <span class="nav-label">New Todo</span>
      </button>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps({
  collapsed: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['create', 'toggle'])
const route = useRoute()

const tasksExpanded = ref(true)

const isTasksActive = computed(() => {
  return route.path === '/unclassified' || route.path === '/archived' || route.path === '/projects'
})
</script>

<style scoped>
.sidebar {
  width: 180px;
  min-width: 180px;
  height: 100vh;
  background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
  display: flex;
  flex-direction: column;
  transition: width 0.25s ease, min-width 0.25s ease;
  overflow: hidden;
  flex-shrink: 0;
}

:global(.dark) .sidebar {
  background: linear-gradient(180deg, #0f172a 0%, #020617 100%);
}

.sidebar.collapsed {
  width: 52px;
  min-width: 52px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 0.75rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  overflow: hidden;
}

.logo-text {
  font-family: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
  font-size: 0.8125rem;
  font-weight: 600;
  color: #f1f5f9;
  white-space: nowrap;
}

.collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: rgba(255, 255, 255, 0.05);
  color: #94a3b8;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.collapse-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #f1f5f9;
}

.sidebar-nav {
  flex: 1;
  padding: 0.75rem 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.5rem 0.625rem;
  border-radius: 6px;
  text-decoration: none;
  color: #94a3b8;
  font-size: 0.8125rem;
  font-weight: 500;
  transition: all 0.15s;
  border: none;
  background: transparent;
  width: 100%;
  cursor: pointer;
  text-align: left;
}

.nav-item svg {
  flex-shrink: 0;
  width: 18px;
  height: 18px;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #e2e8f0;
}

.nav-item.active {
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
}

.nav-item.active svg {
  color: #60a5fa;
}

.nav-group-toggle {
  position: relative;
}

.nav-group-toggle.has-active {
  color: #60a5fa;
}

.nav-group-toggle.has-active svg:first-child {
  color: #60a5fa;
}

.expand-icon {
  margin-left: auto;
  transition: transform 0.2s;
}

.nav-group-toggle.expanded .expand-icon {
  transform: rotate(180deg);
}

.nav-submenu {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  padding-left: 0.5rem;
  margin-top: 0.25rem;
}

.nav-subitem {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4375rem 0.625rem 0.4375rem 2.25rem;
  border-radius: 5px;
  text-decoration: none;
  color: #94a3b8;
  font-size: 0.75rem;
  font-weight: 500;
  transition: all 0.15s;
  position: relative;
}

.nav-subitem::before {
  content: '';
  position: absolute;
  left: 1.125rem;
  top: 50%;
  transform: translateY(-50%);
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #475569;
  transition: background 0.15s;
}

.nav-subitem:hover {
  background: rgba(255, 255, 255, 0.04);
  color: #e2e8f0;
}

.nav-subitem.active {
  background: rgba(59, 130, 246, 0.1);
  color: #60a5fa;
}

.nav-subitem.active::before {
  background: #60a5fa;
}

.nav-label {
  white-space: nowrap;
  overflow: hidden;
}

.sidebar.collapsed .nav-label,
.sidebar.collapsed .expand-icon {
  display: none;
}

.sidebar.collapsed .nav-item {
  justify-content: center;
  padding: 0.625rem;
}

.sidebar.collapsed .nav-submenu {
  display: none;
}

.sidebar.collapsed .logo {
  display: none;
}

.sidebar.collapsed .sidebar-header {
  justify-content: center;
}

.sidebar-footer {
  padding: 0.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.new-todo-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.5rem 0.75rem;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.8125rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.new-todo-btn:hover {
  background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.35);
}

.sidebar.collapsed .new-todo-btn {
  padding: 0.5rem;
}

.new-todo-btn svg {
  width: 16px;
  height: 16px;
}

@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    z-index: 100;
    transform: translateX(-100%);
  }

  .sidebar.expanded {
    transform: translateX(0);
  }
}
</style>
