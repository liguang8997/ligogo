import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const api = axios.create({ baseURL: '/api/v1' })

api.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.token) config.headers.Authorization = `Bearer ${auth.token}`
  return config
})

api.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const data = err.response?.data
    if (data?.code === 401) {
      const auth = useAuthStore()
      auth.logout()
    }
    return Promise.reject(data || err)
  }
)

// ====== Auth ======
export const authAPI = {
  login: (data) => api.post('/auth/login', data),
  refresh: (data) => api.post('/auth/refresh', data),
  logout: () => api.post('/auth/logout'),
  captcha: () => api.get('/auth/captcha'),
  forgotPassword: (data) => api.post('/auth/forgot-password', data),
  resetPassword: (data) => api.post('/auth/reset-password', data),
  changePassword: (data) => api.put('/auth/password', data),
}

// ====== Teachers ======
export const teacherAPI = {
  list: (params) => api.get('/teachers', { params }),
  detail: (id) => api.get(`/teachers/${id}`),
  create: (data) => api.post('/teachers', data),
  update: (id, data) => api.put(`/teachers/${id}`, data),
  remove: (id) => api.delete(`/teachers/${id}`),
  uploadAvatar: (id, file) => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post(`/teachers/${id}/avatar`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
}

// ====== Courses ======
export const courseAPI = {
  list: (params) => api.get('/courses', { params }),
  detail: (id) => api.get(`/courses/${id}`),
  create: (data) => api.post('/courses', data),
  update: (id, data) => api.put(`/courses/${id}`, data),
  remove: (id) => api.delete(`/courses/${id}`),
}

// ====== Affairs ======
export const affairAPI = {
  list: (params) => api.get('/affairs', { params }),
  create: (data) => api.post('/affairs', data),
  update: (id, data) => api.put(`/affairs/${id}`, data),
  submit: (id) => api.post(`/affairs/${id}/submit`),
  approve: (id, data) => api.post(`/affairs/${id}/approve`, data),
  remove: (id) => api.delete(`/affairs/${id}`),
}

// ====== Attendance ======
export const attendanceAPI = {
  list: (params) => api.get('/attendance', { params }),
  checkIn: () => api.post('/attendance/check-in'),
  checkOut: () => api.post('/attendance/check-out'),
}

// ====== Notifications ======
export const notificationAPI = {
  list: (params) => api.get('/notifications', { params }),
  markRead: (id) => api.put(`/notifications/${id}/read`),
  unreadCount: () => api.get('/notifications/unread-count'),
  remove: (id) => api.delete(`/notifications/${id}`),
}

// ====== Logs ======
export const logAPI = {
  list: (params) => api.get('/logs', { params }),
}

// ====== Reports ======
export const reportAPI = {
  exportTeachers: () => api.get('/reports/teachers/export', { responseType: 'blob' }),
  exportAttendance: (params) => api.get('/reports/attendance/export', { params, responseType: 'blob' }),
}

// ====== Agent ======
export const agentAPI = {
  abilities: () => api.get('/agent/abilities'),
  clearSession: (id) => api.post('/agent/clear-session', null, { params: { session_id: id } }),
  getChatURL: () => '/api/v1/agent/chat',
}

// ====== Files ======
export const fileAPI = {
  upload: (file, type = 'attachment') => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post(`/files/upload?file_type=${type}`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
}
