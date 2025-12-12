<template>
  <header class="app-header">
    <div class="header-content">
      <h1 class="app-title">MyAIAssistant</h1>
      <nav class="nav-menu">
        <router-link to="/" class="nav-link" active-class="active">
          Dashboard
        </router-link>
        <router-link to="/unclassified" class="nav-link" active-class="active">
          Unclassified
        </router-link>
        <router-link to="/archived" class="nav-link" active-class="active">
          Archived
        </router-link>
        <router-link to="/knowledge" class="nav-link" active-class="active">
          Knowledge
        </router-link>
        <router-link to="/documentation" class="nav-link" active-class="active">
          Docs
        </router-link>
        <button class="btn-primary" @click="emit('create')">
          + New Todo
        </button>
      </nav>
    </div>
  </header>
</template>

<script setup>
const emit = defineEmits(['create'])
</script>

<style scoped>
.app-header {
  background: white;
  border-bottom: 1px solid #e5e7eb;
  padding: 1rem 2rem;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1400px;
  margin: 0 auto;
}

.app-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0;
  color: #111827;
}

.nav-menu {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.nav-link {
  text-decoration: none;
  color: #6b7280;
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  transition: all 0.2s;
}

.nav-link:hover {
  color: #111827;
  background-color: #f3f4f6;
}

.nav-link.active {
  color: #2563eb;
  background-color: #dbeafe;
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
</style>

