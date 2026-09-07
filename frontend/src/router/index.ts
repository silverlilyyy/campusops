import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: AppLayout,
      children: [
        { path: '', name: 'chat', component: () => import('../views/ChatView.vue'), meta: { title: 'AI 对话' } },
        { path: 'dashboard', name: 'dashboard', component: () => import('../views/DashboardView.vue'), meta: { title: '总览' } },
        { path: 'academic', name: 'academic', component: () => import('../views/AcademicView.vue'), meta: { title: '学业' } },
        { path: 'finance', name: 'finance', component: () => import('../views/FinanceView.vue'), meta: { title: '财务' } },
        { path: 'schedule', name: 'schedule', component: () => import('../views/ScheduleView.vue'), meta: { title: '日程' } },
        { path: 'plans', name: 'plans', component: () => import('../views/PlansView.vue'), meta: { title: '方案回放' } },
      ],
    },
  ],
})

export default router
