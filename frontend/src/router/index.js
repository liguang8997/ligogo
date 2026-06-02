import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('../layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
      { path: 'teachers', name: 'Teachers', component: () => import('../views/teachers/TeacherList.vue') },
      { path: 'courses', name: 'Courses', component: () => import('../views/courses/CourseList.vue') },
      { path: 'affairs', name: 'Affairs', component: () => import('../views/affairs/AffairList.vue') },
      { path: 'attendance', name: 'Attendance', component: () => import('../views/attendance/AttendancePage.vue') },
      { path: 'notifications', name: 'Notifications', component: () => import('../views/notifications/NotificationList.vue') },
      { path: 'agent', name: 'Agent', component: () => import('../views/agent/AgentChat.vue') },
      { path: 'logs', name: 'Logs', component: () => import('../views/logs/LogList.vue'), meta: { admin: true } },
      { path: 'reports', name: 'Reports', component: () => import('../views/reports/ReportPage.vue') },
    ],
  },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.token) return next('/login')
  if (to.meta.admin && auth.user?.role !== 'admin') return next('/dashboard')
  next()
})

export default router
