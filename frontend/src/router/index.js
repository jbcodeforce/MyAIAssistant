import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/Dashboard.vue'
import Unclassified from '@/views/Unclassified.vue'
import ArchivedTodos from '@/views/ArchivedTodos.vue'
import Projects from '@/views/Projects.vue'
import ProjectTodos from '@/views/ProjectTodos.vue'
import Organizations from '@/views/Organizations.vue'
import Knowledge from '@/views/Knowledge.vue'
import Metrics from '@/views/Metrics.vue'
import SLPAssessments from '@/views/SLPAssessments.vue'

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
    path: '/projects/:id/todos',
    name: 'ProjectTodos',
    component: ProjectTodos,
    meta: {
      title: 'Project Tasks - MyAIAssistant'
    }
  },
  {
    path: '/organizations',
    name: 'Organizations',
    component: Organizations,
    meta: {
      title: 'Organizations - MyAIAssistant'
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
    path: '/metrics',
    name: 'Metrics',
    component: Metrics,
    meta: {
      title: 'Metrics - MyAIAssistant'
    }
  },
  {
    path: '/life-portfolio',
    name: 'SLPAssessments',
    component: SLPAssessments,
    meta: {
      title: 'Life Portfolio - MyAIAssistant'
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
