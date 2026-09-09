<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { health } from '../api/client'
import type { HealthInfo } from '../api/types'
import { authState, loadCurrentUser } from '../auth'

const route = useRoute()
const info = ref<HealthInfo | null>(null)
const healthError = ref('')

const navs = [
  { to: '/', label: 'AI 对话', icon: '💬' },
  { to: '/dashboard', label: '总览', icon: '📊' },
  { to: '/academic', label: '学业', icon: '📚' },
  { to: '/finance', label: '财务', icon: '💰' },
  { to: '/schedule', label: '日程', icon: '🗓️' },
  { to: '/plans', label: '方案回放', icon: '🧭' },
  { to: '/profile', label: '个人中心', icon: '👤' },
]

onMounted(async () => {
  try {
    info.value = await health()
  } catch (e) {
    healthError.value = e instanceof Error ? e.message : '无法连接后端'
  }
  await loadCurrentUser()
})

const online = () => !!info.value && info.value.mysql && info.value.redis
</script>

<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-logo">🏫</div>
        <div>
          <div class="brand-name">CampusOps</div>
          <div class="brand-sub">AI 校园生活规划</div>
        </div>
      </div>

      <nav class="nav">
        <router-link
          v-for="n in navs"
          :key="n.to"
          :to="n.to"
          class="nav-item"
          :class="{ active: route.path === n.to }"
        >
          <span class="nav-icon">{{ n.icon }}</span>
          <span>{{ n.label }}</span>
        </router-link>
      </nav>

      <div class="user-chip" v-if="authState.user">
        <span class="user-avatar">👤</span>
        <span class="user-name">{{ authState.user.nickname || authState.user.username }}</span>
      </div>

      <div class="sidebar-foot">
        <div class="status-dot" :class="online() ? 'ok' : 'down'" />
        <div class="status-text">
          <template v-if="healthError">{{ healthError }}</template>
          <template v-else-if="!info">连接中…</template>
          <template v-else>
            MySQL {{ info.mysql ? '✓' : '✗' }} · Redis {{ info.redis ? '✓' : '✗' }}
            <div class="muted">{{ info.agents?.length ?? 0 }} 个 Agent</div>
          </template>
        </div>
      </div>
    </aside>

    <main class="main">
      <header class="topbar">
        <h1 class="page-title">{{ (route.meta.title as string) || '' }}</h1>
      </header>
      <div class="content">
        <router-view />
      </div>
    </main>
  </div>
</template>

<style scoped>
.layout {
  display: flex;
  height: 100%;
}

.sidebar {
  width: 220px;
  flex-shrink: 0;
  background: #101828;
  color: #e5e7eb;
  display: flex;
  flex-direction: column;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.brand-logo {
  font-size: 26px;
}

.brand-name {
  font-weight: 700;
  font-size: 16px;
  color: #fff;
}

.brand-sub {
  font-size: 11px;
  color: #9ca3af;
}

.nav {
  flex: 1;
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  color: #d1d5db;
  transition: all 0.15s ease;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #fff;
}

.nav-item.active {
  background: var(--primary);
  color: #fff;
}

.nav-icon {
  font-size: 16px;
}

.user-chip {
  margin: 0 16px 10px;
  padding: 8px 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.06);
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #e5e7eb;
}

.user-avatar {
  font-size: 15px;
}

.user-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar-foot {
  padding: 14px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
}

.status-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-dot.ok {
  background: #22c55e;
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.2);
}

.status-dot.down {
  background: #ef4444;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.2);
}

.status-text {
  color: #d1d5db;
  line-height: 1.4;
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.topbar {
  height: 60px;
  flex-shrink: 0;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  padding: 0 24px;
}

.page-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.content {
  flex: 1;
  overflow: auto;
  padding: 20px 24px;
}
</style>
