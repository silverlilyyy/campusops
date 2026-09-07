<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'
import type { Schedule, Task } from '../api/types'

const schedules = ref<Schedule[]>([])
const tasks = ref<Task[]>([])
const loading = ref(false)
const error = ref('')

const weekDays = computed(() => {
  const days: Array<{ key: string; label: string; weekday: string }> = []
  const base = new Date()
  for (let i = 0; i < 7; i++) {
    const d = new Date(base)
    d.setDate(base.getDate() + i)
    const key = d.toISOString().slice(0, 10)
    const labels = ['日', '一', '二', '三', '四', '五', '六']
    days.push({
      key,
      label: `${d.getMonth() + 1}/${d.getDate()}`,
      weekday: '周' + labels[d.getDay()],
    })
  }
  return days
})

const byDay = computed(() => {
  const map = new Map<string, Schedule[]>()
  for (const s of schedules.value) {
    if (!map.has(s.day)) map.set(s.day, [])
    map.get(s.day)!.push(s)
  }
  for (const arr of map.values()) {
    arr.sort((a, b) => (a.start_time < b.start_time ? -1 : 1))
  }
  return map
})

function typeClass(t: string) {
  switch (t) {
    case 'course': return 'blue'
    case 'exam': return 'red'
    case 'activity': return 'purple'
    case 'task': return 'amber'
    default: return 'gray'
  }
}

onMounted(async () => {
  loading.value = true
  try {
    const [s, t] = await Promise.all([api.listSchedules(), api.listTasks()])
    schedules.value = s
    tasks.value = t
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载日程失败'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <div v-if="error" class="error-banner">{{ error }}</div>
    <div v-if="loading" class="empty">加载中…</div>

    <template v-else>
      <div class="week">
        <div v-for="d in weekDays" :key="d.key" class="day-col">
          <div class="day-head">
            <div class="day-date">{{ d.label }}</div>
            <div class="muted">{{ d.weekday }}</div>
          </div>
          <div class="day-body">
            <template v-if="(byDay.get(d.key) || []).length">
              <div v-for="s in byDay.get(d.key)" :key="s.id" class="slot">
                <div class="slot-time">{{ s.start_time }}<br />{{ s.end_time }}</div>
                <div class="slot-main">
                  <div class="slot-title">{{ s.title || s.schedule_type }}</div>
                  <span class="badge" :class="typeClass(s.schedule_type)">{{ s.schedule_type }}</span>
                  <div v-if="s.location" class="muted">📍 {{ s.location }}</div>
                </div>
              </div>
            </template>
            <div v-else class="slot empty-slot">—</div>
          </div>
        </div>
      </div>

      <div class="card" style="margin-top: 16px">
        <h3>📌 相关任务</h3>
        <table v-if="tasks.length" class="table">
          <thead>
            <tr><th>任务</th><th>类型</th><th>计划日期</th><th>截止时间</th><th>状态</th></tr>
          </thead>
          <tbody>
            <tr v-for="t in tasks" :key="t.id">
              <td>{{ t.title }}</td>
              <td><span class="badge gray">{{ t.task_type || 'general' }}</span></td>
              <td>{{ t.plan_date || '—' }}</td>
              <td>{{ t.deadline ? t.deadline.replace('T', ' ').slice(0, 16) : '—' }}</td>
              <td><span class="badge amber">{{ t.status }}</span></td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty">暂无任务</div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.week {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 10px;
  overflow-x: auto;
}

.day-col {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  min-height: 320px;
  display: flex;
  flex-direction: column;
}

.day-head {
  padding: 10px;
  border-bottom: 1px solid var(--border);
  text-align: center;
}

.day-date {
  font-weight: 600;
}

.day-body {
  flex: 1;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.slot {
  border: 1px solid var(--border);
  border-left: 3px solid var(--primary);
  border-radius: 6px;
  padding: 7px 8px;
  font-size: 12px;
}

.slot-time {
  color: var(--text-muted);
  font-size: 11px;
  margin-bottom: 4px;
}

.slot-title {
  font-weight: 600;
  margin-bottom: 2px;
}

.slot-main .muted {
  font-size: 11px;
}

.empty-slot {
  color: var(--text-muted);
  text-align: center;
  font-size: 12px;
  border: 1px dashed var(--border);
}
</style>
