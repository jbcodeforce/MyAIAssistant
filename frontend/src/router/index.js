import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/Dashboard.vue'
import Unclassified from '@/views/Unclassified.vue'
import ArchivedTodos from '@/views/ArchivedTodos.vue'
import Knowledge from '@/views/Knowledge.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
    meta: {
      title: 'Dashboard - MyAIAssistant'
    }
  },
  {
    path: '/unclassified',
    name: 'Unclassified',
    component: Unclassified,
    meta: {
      title: 'Unclassified Todos - MyAIAssistant'
    }
  },
  {
    path: '/archived',
    name: 'Archived',
    component: ArchivedTodos,
    meta: {
      title: 'Archived Todos - MyAIAssistant'
    }
  },
  {
    path: '/knowledge',
    name: 'Knowledge',
    component: Knowledge,
    meta: {
      title: 'Knowledge Base - MyAIAssistant'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title || 'MyAIAssistant'
  next()
})

export default router

