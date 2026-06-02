<script setup>
import { ref, onMounted } from 'vue'
import { affairAPI } from '../../api'
import { useAuthStore } from '../../stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'

const auth = useAuthStore()
const list = ref([]); const total = ref(0); const page = ref(1); const pageSize = ref(10)
const dialogVisible = ref(false); const approveVisible = ref(false)
const form = ref({}); const approveForm = ref({ approved: true, comment: '' }); const currentAffair = ref(null)
const typeMap = {1:'事假',2:'病假',3:'调课',4:'出差',5:'报销',6:'反馈'}
const statusMap = {1:'草稿',2:'审批中',3:'已通过',4:'已驳回',5:'已撤回'}
const statusFilter = ref(null)

async function fetchList() {
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (statusFilter.value) params.status = statusFilter.value
    const res = await affairAPI.list(params)
    list.value = res.data.items; total.value = res.data.total
  } catch {}
}

function openCreate() { form.value = { affair_type: 1, title: '', content: '', start_time: '', end_time: '', urgency: 0 }; dialogVisible.value = true }

async function doSave() {
  try {
    await affairAPI.create(form.value); ElMessage.success('创建成功')
    dialogVisible.value = false; fetchList()
  } catch (e) { ElMessage.error(e?.message || '操作失败') }
}

async function doSubmit(row) { try { await affairAPI.submit(row.id); ElMessage.success('已提交'); fetchList() } catch (e) { ElMessage.error(e?.message) } }
async function doDelete(row) { try { await affairAPI.remove(row.id); ElMessage.success('已删除'); fetchList() } catch (e) { ElMessage.error(e?.message) } }

function openApprove(row) { currentAffair.value = row; approveForm.value = { approved: true, comment: '' }; approveVisible.value = true }

async function doApprove() {
  try {
    await affairAPI.approve(currentAffair.value.id, approveForm.value)
    ElMessage.success(approveForm.value.approved ? '已批准' : '已驳回')
    approveVisible.value = false; fetchList()
  } catch (e) { ElMessage.error(e?.message) }
}

onMounted(fetchList)
</script>

<template>
  <div class="page-container">
    <h2 class="page-title">事务管理</h2>
    <div class="toolbar">
      <el-select v-model="statusFilter" placeholder="状态筛选" style="width:120px" clearable @change="fetchList">
        <el-option v-for="(v,k) in statusMap" :key="k" :label="v" :value="Number(k)" />
      </el-select>
      <el-button type="primary" @click="openCreate">新建事务</el-button>
    </div>

    <el-table :data="list" border stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column label="类型" width="80"><template #default="{row}">{{ typeMap[row.affair_type] }}</template></el-table-column>
      <el-table-column prop="title" label="标题" width="140" />
      <el-table-column prop="content" label="内容" width="200" show-overflow-tooltip />
      <el-table-column prop="teacher_name" label="申请人" width="100" />
      <el-table-column label="状态" width="80"><template #default="{row}"><el-tag :type="row.status===3?'success':row.status===4?'danger':row.status===2?'warning':''">{{ statusMap[row.status] }}</el-tag></template></el-table-column>
      <el-table-column prop="approver_name" label="审批人" width="100" />
      <el-table-column prop="approval_comment" label="审批意见" width="140" show-overflow-tooltip />
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{row}">
          <el-button size="small" type="success" @click="doSubmit(row)" v-if="row.status===1">提交</el-button>
          <el-button size="small" type="warning" @click="openApprove(row)" v-if="row.status===2 && auth.isLeader">审批</el-button>
          <el-button size="small" type="danger" @click="doDelete(row)" v-if="row.status===1">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination v-model:current-page="page" v-model:page-size="pageSize" :total="total" layout="total,prev,pager,next" @change="fetchList" />

    <el-dialog v-model="dialogVisible" title="新建事务" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="类型"><el-select v-model="form.affair_type"><el-option v-for="(v,k) in typeMap" :key="k" :label="v" :value="Number(k)" /></el-select></el-form-item>
        <el-form-item label="标题"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="内容"><el-input v-model="form.content" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="开始时间"><el-input v-model="form.start_time" placeholder="2026-06-01" /></el-form-item>
        <el-form-item label="结束时间"><el-input v-model="form.end_time" placeholder="2026-06-02" /></el-form-item>
        <el-form-item label="紧急"><el-switch v-model="form.urgency" :active-value="1" :inactive-value="0" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialogVisible=false">取消</el-button><el-button type="primary" @click="doSave">保存草稿</el-button></template>
    </el-dialog>

    <el-dialog v-model="approveVisible" title="审批事务" width="400px">
      <el-form :model="approveForm" label-width="100px">
        <el-form-item label="审批结果"><el-radio-group v-model="approveForm.approved"><el-radio :value="true">通过</el-radio><el-radio :value="false">驳回</el-radio></el-radio-group></el-form-item>
        <el-form-item label="审批意见"><el-input v-model="approveForm.comment" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="approveVisible=false">取消</el-button><el-button :type="approveForm.approved?'success':'danger'" @click="doApprove">{{ approveForm.approved?'批准':'驳回' }}</el-button></template>
    </el-dialog>
  </div>
</template>
