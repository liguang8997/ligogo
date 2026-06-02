<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { notificationAPI } from '../api'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const unreadCount = ref(0)

const menuItems = computed(() => {
  const items = [
    { path: '/dashboard', title: '隆中对', icon: 'HomeFilled' },
    { path: '/teachers', title: '教师管理', icon: 'UserFilled' },
    { path: '/courses', title: '课程管理', icon: 'Notebook' },
    { path: '/affairs', title: '事务审批', icon: 'DocumentChecked' },
    { path: '/attendance', title: '考勤打卡', icon: 'Clock' },
    { path: '/notifications', title: '消息中心', icon: 'Bell' },
    { path: '/agent', title: '诸葛亮', icon: 'MagicStick' },
    { path: '/reports', title: '报表导出', icon: 'Download' },
  ]
  if (auth.isAdmin) items.push({ path: '/logs', title: '操作日志', icon: 'List' })
  return items
})

async function fetchUnread() {
  try {
    const res = await notificationAPI.unreadCount()
    unreadCount.value = res.data?.count || 0
  } catch {}
}

onMounted(fetchUnread)
setInterval(fetchUnread, 30000)

function handleSelect(path) { router.push(path) }
function doLogout() { auth.logout() }
</script>

<template>
  <el-container style="height:100vh">
    <el-header style="display:flex;align-items:center;justify-content:space-between;padding:0 20px">
      <div style="display:flex;align-items:center;gap:12px">
        <el-icon size="28"><Moon /></el-icon>
        <span>蜀汉教师管理系统</span>
      </div>
      <div style="display:flex;align-items:center;gap:16px;font-size:14px">
        <span>恭迎 {{ auth.user?.name || '主公' }} （{{ auth.user?.role === 'admin' ? '管理员' : auth.user?.role === 'leader' ? '领导' : '教师' }}）</span>
        <el-button text style="color:#DAA520" @click="doLogout">退出</el-button>
      </div>
    </el-header>
    <el-container>
      <el-aside width="200px">
        <el-menu :default-active="route.path" @select="handleSelect">
          <el-menu-item v-for="item in menuItems" :key="item.path" :index="item.path">
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.title }}</span>
            <el-badge v-if="item.path === '/notifications' && unreadCount" :value="unreadCount" style="margin-left:8px" />
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-main style="background:#FFFCF5;overflow-y:auto">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>
