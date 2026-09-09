<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'
import { authState, loadCurrentUser, logout, setToken } from '../auth'

const mode = ref<'login' | 'register'>('login')
const busy = ref(false)
const error = ref('')
const notice = ref('')

// 登录/注册表单
const loginForm = ref({ username: 'demo', password: 'demo' })
const registerForm = ref({ username: '', password: '', nickname: '', email: '' })

// 个人信息编辑
const profileForm = ref({ nickname: '', email: '' })
// 偏好编辑
const prefForm = ref({
  study_start: '08:00:00',
  study_end: '22:30:00',
  weekly_study_hours: 32,
  monthly_budget: 2000,
  notification_enabled: true,
})

const loggedIn = computed(() => !!authState.user)

async function submitLogin() {
  busy.value = true
  error.value = ''
  notice.value = ''
  try {
    const result = await api.login(loginForm.value)
    setToken(result.token)
    await loadCurrentUser()
    syncForms(result)
    notice.value = '登录成功'
  } catch (e) {
    error.value = e instanceof Error ? e.message : '登录失败'
  } finally {
    busy.value = false
  }
}

async function submitRegister() {
  if (registerForm.value.password.length < 4) {
    error.value = '密码至少 4 位'
    return
  }
  busy.value = true
  error.value = ''
  notice.value = ''
  try {
    const result = await api.register(registerForm.value)
    setToken(result.token)
    await loadCurrentUser()
    syncForms(result)
    notice.value = '注册成功，已自动登录'
  } catch (e) {
    error.value = e instanceof Error ? e.message : '注册失败'
  } finally {
    busy.value = false
  }
}

function syncForms(result: { user: { nickname?: string | null; email?: string | null }; preference: any }) {
  profileForm.value.nickname = result.user.nickname ?? ''
  profileForm.value.email = result.user.email ?? ''
  const p = result.preference
  if (p) {
    prefForm.value.study_start = p.study_start ?? '08:00:00'
    prefForm.value.study_end = p.study_end ?? '22:30:00'
    prefForm.value.weekly_study_hours = Number(p.weekly_study_hours ?? 32)
    prefForm.value.monthly_budget = Number(p.monthly_budget ?? 2000)
    prefForm.value.notification_enabled = !!p.notification_enabled
  }
}

async function saveProfile() {
  busy.value = true
  error.value = ''
  notice.value = ''
  try {
    await api.updateMe({ ...profileForm.value })
    await loadCurrentUser()
    notice.value = '个人信息已更新'
  } catch (e) {
    error.value = e instanceof Error ? e.message : '更新失败'
  } finally {
    busy.value = false
  }
}

async function savePreference() {
  busy.value = true
  error.value = ''
  notice.value = ''
  try {
    await api.updatePreference({
      study_start: prefForm.value.study_start,
      study_end: prefForm.value.study_end,
      weekly_study_hours: Number(prefForm.value.weekly_study_hours),
      monthly_budget: Number(prefForm.value.monthly_budget),
      notification_enabled: prefForm.value.notification_enabled,
    })
    notice.value = '偏好已更新'
  } catch (e) {
    error.value = e instanceof Error ? e.message : '更新失败'
  } finally {
    busy.value = false
  }
}

function doLogout() {
  logout()
  notice.value = ''
  error.value = ''
}

onMounted(async () => {
  await loadCurrentUser()
  if (authState.user) {
    profileForm.value.nickname = authState.user.nickname ?? ''
    profileForm.value.email = authState.user.email ?? ''
    try {
      const me = await api.me()
      syncForms({ user: authState.user, preference: me.preference })
    } catch {
      /* 忽略偏好读取失败 */
    }
  }
})
</script>

<template>
  <div class="profile">
    <!-- 未登录：登录 / 注册 -->
    <div v-if="!loggedIn" class="card auth-card">
      <h2>{{ mode === 'login' ? '登录' : '注册' }}</h2>
      <p class="muted">简单账号体系，无外部验证。演示账号：demo / demo</p>

      <form v-if="mode === 'login'" class="form" @submit.prevent="submitLogin">
        <label>用户名</label>
        <input v-model="loginForm.username" placeholder="demo" />
        <label>密码</label>
        <input v-model="loginForm.password" type="password" placeholder="••••••" />
        <button class="btn" type="submit" :disabled="busy">{{ busy ? '登录中…' : '登录' }}</button>
      </form>

      <form v-else class="form" @submit.prevent="submitRegister">
        <label>用户名</label>
        <input v-model="registerForm.username" placeholder="例如 student1" />
        <label>昵称</label>
        <input v-model="registerForm.nickname" placeholder="例如 小华" />
        <label>邮箱（可选）</label>
        <input v-model="registerForm.email" placeholder="you@example.com" />
        <label>密码（至少 4 位）</label>
        <input v-model="registerForm.password" type="password" placeholder="••••••" />
        <button class="btn" type="submit" :disabled="busy">{{ busy ? '注册中…' : '注册并登录' }}</button>
      </form>

      <button class="link" @click="mode = mode === 'login' ? 'register' : 'login'">
        {{ mode === 'login' ? '没有账号？去注册' : '已有账号？去登录' }}
      </button>

      <p v-if="error" class="err">{{ error }}</p>
    </div>

    <!-- 已登录：个人信息 + 偏好 -->
    <template v-else>
      <div class="card">
        <div class="card-head">
          <h2>个人信息</h2>
          <span class="badge">@{{ authState.user?.username }}</span>
        </div>
        <form class="form" @submit.prevent="saveProfile">
          <label>昵称</label>
          <input v-model="profileForm.nickname" />
          <label>邮箱</label>
          <input v-model="profileForm.email" />
          <button class="btn" type="submit" :disabled="busy">保存个人信息</button>
        </form>
      </div>

      <div class="card">
        <h2>学习与预算偏好</h2>
        <form class="form" @submit.prevent="savePreference">
          <div class="row">
            <div>
              <label>学习开始时间</label>
              <input v-model="prefForm.study_start" type="time" />
            </div>
            <div>
              <label>学习结束时间</label>
              <input v-model="prefForm.study_end" type="time" />
            </div>
          </div>
          <div class="row">
            <div>
              <label>每周学习时长（小时）</label>
              <input v-model.number="prefForm.weekly_study_hours" type="number" min="0" step="0.5" />
            </div>
            <div>
              <label>每月预算（元）</label>
              <input v-model.number="prefForm.monthly_budget" type="number" min="0" step="50" />
            </div>
          </div>
          <label class="checkbox">
            <input v-model="prefForm.notification_enabled" type="checkbox" />
            开启通知提醒
          </label>
          <button class="btn" type="submit" :disabled="busy">保存偏好</button>
        </form>
      </div>

      <div class="card">
        <button class="btn danger" @click="doLogout">退出登录</button>
      </div>
    </template>

    <p v-if="notice" class="ok">{{ notice }}</p>
    <p v-if="error" class="err">{{ error }}</p>
  </div>
</template>

<style scoped>
.profile {
  max-width: 640px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
}

.auth-card {
  max-width: 380px;
  margin: 40px auto 0;
}

.card h2 {
  margin: 0 0 8px;
  font-size: 18px;
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.badge {
  font-size: 12px;
  color: var(--primary);
  border: 1px solid var(--primary);
  border-radius: 999px;
  padding: 2px 10px;
}

.muted {
  color: #9ca3af;
  font-size: 13px;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 12px;
}

label {
  font-size: 13px;
  color: #6b7280;
  margin-top: 6px;
}

input {
  padding: 9px 11px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 14px;
  background: var(--background, #fff);
  color: var(--text, #111827);
}

.row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.row > div {
  display: flex;
  flex-direction: column;
}

.checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
}

.checkbox input {
  width: auto;
}

.btn {
  margin-top: 14px;
  padding: 10px 14px;
  border: none;
  border-radius: 8px;
  background: var(--primary);
  color: #fff;
  font-size: 14px;
  cursor: pointer;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn.danger {
  background: #ef4444;
}

.link {
  margin-top: 12px;
  background: none;
  border: none;
  color: var(--primary);
  cursor: pointer;
  font-size: 13px;
}

.err {
  color: #ef4444;
  font-size: 13px;
}

.ok {
  color: #16a34a;
  font-size: 13px;
}
</style>
