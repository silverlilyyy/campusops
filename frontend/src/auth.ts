import { reactive, readonly } from 'vue'
import { api } from './api'
import type { UserInfo } from './api/types'

const TOKEN_KEY = 'campusops_token'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

// 当前登录用户（响应式，供侧边栏/个人中心共用）
const state = reactive<{ user: UserInfo | null }>({ user: null })

export const authState = readonly(state)

export async function loadCurrentUser(): Promise<UserInfo | null> {
  if (!getToken()) {
    state.user = null
    return null
  }
  try {
    const data = await api.authMe()
    state.user = data.user
    return data.user
  } catch {
    state.user = null
    return null
  }
}

export function logout(): void {
  clearToken()
  state.user = null
}
