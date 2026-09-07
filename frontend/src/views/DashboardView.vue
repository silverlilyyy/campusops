<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import type { Assignment, Exam, FinanceSummary, Plan, Preference, Schedule, Task, UserInfo } from '../api/types'

const user = ref<UserInfo | null>(null)
const preference = ref<Preference | null>(null)
const exams = ref<Exam[]>([])
const assignments = ref<Assignment[]>([])
const tasks = ref<Task[]>([])
const schedules = ref<Schedule[]>([])
const plan = ref<Plan | null>(null)
const finance = ref<FinanceSummary | null>(null)
const error = ref('')
const loading = ref(true)

const editForm = reactive({ nickname: '', email: '' })
const profileSaving = ref(false)
const profileError = ref('')
const profileOk = ref('')

const monthSpent = computed(() => {
  const cats = finance.value?.by_category ?? []
  return cats.reduce((sum, c) => sum + Number(c.total || 0), 0)
})

const pendingAssignments = computed(() =>
  assignments.value.filter((a) => a.status === 'pending' || a.status === 'in_progress'),
)

const pendingTasks = computed(() =>
  tasks.value.filter((t) => t.status !== 'done' && t.status !== 'cancelled'),
)

onMounted(async () => {
  loading.value = true
  try {
    const [me, ex, asg, tsk, sch, pl, fin] = await Promise.all([
      api.me(),
      api.upcomingExams(30),
      api.listAssignments(),
      api.listTasks(),
      api.listSchedules(),
      api.latestPlan(),
      api.financeSummary(),
    ])
    user.value = me.user
    preference.value = me.preference
    editForm.nickname = me.user.nickname || ''
    editForm.email = me.user.email || ''
    exams.value = ex
    assignments.value = asg
    tasks.value = tsk
    schedules.value = sch
    plan.value = pl
    finance.value = fin
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载总览失败'
  } finally {
    loading.value = false
  }
})

function fmtDateTime(s?: string | null) {
  if (!s) return '—'
  return s.replace('T', ' ').slice(0, 16)
}

async function saveProfile() {
  profileSaving.value = true
  profileError.value = ''
  profileOk.value = ''
  try {
    const res = await api.updateMe({
      nickname: editForm.nickname || null,
      email: editForm.email || null,
    })
    user.value = res.user
    profileOk.value = '个人信息已更新'
  } catch (e) {
    profileError.value = e instanceof Error ? e.message : '更新失败'
  } finally {
    profileSaving.value = false
  }
}
</script>

<template>
  <div>
    <div v-if="error" class="error-banner">{{ error }}</div>
    <div v-if="loading" class="empty">加载中…</div>

    <template v-else>
      <!-- 统计卡片 -->
      <div class="grid cols-4 stats">
        <div class="card stat">
          <div class="stat-num">{{ pendingTasks.length }}</div>
          <div class="muted">待办任务</div>
        </div>
        <div class="card stat">
          <div class="stat-num">{{ pendingAssignments.length }}</div>
          <div class="muted">进行中作业</div>
        </div>
        <div class="card stat">
          <div class="stat-num">{{ exams.length }}</div>
          <div class="muted">30 天内考试</div>
        </div>
        <div class="card stat">
          <div class="stat-num">¥{{ monthSpent.toFixed(2) }}</div>
          <div class="muted">本月已消费</div>
        </div>
      </div>

      <div class="grid cols-2" style="margin-top: 16px">
        <!-- 用户信息 -->
        <div class="card">
          <h3>👤 我的信息</h3>
          <table class="table">
            <tbody>
              <tr><td class="muted">昵称</td><td>{{ user?.nickname || user?.username || '—' }}</td></tr>
              <tr><td class="muted">用户名</td><td>{{ user?.username || '—' }}</td></tr>
              <tr>
                <td class="muted">学习时段</td>
                <td>{{ preference?.study_start || '—' }} ~ {{ preference?.study_end || '—' }}</td>
              </tr>
              <tr>
                <td class="muted">每周学习时长</td>
                <td>{{ preference?.weekly_study_hours ?? '—' }} 小时</td>
              </tr>
              <tr>
                <td class="muted">月度预算</td>
                <td>¥{{ preference?.monthly_budget ?? '—' }}</td>
              </tr>
            </tbody>
          </table>
          <router-link to="/academic" class="btn sm">去设置 →</router-link>

          <hr class="divider" />
          <h3>✏️ 修改个人信息</h3>
          <div v-if="profileError" class="error-banner">{{ profileError }}</div>
          <div v-if="profileOk" class="ok-banner">{{ profileOk }}</div>
          <div class="grid cols-2">
            <div class="field">
              <label>昵称</label>
              <input v-model="editForm.nickname" placeholder="请输入昵称" />
            </div>
            <div class="field">
              <label>邮箱</label>
              <input v-model="editForm.email" placeholder="请输入邮箱" />
            </div>
          </div>
          <button class="btn primary" :disabled="profileSaving" @click="saveProfile">
            {{ profileSaving ? '保存中…' : '保存修改' }}
          </button>
        </div>

        <!-- 最新方案 -->
        <div class="card">
          <h3>🧭 最新行动方案</h3>
          <div v-if="plan">
            <div class="muted">方案 #{{ plan.id }} · {{ plan.status }}</div>
            <p v-if="plan.goal" style="margin: 8px 0">{{ plan.goal }}</p>
            <div class="mini-items">
              <div v-for="it in (plan.items || []).slice(0, 5)" :key="it.id" class="mini-item">
                <span class="badge blue">{{ it.day || '—' }}</span> {{ it.content }}
              </div>
            </div>
            <router-link to="/plans" class="btn sm">查看详情 →</router-link>
          </div>
          <div v-else class="empty">暂无行动方案，去「AI 对话」生成一份吧</div>
        </div>

        <!-- 即将到来的考试 -->
        <div class="card">
          <h3>📚 即将考试</h3>
          <table v-if="exams.length" class="table">
            <thead>
              <tr><th>科目</th><th>日期</th><th>地点</th></tr>
            </thead>
            <tbody>
              <tr v-for="e in exams" :key="e.id">
                <td>{{ e.name }}</td>
                <td>{{ e.exam_date }}</td>
                <td>{{ e.location || '—' }}</td>
              </tr>
            </tbody>
          </table>
          <div v-else class="empty">近 30 天没有考试</div>
        </div>

        <!-- 近期日程 -->
        <div class="card">
          <h3>🗓️ 近期日程</h3>
          <table v-if="schedules.length" class="table">
            <thead>
              <tr><th>日期</th><th>时间</th><th>内容</th></tr>
            </thead>
            <tbody>
              <tr v-for="s in schedules.slice(0, 8)" :key="s.id">
                <td>{{ s.day }}</td>
                <td>{{ s.start_time }} - {{ s.end_time }}</td>
                <td>{{ s.title || s.schedule_type }}</td>
              </tr>
            </tbody>
          </table>
          <div v-else class="empty">暂无日程安排</div>
        </div>
      </div>

      <!-- 待办任务 -->
      <div class="card" style="margin-top: 16px">
        <h3>✅ 待办任务</h3>
        <table v-if="pendingTasks.length" class="table">
          <thead>
            <tr><th>任务</th><th>类型</th><th>优先级</th><th>截止时间</th><th>状态</th></tr>
          </thead>
          <tbody>
            <tr v-for="t in pendingTasks" :key="t.id">
              <td>{{ t.title }}</td>
              <td><span class="badge gray">{{ t.task_type || 'general' }}</span></td>
              <td>{{ t.priority ?? '—' }}</td>
              <td>{{ fmtDateTime(t.deadline) }}</td>
              <td><span class="badge amber">{{ t.status }}</span></td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty">暂无待办任务</div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.stats .stat-num {
  font-size: 28px;
  font-weight: 700;
  color: var(--primary);
}

.mini-items {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin: 10px 0;
  font-size: 13px;
}

.mini-item {
  display: flex;
  gap: 8px;
  align-items: baseline;
}
</style>
