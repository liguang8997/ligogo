<script setup>
import { ref, onMounted, computed } from 'vue'
import { teacherAPI } from '../../api'
import { useAuthStore } from '../../stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'

const auth = useAuthStore()
const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const dialogVisible = ref(false)
const isEdit = ref(false)
const form = ref({})
const keyword = ref('')
const statusFilter = ref(null)

const statusMap = { 1: '在职', 2: '离职', 3: '退休', 4: '外聘' }
const genderMap = { 0: '未知', 1: '男', 2: '女' }

async function fetchList() {
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (keyword.value) params.keyword = keyword.value
    if (statusFilter.value) params.status = statusFilter.value
    const res = await teacherAPI.list(params)
    list.value = res.data.items; total.value = res.data.total
  } catch {}
}

function openCreate() {
  isEdit.value = false
  form.value = { name: '', role_code: 1, gender: 1, phone: '', email: '', department: '', title: '', password: '',
    question1: '父亲名字', answer1: '', question2: '母亲名字', answer2: '', question3: '出生地', answer3: '' }
  dialogVisible.value = true
}

function openEdit(row) {
  isEdit.value = true
  form.value = { ...row, id: row.id, teacher_id: row.teacher_id }
  dialogVisible.value = true
}

async function doSave() {
  try {
    if (isEdit.value) {
      await teacherAPI.update(form.value.teacher_id, { phone: form.value.phone, email: form.value.email, department: form.value.department, title: form.value.title, remark: form.value.remark })
      ElMessage.success('更新成功')
    } else {
      await teacherAPI.create(form.value)
      ElMessage.success('教师创建成功')
    }
    dialogVisible.value = false; fetchList()
  } catch (e) { ElMessage.error(e?.message || '操作失败') }
}

async function doDelete(row) {
  try {
    await ElMessageBox.confirm(`确定要软删除教师 ${row.name} 吗？`, '确认', { type: 'warning' })
    await teacherAPI.remove(row.teacher_id)
    ElMessage.success('已删除'); fetchList()
  } catch {}
}

onMounted(fetchList)
</script>

<template>
  <div class="page-container">
    <h2 class="page-title">教师管理</h2>
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索姓名" style="width:200px" clearable @clear="fetchList" @keyup.enter="fetchList" />
      <el-select v-model="statusFilter" placeholder="状态" style="width:120px" clearable @change="fetchList">
        <el-option v-for="(v,k) in statusMap" :key="k" :label="v" :value="Number(k)" />
      </el-select>
      <el-button type="primary" @click="openCreate" v-if="auth.isLeader">新增教师</el-button>
    </div>

    <el-table :data="list" border stripe>
      <el-table-column prop="teacher_id" label="工号" width="100" />
      <el-table-column prop="name" label="姓名" width="100" />
      <el-table-column label="性别" width="60"><template #default="{row}">{{ genderMap[row.gender] }}</template></el-table-column>
      <el-table-column prop="phone" label="手机号" width="130" />
      <el-table-column prop="email" label="邮箱" width="160" />
      <el-table-column prop="department" label="部门" width="100" />
      <el-table-column prop="title" label="职称" width="100" />
      <el-table-column label="状态" width="80"><template #default="{row}">{{ statusMap[row.status] }}</template></el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{row}">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="doDelete(row)" v-if="auth.isAdmin">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination v-model:current-page="page" v-model:page-size="pageSize" :total="total" layout="total,prev,pager,next" @change="fetchList" />

    <el-dialog v-model="dialogVisible" :title="isEdit?'编辑教师':'新增教师'" width="600px">
      <el-form :model="form" label-width="100px">
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="姓名"><el-input v-model="form.name" :disabled="isEdit" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="角色"><el-select v-model="form.role_code" :disabled="isEdit"><el-option label="普通教师" :value="1" /><el-option label="领导" :value="2" /><el-option label="管理员" :value="3" /></el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="性别"><el-select v-model="form.gender"><el-option label="男" :value="1" /><el-option label="女" :value="2" /></el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="手机号"><el-input v-model="form.phone" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="邮箱"><el-input v-model="form.email" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="部门"><el-input v-model="form.department" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="职称"><el-input v-model="form.title" /></el-form-item></el-col>
        </el-row>
        <template v-if="!isEdit">
          <el-divider>登录信息</el-divider>
          <el-row :gutter="16">
            <el-col :span="12"><el-form-item label="密码"><el-input v-model="form.password" type="password" show-password /></el-form-item></el-col>
            <el-col :span="12"><el-form-item label="密保1"><el-input v-model="form.answer1" /></el-form-item></el-col>
            <el-col :span="12"><el-form-item label="密保2"><el-input v-model="form.answer2" /></el-form-item></el-col>
            <el-col :span="12"><el-form-item label="密保3"><el-input v-model="form.answer3" /></el-form-item></el-col>
          </el-row>
        </template>
      </el-form>
      <template #footer><el-button @click="dialogVisible=false">取消</el-button><el-button type="primary" @click="doSave">保存</el-button></template>
    </el-dialog>
  </div>
</template>
