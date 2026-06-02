<script setup>
import { ref, onMounted } from 'vue'
import { courseAPI, teacherAPI } from '../../api'
import { useAuthStore } from '../../stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'

const auth = useAuthStore()
const list = ref([]); const total = ref(0); const page = ref(1); const pageSize = ref(10)
const dialogVisible = ref(false); const isEdit = ref(false); const form = ref({})
const teachers = ref([])
const typeMap = {1:'必修',2:'选修',3:'公选'}

async function fetchList() {
  try {
    const res = await courseAPI.list({ page: page.value, page_size: pageSize.value })
    list.value = res.data.items; total.value = res.data.total
  } catch {}
}

async function fetchTeachers() {
  try {
    const res = await teacherAPI.list({ page: 1, page_size: 100 })
    teachers.value = res.data.items || []
  } catch {}
}

function openCreate() { isEdit.value = false; form.value = { teacher_id: '', course_name: '', semester: '2025-2026-2', schedule_info: '', location: '', class_group: '', course_type: 1 }; dialogVisible.value = true }
function openEdit(row) { isEdit.value = true; form.value = { ...row }; dialogVisible.value = true }

async function doSave() {
  try {
    if (isEdit.value) { await courseAPI.update(form.value.id, form.value); ElMessage.success('更新成功') }
    else { await courseAPI.create(form.value); ElMessage.success('创建成功') }
    dialogVisible.value = false; fetchList()
  } catch (e) { ElMessage.error(e?.message || '操作失败') }
}

async function doDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除课程 ${row.course_name} 吗？`, '确认', { type: 'warning' })
    await courseAPI.remove(row.id); ElMessage.success('已删除'); fetchList()
  } catch {}
}

onMounted(() => { fetchList(); fetchTeachers() })
</script>

<template>
  <div class="page-container">
    <h2 class="page-title">课程管理</h2>
    <div class="toolbar">
      <el-button type="primary" @click="openCreate" v-if="auth.isLeader">新增课程</el-button>
    </div>
    <el-table :data="list" border stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="course_name" label="课程名称" width="140" />
      <el-table-column prop="teacher_name" label="教师" width="100" />
      <el-table-column prop="semester" label="学期" width="120" />
      <el-table-column prop="schedule_info" label="时间" width="100" />
      <el-table-column prop="location" label="地点" width="100" />
      <el-table-column label="类型" width="70"><template #default="{row}">{{ typeMap[row.course_type] }}</template></el-table-column>
      <el-table-column prop="class_group" label="班级" width="100" />
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{row}">
          <el-button size="small" @click="openEdit(row)" v-if="auth.isLeader">编辑</el-button>
          <el-button size="small" type="danger" @click="doDelete(row)" v-if="auth.isLeader">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination v-model:current-page="page" v-model:page-size="pageSize" :total="total" layout="total,prev,pager,next" @change="fetchList" />

    <el-dialog v-model="dialogVisible" :title="isEdit?'编辑课程':'新增课程'" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="教师"><el-select v-model="form.teacher_id" :disabled="isEdit" filterable><el-option v-for="t in teachers" :key="t.teacher_id" :label="t.name" :value="t.teacher_id" /></el-select></el-form-item>
        <el-form-item label="课程名称"><el-input v-model="form.course_name" /></el-form-item>
        <el-form-item label="学期"><el-input v-model="form.semester" /></el-form-item>
        <el-form-item label="时间"><el-input v-model="form.schedule_info" placeholder="周一1-2节" /></el-form-item>
        <el-form-item label="地点"><el-input v-model="form.location" /></el-form-item>
        <el-form-item label="班级"><el-input v-model="form.class_group" /></el-form-item>
        <el-form-item label="类型"><el-select v-model="form.course_type"><el-option label="必修" :value="1" /><el-option label="选修" :value="2" /><el-option label="公选" :value="3" /></el-select></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialogVisible=false">取消</el-button><el-button type="primary" @click="doSave">保存</el-button></template>
    </el-dialog>
  </div>
</template>
