import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/Dashboard.vue'
import Unclassified from '@/views/Unclassified.vue'
import ArchivedTodos from '@/views/ArchivedTodos.vue'
import Projects from '@/views/Projects.vue'
import ProjectDetail from '@/views/ProjectDetail.vue'
import ProjectTodos from '@/views/ProjectTodos.vue'
import Organizations from '@/views/Organizations.vue'
import OrganizationDetail from '@/views/OrganizationDetail.vue'
import Knowledge from '@/views/Knowledge.vue'
import Assistant from '@/views/Assistant.vue'
import Meetings from '@/views/Meetings.vue'
import Assets from '@/views/Assets.vue'
import Metrics from '@/views/Metrics.vue'
import SLPAssessments from '@/views/SLPAssessments.vue'
import Persons from '@/views/Persons.vue'
import Agents from '@/views/Agents.vue'
import WeeklyTodo from '@/views/WeeklyTodo.vue'

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
    path: '/weekly-todo',
    name: 'WeeklyTodo',
    component: WeeklyTodo,
    meta: {
      title: 'Weekly Todo - MyAIAssistant'
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
    path: '/projects/:id',
    name: 'ProjectDetail',
    component: ProjectDetail,
    meta: {
      title: 'Project - MyAIAssistant'
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
    path: '/organizations/:id',
    name: 'OrganizationDetail',
    component: OrganizationDetail,
    meta: {
      title: 'Organization - MyAIAssistant'
    }
  },
  {
    path: '/organizations/:id/todos',
    name: 'OrganizationTodos',
    component: () => import('@/views/OrganizationTodos.vue'),
    meta: {
      title: 'Organization Tasks - MyAIAssistant'
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
    path: '/assistant',
    name: 'Assistant',
    component: Assistant,
    meta: {
      title: 'Assistant - MyAIAssistant'
    }
  },
  {
    path: '/agents',
    name: 'Agents',
    component: Agents,
    meta: {
      title: 'Agents - MyAIAssistant'
    }
  },
  {
    path: '/meetings',
    name: 'Meetings',
    component: Meetings,
    meta: {
      title: 'Meeting Notes - MyAIAssistant'
    }
  },
  {
    path: '/assets',
    name: 'Assets',
    component: Assets,
    meta: {
      title: 'Assets - MyAIAssistant'
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
  },
  {
    path: '/persons',
    name: 'Persons',
    component: Persons,
    meta: {
      title: 'Persons - MyAIAssistant'
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
