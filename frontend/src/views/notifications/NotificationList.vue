<script setup>
import { ref, onMounted } from 'vue'
import { notificationAPI } from '../../api'
import { ElMessage } from 'element-plus'

const list = ref([]); const total = ref(0); const page = ref(1); const pageSize = ref(10)
const typeMap = {1:'课程提醒',2:'事务通知',3:'生日祝福',4:'系统公告'}

async function fetchList() {
  try {
    const res = await notificationAPI.list({ page: page.value, page_size: pageSize.value })
    list.value = res.data.items; total.value = res.data.total
  } catch {}
}

async function doMarkRead(row) {
  try { await notificationAPI.markRead(row.id); row.is_read = 1; ElMessage.success('已标记') } catch (e) { ElMessage.error(e?.message) }
}

async function doDelete(row) {
  try { await notificationAPI.remove(row.id); ElMessage.success('已删除'); fetchList() } catch (e) { ElMessage.error(e?.message) }
}

onMounted(fetchList)
</script>

<template>
  <div class="page-container">
    <h2 class="page-title">消息中心</h2>
    <el-table :data="list" border stripe :row-class-name="({row}) => row.is_read ? '' : 'unread-row'">
      <el-table-column label="" width="10"><template #default="{row}"><el-icon v-if="!row.is_read" color="red" size="12"><CircleFilled /></el-icon></template></el-table-column>
      <el-table-column label="类型" width="100"><template #default="{row}">{{ typeMap[row.type] }}</template></el-table-column>
      <el-table-column prop="title" label="标题" width="160" />
      <el-table-column prop="content" label="内容" show-overflow-tooltip />
      <el-table-column prop="created_at" label="时间" width="180" />
      <el-table-column label="操作" width="130" fixed="right">
        <template #default="{row}">
          <el-button size="small" @click="doMarkRead(row)" v-if="!row.is_read">标为已读</el-button>
          <el-button size="small" type="danger" @click="doDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination v-model:current-page="page" v-model:page-size="pageSize" :total="total" layout="total,prev,pager,next" @change="fetchList" />
  </div>
</template>

<style>
.unread-row { font-weight: bold; background: #FFF8DC; }
</style>
