import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authAPI } from '../api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isLeader = computed(() => user.value?.role === 'leader' || user.value?.role === 'admin')

  async function login(teacherId, password) {
    const res = await authAPI.login({ teacher_id: teacherId, password })
    token.value = res.data.access_token
    user.value = { teacher_id: res.data.teacher_id, name: res.data.name, role: res.data.role }
    localStorage.setItem('token', token.value)
    localStorage.setItem('user', JSON.stringify(user.value))
    return res
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    window.location.href = '/login'
  }

  return { token, user, isLoggedIn, isAdmin, isLeader, login, logout }
})
