<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import type { Assignment, Course, Exam } from '../api/types'

const tab = ref<'courses' | 'exams' | 'assignments'>('courses')
const courses = ref<Course[]>([])
const exams = ref<Exam[]>([])
const assignments = ref<Assignment[]>([])
const loading = ref(false)
const error = ref('')
const assignFilter = ref('')

const form = reactive({
  name: '',
  teacher: '',
  weekday: '',
  start_time: '',
  end_time: '',
  location: '',
  semester: '',
  credit: '',
  note: '',
})
const saving = ref(false)
const formError = ref('')

const examForm = reactive({
  name: '',
  exam_date: '',
  start_time: '',
  end_time: '',
  location: '',
  weight: '',
  importance: '3',
  note: '',
})
const examSaving = ref(false)
const examError = ref('')

const assignmentForm = reactive({
  title: '',
  kind: 'homework',
  deadline: '',
  estimated_hours: '',
  priority: '3',
  description: '',
})
const assignmentSaving = ref(false)
const assignmentError = ref('')

// 编辑模式：非 null 表示正在编辑对应 id 的记录
const editingCourseId = ref<number | null>(null)
const editingExamId = ref<number | null>(null)
const editingAssignmentId = ref<number | null>(null)

// 时间字符串 "HH:MM:SS" -> "HH:MM"（适配 <input type=time>）
function toTimeInput(v?: string | null) {
  return v ? v.slice(0, 5) : ''
}

// 日期时间 "YYYY-MM-DDTHH:MM:SS" -> "YYYY-MM-DDTHH:MM"（适配 datetime-local）
function toDateTimeLocal(v?: string | null) {
  if (!v) return ''
  // 兼容空格分隔与带 'T' 的两种格式
  const iso = v.replace(' ', 'T')
  return iso.slice(0, 16)
}

async function loadAll() {
  loading.value = true
  error.value = ''
  try {
    const [c, e, a] = await Promise.all([
      api.listCourses(),
      api.listExams(),
      api.listAssignments(),
    ])
    courses.value = c
    exams.value = e
    assignments.value = a
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载失败'
  } finally {
    loading.value = false
  }
}

async function loadAssignments() {
  try {
    assignments.value = await api.listAssignments(assignFilter.value || undefined)
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载作业失败'
  }
}

async function addCourse() {
  if (!form.name.trim()) {
    formError.value = '课程名不能为空'
    return
  }
  saving.value = true
  formError.value = ''
  const payload = {
    name: form.name.trim(),
    teacher: form.teacher || null,
    weekday: form.weekday === '' ? null : Number(form.weekday),
    start_time: form.start_time || null,
    end_time: form.end_time || null,
    location: form.location || null,
    semester: form.semester || null,
    credit: form.credit === '' ? null : Number(form.credit),
    note: form.note || null,
  }
  try {
    if (editingCourseId.value != null) {
      await api.updateCourse(editingCourseId.value, payload)
    } else {
      await api.addCourse(payload)
    }
    resetCourseForm()
    await loadAll()
  } catch (err) {
    formError.value = err instanceof Error ? err.message : '保存失败'
  } finally {
    saving.value = false
  }
}

function editCourse(c: Course) {
  editingCourseId.value = c.id
  Object.assign(form, {
    name: c.name,
    teacher: c.teacher || '',
    weekday: c.weekday != null ? String(c.weekday) : '',
    start_time: toTimeInput(c.start_time),
    end_time: toTimeInput(c.end_time),
    location: c.location || '',
    semester: c.semester || '',
    credit: c.credit != null ? String(c.credit) : '',
    note: c.note || '',
  })
  formError.value = ''
}

function resetCourseForm() {
  editingCourseId.value = null
  Object.assign(form, {
    name: '', teacher: '', weekday: '', start_time: '', end_time: '',
    location: '', semester: '', credit: '', note: '',
  })
}

async function removeCourse(c: Course) {
  if (!confirm(`确定删除课程「${c.name}」吗？`)) return
  try {
    await api.deleteCourse(c.id)
    await loadAll()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '删除失败'
  }
}

async function addExam() {
  if (!examForm.name.trim() || !examForm.exam_date) {
    examError.value = '考试名称和日期为必填项'
    return
  }
  examSaving.value = true
  examError.value = ''
  const payload = {
    name: examForm.name.trim(),
    exam_date: examForm.exam_date,
    start_time: examForm.start_time || null,
    end_time: examForm.end_time || null,
    location: examForm.location || null,
    weight: examForm.weight === '' ? null : Number(examForm.weight),
    importance: examForm.importance === '' ? null : Number(examForm.importance),
    note: examForm.note || null,
  }
  try {
    if (editingExamId.value != null) {
      await api.updateExam(editingExamId.value, payload)
    } else {
      await api.addExam(payload)
    }
    resetExamForm()
    await loadAll()
  } catch (err) {
    examError.value = err instanceof Error ? err.message : '保存失败'
  } finally {
    examSaving.value = false
  }
}

function editExam(e: Exam) {
  editingExamId.value = e.id
  Object.assign(examForm, {
    name: e.name,
    exam_date: e.exam_date,
    start_time: toTimeInput(e.start_time),
    end_time: toTimeInput(e.end_time),
    location: e.location || '',
    weight: e.weight != null ? String(e.weight) : '',
    importance: e.importance != null ? String(e.importance) : '3',
    note: e.note || '',
  })
  examError.value = ''
}

function resetExamForm() {
  editingExamId.value = null
  Object.assign(examForm, {
    name: '', exam_date: '', start_time: '', end_time: '',
    location: '', weight: '', importance: '3', note: '',
  })
}

async function removeExam(e: Exam) {
  if (!confirm(`确定删除考试「${e.name}」吗？`)) return
  try {
    await api.deleteExam(e.id)
    await loadAll()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '删除失败'
  }
}

async function addAssignment() {
  if (!assignmentForm.title.trim() || !assignmentForm.deadline) {
    assignmentError.value = '作业标题和截止时间为必填项'
    return
  }
  assignmentSaving.value = true
  assignmentError.value = ''
  const payload = {
    title: assignmentForm.title.trim(),
    kind: assignmentForm.kind,
    deadline: assignmentForm.deadline,
    estimated_hours:
      assignmentForm.estimated_hours === '' ? null : Number(assignmentForm.estimated_hours),
    priority: assignmentForm.priority === '' ? null : Number(assignmentForm.priority),
    description: assignmentForm.description || null,
  }
  try {
    if (editingAssignmentId.value != null) {
      await api.updateAssignment(editingAssignmentId.value, payload)
    } else {
      await api.addAssignment(payload)
    }
    resetAssignmentForm()
    await loadAll()
  } catch (err) {
    assignmentError.value = err instanceof Error ? err.message : '保存失败'
  } finally {
    assignmentSaving.value = false
  }
}

function editAssignment(a: Assignment) {
  editingAssignmentId.value = a.id
  Object.assign(assignmentForm, {
    title: a.title,
    kind: a.kind || 'homework',
    deadline: toDateTimeLocal(a.deadline),
    estimated_hours: a.estimated_hours != null ? String(a.estimated_hours) : '',
    priority: a.priority != null ? String(a.priority) : '3',
    description: a.description || '',
  })
  assignmentError.value = ''
}

function resetAssignmentForm() {
  editingAssignmentId.value = null
  Object.assign(assignmentForm, {
    title: '', kind: 'homework', deadline: '', estimated_hours: '',
    priority: '3', description: '',
  })
}

async function removeAssignment(a: Assignment) {
  if (!confirm(`确定删除作业「${a.title}」吗？`)) return
  try {
    await api.deleteAssignment(a.id)
    await loadAll()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '删除失败'
  }
}

function weekLabel(w?: number | null) {
  const names = ['', '周一', '周二', '周三', '周四', '周五', '周六', '周日']
  return w ? names[w] || `周${w}` : '—'
}

onMounted(loadAll)
</script>

<template>
  <div>
    <div v-if="error" class="error-banner">{{ error }}</div>

    <div class="tabs">
      <button class="btn" :class="{ primary: tab === 'courses' }" @click="tab = 'courses'">课程</button>
      <button class="btn" :class="{ primary: tab === 'exams' }" @click="tab = 'exams'">考试</button>
      <button class="btn" :class="{ primary: tab === 'assignments' }" @click="tab = 'assignments'">作业</button>
    </div>

    <div v-if="loading" class="empty">加载中…</div>

    <!-- 课程 -->
    <div v-else-if="tab === 'courses'" class="grid cols-2" style="margin-top: 16px">
      <div class="card">
        <h3>课程列表</h3>
        <table v-if="courses.length" class="table">
          <thead>
            <tr><th>课程</th><th>教师</th><th>时间</th><th>地点</th><th>学分</th><th>操作</th></tr>
          </thead>
          <tbody>
            <tr v-for="c in courses" :key="c.id">
              <td>{{ c.name }}</td>
              <td>{{ c.teacher || '—' }}</td>
              <td>{{ weekLabel(c.weekday) }} {{ c.start_time || '' }}-{{ c.end_time || '' }}</td>
              <td>{{ c.location || '—' }}</td>
              <td>{{ c.credit ?? '—' }}</td>
              <td>
                <button class="btn sm" @click="editCourse(c)">编辑</button>
                <button class="btn sm danger" @click="removeCourse(c)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty">暂无课程，请在右侧添加</div>
      </div>

      <div class="card">
        <h3>{{ editingCourseId != null ? '编辑课程' : '添加课程' }}</h3>
        <div v-if="formError" class="error-banner">{{ formError }}</div>
        <div class="field">
          <label>课程名 *</label>
          <input v-model="form.name" placeholder="如：数据库系统" />
        </div>
        <div class="grid cols-2">
          <div class="field">
            <label>教师</label>
            <input v-model="form.teacher" />
          </div>
          <div class="field">
            <label>星期</label>
            <select v-model="form.weekday">
              <option value="">—</option>
              <option v-for="d in 7" :key="d" :value="String(d)">周{{ '一二三四五六日'[d - 1] }}</option>
            </select>
          </div>
        </div>
        <div class="grid cols-2">
          <div class="field">
            <label>开始时间</label>
            <input v-model="form.start_time" type="time" />
          </div>
          <div class="field">
            <label>结束时间</label>
            <input v-model="form.end_time" type="time" />
          </div>
        </div>
        <div class="grid cols-2">
          <div class="field">
            <label>地点</label>
            <input v-model="form.location" />
          </div>
          <div class="field">
            <label>学期</label>
            <input v-model="form.semester" placeholder="如 2025-2026-1" />
          </div>
        </div>
        <div class="field">
          <label>学分</label>
          <input v-model="form.credit" type="number" step="0.5" min="0" />
        </div>
        <div class="field">
          <label>备注</label>
          <input v-model="form.note" />
        </div>
        <button class="btn primary" :disabled="saving" @click="addCourse">
          {{ saving ? '保存中…' : editingCourseId != null ? '保存修改' : '添加课程' }}
        </button>
        <button v-if="editingCourseId != null" class="btn" @click="resetCourseForm">取消</button>
      </div>
    </div>

    <!-- 考试 -->
    <div v-else-if="tab === 'exams'" class="grid cols-2" style="margin-top: 16px">
      <div class="card">
        <h3>考试列表</h3>
        <table v-if="exams.length" class="table">
          <thead>
            <tr><th>考试</th><th>日期</th><th>时间</th><th>地点</th><th>占比</th><th>状态</th><th>操作</th></tr>
          </thead>
          <tbody>
            <tr v-for="e in exams" :key="e.id">
              <td>{{ e.name }}</td>
              <td>{{ e.exam_date }}</td>
              <td>{{ e.start_time || '—' }} - {{ e.end_time || '—' }}</td>
              <td>{{ e.location || '—' }}</td>
              <td>{{ e.weight != null ? e.weight + '%' : '—' }}</td>
              <td><span class="badge" :class="e.status === 'done' ? 'green' : 'amber'">{{ e.status }}</span></td>
              <td>
                <button class="btn sm" @click="editExam(e)">编辑</button>
                <button class="btn sm danger" @click="removeExam(e)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty">暂无考试数据</div>
      </div>

      <div class="card">
        <h3>{{ editingExamId != null ? '编辑考试' : '录入考试' }}</h3>
        <div v-if="examError" class="error-banner">{{ examError }}</div>
        <div class="field">
          <label>考试名称 *</label>
          <input v-model="examForm.name" placeholder="如：数据结构期末考" />
        </div>
        <div class="field">
          <label>考试日期 *</label>
          <input v-model="examForm.exam_date" type="date" />
        </div>
        <div class="grid cols-2">
          <div class="field">
            <label>开始时间</label>
            <input v-model="examForm.start_time" type="time" />
          </div>
          <div class="field">
            <label>结束时间</label>
            <input v-model="examForm.end_time" type="time" />
          </div>
        </div>
        <div class="grid cols-2">
          <div class="field">
            <label>地点</label>
            <input v-model="examForm.location" />
          </div>
          <div class="field">
            <label>成绩占比(%)</label>
            <input v-model="examForm.weight" type="number" step="0.5" min="0" max="100" />
          </div>
        </div>
        <div class="grid cols-2">
          <div class="field">
            <label>重要度(1-5)</label>
            <input v-model="examForm.importance" type="number" min="1" max="5" />
          </div>
          <div class="field">
            <label>备注</label>
            <input v-model="examForm.note" />
          </div>
        </div>
        <button class="btn primary" :disabled="examSaving" @click="addExam">
          {{ examSaving ? '保存中…' : editingExamId != null ? '保存修改' : '录入考试' }}
        </button>
        <button v-if="editingExamId != null" class="btn" @click="resetExamForm">取消</button>
      </div>
    </div>

    <!-- 作业 -->
    <div v-else class="grid cols-2" style="margin-top: 16px">
      <div class="card">
        <div class="head-row">
          <h3 class="mb-0">作业 / 课设</h3>
          <select v-model="assignFilter" style="width: 160px" @change="loadAssignments">
            <option value="">全部状态</option>
            <option value="pending">待开始</option>
            <option value="in_progress">进行中</option>
            <option value="completed">已完成</option>
            <option value="overdue">已逾期</option>
          </select>
        </div>
        <table v-if="assignments.length" class="table">
          <thead>
            <tr><th>标题</th><th>类型</th><th>截止时间</th><th>预计耗时</th><th>优先级</th><th>状态</th><th>操作</th></tr>
          </thead>
          <tbody>
            <tr v-for="a in assignments" :key="a.id">
              <td>{{ a.title }}</td>
              <td><span class="badge gray">{{ a.kind || 'homework' }}</span></td>
              <td>{{ a.deadline.replace('T', ' ').slice(0, 16) }}</td>
              <td>{{ a.estimated_hours ?? '—' }}h</td>
              <td>{{ a.priority ?? '—' }}</td>
              <td>
                <span class="badge" :class="{
                  green: a.status === 'completed',
                  blue: a.status === 'in_progress',
                  amber: a.status === 'pending',
                  red: a.status === 'overdue',
                  gray: true,
                }">{{ a.status }}</span>
              </td>
              <td>
                <button class="btn sm" @click="editAssignment(a)">编辑</button>
                <button class="btn sm danger" @click="removeAssignment(a)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty">暂无作业数据</div>
      </div>

      <div class="card">
        <h3>{{ editingAssignmentId != null ? '编辑作业 / 课设' : '录入作业 / 课设' }}</h3>
        <div v-if="assignmentError" class="error-banner">{{ assignmentError }}</div>
        <div class="field">
          <label>标题 *</label>
          <input v-model="assignmentForm.title" placeholder="如：数据库课程设计" />
        </div>
        <div class="grid cols-2">
          <div class="field">
            <label>类型</label>
            <select v-model="assignmentForm.kind">
              <option value="homework">作业</option>
              <option value="course_design">课设</option>
              <option value="project">项目</option>
            </select>
          </div>
          <div class="field">
            <label>截止时间 *</label>
            <input v-model="assignmentForm.deadline" type="datetime-local" />
          </div>
        </div>
        <div class="grid cols-2">
          <div class="field">
            <label>预计耗时(小时)</label>
            <input v-model="assignmentForm.estimated_hours" type="number" step="0.5" min="0" />
          </div>
          <div class="field">
            <label>优先级(1-5)</label>
            <input v-model="assignmentForm.priority" type="number" min="1" max="5" />
          </div>
        </div>
        <div class="field">
          <label>描述</label>
          <input v-model="assignmentForm.description" />
        </div>
        <button class="btn primary" :disabled="assignmentSaving" @click="addAssignment">
          {{ assignmentSaving ? '保存中…' : editingAssignmentId != null ? '保存修改' : '录入作业' }}
        </button>
        <button v-if="editingAssignmentId != null" class="btn" @click="resetAssignmentForm">取消</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tabs {
  display: flex;
  gap: 8px;
}

.head-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
</style>
