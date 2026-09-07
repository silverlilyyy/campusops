import axios from 'axios'
import type { ApiResponse, HealthInfo } from './types'

// 统一走 /api/v1；Vite dev server 会把 /api 与 /health 代理到后端 8000 端口
const http = axios.create({
  baseURL: '/api/v1',
  timeout: 120000,
})

http.interceptors.response.use(
  (resp) => resp,
  (err) => {
    const detail = err?.response?.data?.detail
    const msg =
      (Array.isArray(detail)
        ? detail.map((d: { msg?: string }) => d.msg).join('；')
        : typeof detail === 'string'
          ? detail
          : null) || err?.message || '网络请求失败'
    return Promise.reject(new Error(msg))
  },
)

// 请求并解包统一响应 {ok, data, message}
export async function request<T>(config: {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  url: string
  params?: Record<string, unknown>
  data?: unknown
}): Promise<T> {
  const resp = await http.request<ApiResponse<T>>({
    method: config.method ?? 'GET',
    url: config.url,
    params: config.params,
    data: config.data,
  })
  const body = resp.data
  if (body && body.ok === false) {
    throw new Error(body.message || '请求失败')
  }
  return body.data as T
}

// 健康检查（不在 /api/v1 前缀下）
export async function health(): Promise<HealthInfo> {
  const resp = await axios.get<HealthInfo>('/health')
  return resp.data
}
