<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ElMessage } from 'element-plus'

const auth = useAuthStore()
const router = useRouter()
const form = ref({ teacher_id: '', password: '' })
const loading = ref(false)

async function doLogin() {
  if (!form.value.teacher_id || !form.value.password) return ElMessage.warning('请输入工号和密码')
  loading.value = true
  try {
    await auth.login(form.value.teacher_id, form.value.password)
    ElMessage.success('主公，亮恭候多时！')
    router.push('/dashboard')
  } catch (e) {
    ElMessage.error(e?.message || '登录失败')
  } finally { loading.value = false }
}
</script>

<template>
  <div style="display:flex;justify-content:center;align-items:center;min-height:100vh;background:linear-gradient(135deg,#3C2415,#8B4513,#3C2415)">
    <el-card style="width:420px;padding:20px;text-align:center">
      <div style="font-size:48px;color:var(--gold);margin-bottom:8px">🐉</div>
      <h2 style="color:var(--primary);margin-bottom:4px">蜀汉教师管理系统</h2>
      <p style="color:var(--text-light);margin-bottom:24px">诸葛亮智能助手恭候主公</p>
      <el-form @submit.prevent="doLogin">
        <el-form-item><el-input v-model="form.teacher_id" placeholder="工号" size="large" clearable /></el-form-item>
        <el-form-item><el-input v-model="form.password" type="password" placeholder="密码" size="large" show-password @keyup.enter="doLogin" /></el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" style="width:100%" :loading="loading" @click="doLogin">登 录</el-button>
        </el-form-item>
      </el-form>
      <p style="color:var(--text-light);font-size:12px">管理员账号：32605001 / admin123</p>
    </el-card>
  </div>
</template>
