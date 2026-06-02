<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { teacherAPI, courseAPI, affairAPI, agentAPI } from '../api'

const auth = useAuthStore()
const router = useRouter()
const stats = ref({ teachers: 0, courses: 0, affairs: 0 })
const greeting = ref('')

onMounted(async () => {
  try {
    const [t, c, a, ab] = await Promise.all([
      teacherAPI.list({ page: 1, page_size: 1 }),
      courseAPI.list({ page: 1, page_size: 1 }),
      affairAPI.list({ page: 1, page_size: 1 }),
      agentAPI.abilities(),
    ])
    stats.value = {
      teachers: t.data?.total || 0,
      courses: c.data?.total || 0,
      affairs: a.data?.total || 0,
    }
    greeting.value = ab.data?.greeting || '主公在上，亮在此恭候差遣。'
  } catch {}
})

const shortcuts = [
  { title: '教师管理', desc: '查看和管理教师信息', icon: 'UserFilled', path: '/teachers', color: '#8B4513' },
  { title: '课程安排', desc: '管理课程和排课', icon: 'Notebook', path: '/courses', color: '#2E8B57' },
  { title: '事务审批', desc: '处理和审批事务', icon: 'DocumentChecked', path: '/affairs', color: '#B22222' },
  { title: '考勤打卡', desc: '每日打卡签到', icon: 'Clock', path: '/attendance', color: '#5F9EA0' },
  { title: '诸葛丞相', desc: '智能助手对话', icon: 'MagicStick', path: '/agent', color: '#DAA520' },
  { title: '报表导出', desc: '导出Excel报表', icon: 'Download', path: '/reports', color: '#8B7355' },
]
</script>

<template>
  <div class="page-container">
    <div style="background:linear-gradient(135deg,#F5E6D3,#FFF8F0);padding:24px;border-radius:8px;border:1px solid var(--border);margin-bottom:20px">
      <p style="font-size:18px;color:var(--primary);line-height:1.8">{{ greeting }}</p>
      <p style="color:var(--text-light);margin-top:8px">{{ auth.user?.name }}，欢迎回来。</p>
    </div>

    <el-row :gutter="16" style="margin-bottom:20px">
      <el-col :span="8" v-for="(v, k) in stats" :key="k">
        <el-card shadow="hover" style="text-align:center">
          <div style="font-size:32px;color:var(--primary);font-weight:bold">{{ v }}</div>
          <div style="color:var(--text-light)">{{ {teachers:'教师',courses:'课程',affairs:'事务'}[k] }}</div>
        </el-card>
      </el-col>
    </el-row>

    <h3 class="page-title">常用功能</h3>
    <el-row :gutter="16">
      <el-col :span="8" v-for="s in shortcuts" :key="s.path" style="margin-bottom:16px">
        <el-card shadow="hover" style="cursor:pointer" @click="router.push(s.path)">
          <div style="display:flex;align-items:center;gap:12px">
            <div style="width:48px;height:48px;border-radius:8px;display:flex;align-items:center;justify-content:center" :style="{background:s.color+'20'}">
              <el-icon size="24" :style="{color:s.color}"><component :is="s.icon" /></el-icon>
            </div>
            <div>
              <div style="font-weight:bold;color:var(--text)">{{ s.title }}</div>
              <div style="font-size:12px;color:var(--text-light)">{{ s.desc }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
