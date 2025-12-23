<template>

    <Sidebar 
      ref="sidebarRef"
      :collapsed="sidebarCollapsed"
      @create="handleCreateTodo" 
      @toggle="toggleSidebar"
    />
    <div class="main-wrapper">
      <TopBar @toggle-sidebar="toggleSidebar" @open-preferences="openSettingsModal" />
      <main class="app-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" :ref="setViewRef" />
          </transition>
        </router-view>
      </main>
    </div>

    <SettingsModal
      :show="showSettingsModal"
      @close="closeSettingsModal"
    />

</template>

<script setup>
import { ref } from 'vue'
import { useUiStore } from '@/stores/uiStore'
import Sidebar from '@/components/common/Sidebar.vue'
import TopBar from '@/components/common/TopBar.vue'
import SettingsModal from '@/components/common/SettingsModal.vue'

const uiStore = useUiStore()
const currentViewRef = ref(null)
const sidebarCollapsed = ref(false)
const sidebarRef = ref(null)
const showSettingsModal = ref(false)

function setViewRef(el) {
  currentViewRef.value = el
}

function handleCreateTodo() {
  uiStore.openCreateModal()
}

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

function openSettingsModal() {
  showSettingsModal.value = true
}

function closeSettingsModal() {
  showSettingsModal.value = false
}
</script>

<style>
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: #f8fafc;
  color: #111827;
}

html.dark body {
  background: #0f172a;
  color: #f1f5f9;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: row;
}

.main-wrapper {
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

.app-content {
  flex: 1 1 auto;
  overflow-y: auto;
  overflow-x: hidden;
  height: calc(100vh - 52px);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
