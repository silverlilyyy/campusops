<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '../api'
import type { AgentAction, AgentSession, Plan } from '../api/types'

const plan = ref<Plan | null>(null)
const sessions = ref<AgentSession[]>([])
const actions = ref<AgentAction[]>([])
const activeSession = ref<AgentSession | null>(null)
const loading = ref(false)
const error = ref('')
const actionError = ref('')

async function loadAll() {
  loading.value = true
  error.value = ''
  try {
    const [p, s] = await Promise.all([api.latestPlan(), api.listSessions()])
    plan.value = p
    sessions.value = s
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载失败'
  } finally {
    loading.value = false
  }
}

async function completePlan() {
  if (!plan.value) return
  try {
    await api.completePlan(plan.value.id)
    await loadAll()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '操作失败'
  }
}

async function viewSession(s: AgentSession) {
  activeSession.value = s
  actionError.value = ''
  try {
    const res = await api.sessionActions(s.id)
    actions.value = res.actions
  } catch (err) {
    actionError.value = err instanceof Error ? err.message : '加载动作轨迹失败'
    actions.value = []
  }
}

function statusClass(s?: string | null) {
  switch (s) {
    case 'completed': return 'green'
    case 'running': return 'blue'
    case 'failed': return 'red'
    default: return 'gray'
  }
}

function fmt(s?: string | null) {
  return s ? s.replace('T', ' ').slice(0, 16) : '—'
}

onMounted(loadAll)
</script>

<template>
  <div>
    <div v-if="error" class="error-banner">{{ error }}</div>
    <div v-if="loading" class="empty">加载中…</div>

    <template v-else>
      <!-- 最新行动方案 -->
      <div class="card">
        <div class="head-row">
          <h3 class="mb-0">🧭 最新行动方案</h3>
          <button
            v-if="plan && plan.status === 'active'"
            class="btn sm"
            @click="completePlan"
          >
            ✓ 标记完成
          </button>
        </div>

        <div v-if="plan">
          <div class="plan-meta">
            <span class="badge" :class="plan.status === 'active' ? 'green' : 'gray'">{{ plan.status }}</span>
            <span class="muted">方案 #{{ plan.id }} · 创建于 {{ fmt(plan.created_at) }}</span>
          </div>
          <p v-if="plan.goal" class="goal">🎯 {{ plan.goal }}</p>
          <p v-if="plan.summary" class="muted">{{ plan.summary }}</p>

          <table v-if="plan.items && plan.items.length" class="table" style="margin-top: 12px">
            <thead>
              <tr><th>#</th><th>执行内容</th><th>日期</th><th>时段</th><th>原因</th><th>状态</th></tr>
            </thead>
            <tbody>
              <tr v-for="(it, idx) in plan.items" :key="it.id">
                <td>{{ idx + 1 }}</td>
                <td>{{ it.content }}</td>
                <td>{{ it.day || '—' }}</td>
                <td>{{ it.start_time || '—' }} - {{ it.end_time || '—' }}</td>
                <td class="muted">{{ it.reason || '—' }}</td>
                <td><span class="badge" :class="it.status === 'done' ? 'green' : 'amber'">{{ it.status }}</span></td>
              </tr>
            </tbody>
          </table>
          <div v-else class="empty">该方案暂无明细</div>
        </div>
        <div v-else class="empty">
          暂无行动方案。去 <router-link to="/">AI 对话</router-link> 提出你的需求，由 Agent 生成一份方案。
        </div>
      </div>

      <!-- 执行历史 -->
      <div class="grid cols-2" style="margin-top: 16px">
        <div class="card">
          <h3>📜 Agent 执行历史</h3>
          <table v-if="sessions.length" class="table">
            <thead>
              <tr><th>#</th><th>输入</th><th>状态</th><th>时间</th></tr>
            </thead>
            <tbody>
              <tr
                v-for="s in sessions"
                :key="s.id"
                style="cursor: pointer"
                :class="{ active: activeSession?.id === s.id }"
                @click="viewSession(s)"
              >
                <td>{{ s.id }}</td>
                <td style="max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap">
                  {{ s.input_text || '—' }}
                </td>
                <td><span class="badge" :class="statusClass(s.status)">{{ s.status }}</span></td>
                <td>{{ fmt(s.started_at) }}</td>
              </tr>
            </tbody>
          </table>
          <div v-else class="empty">暂无执行记录</div>
        </div>

        <div class="card">
          <h3>🔍 动作轨迹</h3>
          <div v-if="actionError" class="error-banner">{{ actionError }}</div>
          <div v-if="!activeSession" class="empty">点击左侧执行记录查看轨迹</div>
          <template v-else>
            <div class="muted" style="margin-bottom: 10px">
              执行 #{{ activeSession.id }} · {{ fmt(activeSession.started_at) }}
            </div>
            <div v-if="actions.length" class="trace">
              <div v-for="a in actions" :key="a.id" class="trace-item">
                <div class="trace-head">
                  <span class="badge blue">{{ a.agent_name || 'agent' }}</span>
                  <span class="badge gray">{{ a.action }}</span>
                  <span class="badge" :class="statusClass(a.status)">{{ a.status }}</span>
                </div>
                <div v-if="a.response" class="trace-resp">{{ a.response }}</div>
              </div>
            </div>
            <div v-else class="empty">暂无动作记录</div>
          </template>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.head-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.plan-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}

.goal {
  margin: 8px 0;
  font-weight: 500;
}

.trace {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 480px;
  overflow: auto;
}

.trace-item {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px;
}

.trace-head {
  display: flex;
  gap: 6px;
  margin-bottom: 6px;
}

.trace-resp {
  font-size: 12px;
  color: var(--text);
  white-space: pre-wrap;
  word-break: break-word;
}

tr.active {
  background: #eef2ff;
}
</style>
