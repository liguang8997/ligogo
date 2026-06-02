<script setup>
import { ref, onMounted } from 'vue'
import { attendanceAPI } from '../../api'
import { ElMessage } from 'element-plus'

const list = ref([]); const total = ref(0); const page = ref(1); const pageSize = ref(10)
const todayRecord = ref(null)
const statusMap = {1:'正常',2:'迟到',3:'早退',4:'缺卡'}
const loading = ref(false)

async function fetchList() {
  try {
    const res = await attendanceAPI.list({ page: page.value, page_size: pageSize.value })
    list.value = res.data.items; total.value = res.data.total
  } catch {}
}

async function doCheckIn() {
  loading.value = true
  try {
    const res = await attendanceAPI.checkIn()
    ElMessage.success('打卡成功！')
    todayRecord.value = res.data
    fetchList()
  } catch (e) { ElMessage.error(e?.message || '打卡失败') }
  finally { loading.value = false }
}

async function doCheckOut() {
  loading.value = true
  try {
    const res = await attendanceAPI.checkOut()
    ElMessage.success('签退成功！')
    todayRecord.value = res.data
    fetchList()
  } catch (e) { ElMessage.error(e?.message || '签退失败') }
  finally { loading.value = false }
}

onMounted(fetchList)
</script>

<template>
  <div class="page-container">
    <h2 class="page-title">考勤打卡</h2>

    <el-row :gutter="20" style="margin-bottom:24px">
      <el-col :span="8">
        <el-card style="text-align:center">
          <div style="font-size:48px;margin-bottom:12px">🏛️</div>
          <el-button type="primary" size="large" @click="doCheckIn" :loading="loading" style="width:100%;margin-bottom:8px">上班打卡</el-button>
          <el-button type="success" size="large" @click="doCheckOut" :loading="loading" style="width:100%">下班签退</el-button>
        </el-card>
      </el-col>
      <el-col :span="16">
        <el-card v-if="todayRecord">
          <h3>今日打卡记录</h3>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="状态">{{ statusMap[todayRecord.status] || todayRecord.status }}</el-descriptions-item>
            <el-descriptions-item label="备注">{{ todayRecord.remark || '-' }}</el-descriptions-item>
            <el-descriptions-item label="上班时间">{{ todayRecord.check_in_time || '未打卡' }}</el-descriptions-item>
            <el-descriptions-item label="下班时间">{{ todayRecord.check_out_time || '未签退' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>

    <h3 style="margin-bottom:12px">打卡记录</h3>
    <el-table :data="list" border stripe>
      <el-table-column prop="teacher_name" label="姓名" width="100" />
      <el-table-column prop="check_date" label="日期" width="120" />
      <el-table-column prop="check_in_time" label="上班时间" width="200" />
      <el-table-column prop="check_out_time" label="下班时间" width="200" />
      <el-table-column label="状态" width="80"><template #default="{row}"><el-tag :type="row.status===1?'success':row.status===2?'warning':'danger'">{{ statusMap[row.status] }}</el-tag></template></el-table-column>
      <el-table-column prop="remark" label="备注" />
    </el-table>
    <el-pagination v-model:current-page="page" v-model:page-size="pageSize" :total="total" layout="total,prev,pager,next" @change="fetchList" />
  </div>
</template>
