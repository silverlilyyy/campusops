<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'
import type { Course, Task } from '../api/types'

const courses = ref<Course[]>([])
const tasks = ref<Task[]>([])
const loading = ref(false)
const error = ref('')

const weekdays = [
  { value: 1, label: '周一' },
  { value: 2, label: '周二' },
  { value: 3, label: '周三' },
  { value: 4, label: '周四' },
  { value: 5, label: '周五' },
  { value: 6, label: '周六' },
  { value: 7, label: '周日' },
]

const periods = [
  { value: 1, label: '第一节', time: '08:00 - 09:45', start: 8 * 60 },
  { value: 2, label: '第二节', time: '10:05 - 11:50', start: 10 * 60 + 5 },
  { value: 3, label: '第三节', time: '14:00 - 15:45', start: 14 * 60 },
  { value: 4, label: '第四节', time: '16:05 - 17:50', start: 16 * 60 + 5 },
  { value: 5, label: '第五节', time: '18:40 - 20:25', start: 18 * 60 + 40 },
  { value: 6, label: '第六节', time: '20:40 - 21:25', start: 20 * 60 + 40 },
]

function timeToMinutes(value?: string | null) {
  if (!value) return null
  const match = value.match(/^(\d{1,2}):(\d{2})/)
  return match ? Number(match[1]) * 60 + Number(match[2]) : null
}

function periodForCourse(course: Course) {
  const start = timeToMinutes(course.start_time)
  if (start == null) return null

  // 优先按固定节次的开始时间匹配；兼容历史数据中的少量分钟偏差。
  return periods.reduce((closest, period) => {
    if (!closest) return period
    return Math.abs(period.start - start) < Math.abs(closest.start - start)
      ? period
      : closest
  }, periods[0])
}

function coursesFor(weekday: number, period: number) {
  return courses.value.filter((course) => {
    const matchedPeriod = periodForCourse(course)
    return course.weekday === weekday && matchedPeriod?.value === period
  })
}

const hasCourses = computed(() => courses.value.length > 0)

onMounted(async () => {
  loading.value = true
  try {
    const [courseList, taskList] = await Promise.all([
      api.listCourses(),
      api.listTasks(),
    ])
    courses.value = courseList
    tasks.value = taskList
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载课表失败'
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
      <div class="timetable-card">
        <div class="timetable-title">
          <div>
            <h2>本周课表</h2>
            <div class="muted">固定节次安排</div>
          </div>
          <div v-if="!hasCourses" class="muted">暂无课程</div>
        </div>

        <div class="timetable">
          <div class="corner-cell">节次</div>
          <div v-for="day in weekdays" :key="day.value" class="day-header">
            {{ day.label }}
          </div>

          <template v-for="period in periods" :key="period.value">
            <div class="period-cell">
              <strong>{{ period.label }}</strong>
              <span>{{ period.time }}</span>
            </div>
            <div
              v-for="day in weekdays"
              :key="`${period.value}-${day.value}`"
              class="course-cell"
            >
              <div
                v-for="course in coursesFor(day.value, period.value)"
                :key="course.id"
                class="course-card"
              >
                <div class="course-name">{{ course.name }}</div>
                <div v-if="course.teacher" class="course-detail">👤 {{ course.teacher }}</div>
                <div v-if="course.location" class="course-detail">📍 {{ course.location }}</div>
                <div v-if="course.start_time && course.end_time" class="course-detail">
                  {{ course.start_time.slice(0, 5) }} - {{ course.end_time.slice(0, 5) }}
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>

      <div class="card" style="margin-top: 16px">
        <h3>📌 相关任务</h3>
        <table v-if="tasks.length" class="table">
          <thead>
            <tr><th>任务</th><th>类型</th><th>计划日期</th><th>截止时间</th><th>状态</th></tr>
          </thead>
          <tbody>
            <tr v-for="task in tasks" :key="task.id">
              <td>{{ task.title }}</td>
              <td><span class="badge gray">{{ task.task_type || 'general' }}</span></td>
              <td>{{ task.plan_date || '—' }}</td>
              <td>{{ task.deadline ? task.deadline.replace('T', ' ').slice(0, 16) : '—' }}</td>
              <td><span class="badge amber">{{ task.status }}</span></td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty">暂无任务</div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.timetable-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 16px;
  overflow-x: auto;
}

.timetable-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.timetable-title h2 {
  margin: 0;
  font-size: 18px;
}

.timetable {
  min-width: 860px;
  display: grid;
  grid-template-columns: 116px repeat(7, minmax(105px, 1fr));
  border-top: 1px solid var(--border);
  border-left: 1px solid var(--border);
}

.corner-cell,
.day-header,
.period-cell,
.course-cell {
  border-right: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}

.corner-cell,
.day-header {
  min-height: 46px;
  padding: 11px 8px;
  background: #f8fafc;
  text-align: center;
  font-weight: 600;
}

.period-cell {
  min-height: 112px;
  padding: 12px 8px;
  background: #fafafa;
  color: var(--text);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  text-align: center;
}

.period-cell span {
  color: var(--text-muted);
  font-size: 11px;
  white-space: nowrap;
}

.course-cell {
  min-height: 112px;
  padding: 7px;
  background: var(--surface);
}

.course-card {
  min-height: 96px;
  padding: 9px;
  border: 1px solid #c7d2fe;
  border-left: 3px solid var(--primary);
  border-radius: 7px;
  background: #eef2ff;
  font-size: 12px;
}

.course-name {
  color: #3730a3;
  font-weight: 700;
  line-height: 1.4;
  margin-bottom: 5px;
}

.course-detail {
  color: var(--text-muted);
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
