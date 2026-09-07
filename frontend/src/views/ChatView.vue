<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '../api'
import type { ChatResult, Conversation, Message } from '../api/types'

const conversations = ref<Conversation[]>([])
const currentId = ref<number | null>(null)
const messages = ref<Message[]>([])
const input = ref('')
const sending = ref(false)
const error = ref('')
const lastResult = ref<ChatResult | null>(null)
const loadingConvs = ref(false)

async function loadConversations(selectFirst = false) {
  loadingConvs.value = true
  try {
    conversations.value = await api.listConversations()
    if (selectFirst && conversations.value.length > 0) {
      await selectConversation(conversations.value[0].id)
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载会话失败'
  } finally {
    loadingConvs.value = false
  }
}

async function selectConversation(id: number) {
  currentId.value = id
  lastResult.value = null
  error.value = ''
  try {
    messages.value = await api.getMessages(id)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载消息失败'
  }
}

function newConversation() {
  currentId.value = null
  messages.value = []
  lastResult.value = null
  error.value = ''
}

async function send() {
  const text = input.value.trim()
  if (!text || sending.value) return
  input.value = ''
  error.value = ''
  sending.value = true
  messages.value.push({ id: Date.now(), role: 'user', content: text })

  try {
    const result = await api.chat({
      conversation_id: currentId.value,
      message: text,
    })
    currentId.value = result.conversation_id ?? currentId.value
    lastResult.value = result
    const answer = result.answer || '（Agent 已处理，但未返回文本）'
    messages.value.push({ id: Date.now() + 1, role: 'assistant', content: answer })
    await loadConversations()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '发送失败'
    messages.value.push({ id: Date.now() + 1, role: 'assistant', content: '❌ 请求失败：' + error.value })
  } finally {
    sending.value = false
  }
}

onMounted(() => loadConversations(true))
</script>

<template>
  <div class="chat-wrap">
    <!-- 会话列表 -->
    <aside class="conv-panel card">
      <div class="conv-head">
        <button class="btn primary sm" @click="newConversation">＋ 新建对话</button>
      </div>
      <div class="conv-list">
        <div v-if="loadingConvs" class="empty">加载中…</div>
        <div v-else-if="conversations.length === 0" class="empty">暂无会话</div>
        <div
          v-for="c in conversations"
          :key="c.id"
          class="conv-item"
          :class="{ active: c.id === currentId }"
          @click="selectConversation(c.id)"
        >
          <div class="conv-title">{{ c.title || '未命名' }}</div>
          <div class="muted">{{ c.status || 'active' }}</div>
        </div>
      </div>
    </aside>

    <!-- 消息区 -->
    <section class="chat-panel card">
      <div v-if="error" class="error-banner">{{ error }}</div>
      <div class="notice-banner">
        ⚠️ 提示：AI 助手暂不支持直接录入/修改/删除课程、考试和作业，
        如需管理这些数据，请前往左侧「学业」页面手动操作。
      </div>

      <div class="msg-list">
        <div v-if="messages.length === 0" class="empty">
          👋 你好！我是 CampusOps 校园生活规划助手。<br />
          告诉我你的目标（如「帮我安排下周的期末复习计划」），我会调度多个 Agent 为你生成行动方案。
        </div>

        <div
          v-for="m in messages"
          :key="m.id"
          class="msg"
          :class="m.role === 'user' ? 'user' : 'assistant'"
        >
          <div class="msg-role">{{ m.role === 'user' ? '我' : 'CampusOps' }}</div>
          <div class="msg-bubble">{{ m.content }}</div>
        </div>

        <!-- 方案摘要 -->
        <div v-if="lastResult && lastResult.plan" class="plan-card">
          <div class="plan-head">
            <strong>📋 行动方案 #{{ lastResult.plan.id }}</strong>
            <span class="badge" :class="lastResult.plan.status === 'active' ? 'green' : 'gray'">
              {{ lastResult.plan.status }}
            </span>
          </div>
          <div v-if="lastResult.plan.goal" class="muted">{{ lastResult.plan.goal }}</div>
          <div class="plan-items">
            <div v-for="it in lastResult.plan.items || []" :key="it.id" class="plan-item">
              <span class="badge blue">{{ it.day || '—' }}</span>
              <span>{{ it.content }}</span>
            </div>
            <div v-if="!lastResult.plan.items || lastResult.plan.items.length === 0" class="muted">
              暂无明细
            </div>
          </div>
          <router-link to="/plans" class="btn sm">查看完整方案 →</router-link>
        </div>
      </div>

      <div class="input-bar">
        <textarea
          v-model="input"
          rows="2"
          placeholder="输入你的需求，Enter 发送，Shift+Enter 换行"
          @keydown.enter.exact.prevent="send"
        />
        <button class="btn primary" :disabled="sending || !input.trim()" @click="send">
          {{ sending ? '规划中…' : '发送' }}
        </button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.chat-wrap {
  display: flex;
  gap: 16px;
  height: 100%;
  min-height: 0;
}

.conv-panel {
  width: 240px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  padding: 12px;
}

.conv-head {
  margin-bottom: 10px;
}

.conv-head .btn {
  width: 100%;
}

.conv-list {
  flex: 1;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.conv-item {
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.conv-item:hover {
  background: #f3f4f6;
}

.conv-item.active {
  background: #eef2ff;
}

.conv-title {
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  padding: 0;
  overflow: hidden;
}

.chat-panel .error-banner {
  margin: 12px 12px 0;
}

.notice-banner {
  margin: 12px 12px 0;
  padding: 10px 12px;
  border-radius: 8px;
  background: #fffbeb;
  border: 1px solid #fde68a;
  color: #92400e;
  font-size: 13px;
  line-height: 1.5;
}

.msg-list {
  flex: 1;
  overflow: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.msg {
  display: flex;
  flex-direction: column;
  max-width: 78%;
}

.msg.user {
  align-self: flex-end;
  align-items: flex-end;
}

.msg.assistant {
  align-self: flex-start;
  align-items: flex-start;
}

.msg-role {
  font-size: 11px;
  color: var(--text-muted);
  margin-bottom: 3px;
}

.msg-bubble {
  padding: 10px 14px;
  border-radius: 12px;
  white-space: pre-wrap;
  word-break: break-word;
}

.msg.user .msg-bubble {
  background: var(--primary);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.msg.assistant .msg-bubble {
  background: #f3f4f6;
  border-bottom-left-radius: 4px;
}

.plan-card {
  align-self: stretch;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 12px 14px;
  background: #fafafa;
}

.plan-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.plan-items {
  margin: 10px 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.plan-item {
  display: flex;
  gap: 8px;
  align-items: baseline;
  font-size: 13px;
}

.input-bar {
  display: flex;
  gap: 10px;
  padding: 12px;
  border-top: 1px solid var(--border);
  align-items: flex-end;
}

.input-bar textarea {
  flex: 1;
  resize: none;
}
</style>
