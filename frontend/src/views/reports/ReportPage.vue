<script setup>
import { ref } from 'vue'
import { reportAPI } from '../../api'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../../stores/auth'

const auth = useAuthStore()
const loading = ref(false)

async function exportTeachers() {
  loading.value = true
  try {
    const res = await reportAPI.exportTeachers()
    downloadBlob(res, '教师名单.xlsx')
  } catch (e) { ElMessage.error('导出失败') }
  loading.value = false
}

async function exportAttendance() {
  loading.value = true
  try {
    const res = await reportAPI.exportAttendance()
    downloadBlob(res, '考勤记录.xlsx')
  } catch (e) { ElMessage.error('导出失败') }
  loading.value = false
}

function downloadBlob(data, filename) {
  const url = window.URL.createObjectURL(new Blob([data]))
  const a = document.createElement('a')
  a.href = url; a.download = filename; a.click()
  window.URL.revokeObjectURL(url)
  ElMessage.success(`已下载: ${filename}`)
}
</script>

<template>
  <div class="page-container">
    <h2 class="page-title">报表导出</h2>
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card shadow="hover" style="text-align:center;cursor:pointer" @click="exportTeachers">
          <div style="font-size:48px;margin-bottom:12px">📋</div>
          <h3>教师名单</h3>
          <p style="color:var(--text-light)">导出所有在职教师信息</p>
          <el-button type="primary" :loading="loading">导出 Excel</el-button>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" style="text-align:center;cursor:pointer" @click="exportAttendance">
          <div style="font-size:48px;margin-bottom:12px">📊</div>
          <h3>考勤记录</h3>
          <p style="color:var(--text-light)">导出考勤打卡记录</p>
          <el-button type="success" :loading="loading">导出 Excel</el-button>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
