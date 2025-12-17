import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/Dashboard.vue'
import Unclassified from '@/views/Unclassified.vue'
import ArchivedTodos from '@/views/ArchivedTodos.vue'
import Projects from '@/views/Projects.vue'
import Customers from '@/views/Customers.vue'
import Knowledge from '@/views/Knowledge.vue'
import Documentation from '@/views/Documentation.vue'

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
    path: '/projects',
    name: 'Projects',
    component: Projects,
    meta: {
      title: 'Projects - MyAIAssistant'
    }
  },
  {
    path: '/customers',
    name: 'Customers',
    component: Customers,
    meta: {
      title: 'Customers - MyAIAssistant'
    }
  },
  {
    path: '/knowledge',
    name: 'Knowledge',
    component: Knowledge,
    meta: {
      title: 'Knowledge Base - MyAIAssistant'
    }
  },
  {
    path: '/documentation',
    name: 'Documentation',
    component: Documentation,
    meta: {
      title: 'Documentation - MyAIAssistant'
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

