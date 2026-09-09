import { request } from './client'
import type {
  Activity,
  AgentAction,
  AgentSession,
  Assignment,
  AuthResult,
  Budget,
  ChatResult,
  Conversation,
  Course,
  Exam,
  Expense,
  FinanceSummary,
  Message,
  Plan,
  Preference,
  Schedule,
  Task,
  UserInfo,
} from './types'

export interface ChatPayload {
  user_id?: number
  conversation_id?: number | null
  message: string
  replan?: boolean
  previous_session_id?: number | null
}

export const api = {
  // 认证
  login(payload: { username: string; password: string }) {
    return request<AuthResult>({ method: 'POST', url: '/auth/login', data: payload })
  },
  register(payload: { username: string; password: string; nickname?: string; email?: string }) {
    return request<AuthResult>({ method: 'POST', url: '/auth/register', data: payload })
  },
  authMe() {
    return request<AuthResult>({ method: 'GET', url: '/auth/me' })
  },

  // 对话
  chat(payload: ChatPayload) {
    return request<ChatResult>({ method: 'POST', url: '/chat', data: payload })
  },

  // 用户
  me() {
    return request<{ user: UserInfo; preference: Preference | null }>({
      method: 'GET',
      url: '/users/me',
    })
  },
  updatePreference(payload: Record<string, unknown>) {
    return request<Preference>({ method: 'PUT', url: '/users/me/preference', data: payload })
  },
  updateMe(payload: Record<string, unknown>) {
    return request<{ user: UserInfo }>({ method: 'PUT', url: '/users/me', data: payload })
  },

  // 会话
  createConversation() {
    return request<Conversation>({ method: 'POST', url: '/conversations' })
  },
  listConversations() {
    return request<Conversation[]>({ method: 'GET', url: '/conversations' })
  },
  getMessages(id: number) {
    return request<Message[]>({ method: 'GET', url: `/conversations/${id}/messages` })
  },

  // 课程
  listCourses() {
    return request<Course[]>({ method: 'GET', url: '/campus/courses' })
  },
  addCourse(payload: Record<string, unknown>) {
    return request<Course>({ method: 'POST', url: '/campus/courses', data: payload })
  },
  updateCourse(id: number, payload: Record<string, unknown>) {
    return request<Course>({ method: 'PUT', url: `/campus/courses/${id}`, data: payload })
  },
  deleteCourse(id: number) {
    return request<null>({ method: 'DELETE', url: `/campus/courses/${id}` })
  },

  // 考试
  listExams() {
    return request<Exam[]>({ method: 'GET', url: '/campus/exams' })
  },
  upcomingExams(days = 30) {
    return request<Exam[]>({ method: 'GET', url: '/campus/exams/upcoming', params: { days } })
  },
  addExam(payload: Record<string, unknown>) {
    return request<Exam>({ method: 'POST', url: '/campus/exams', data: payload })
  },
  updateExam(id: number, payload: Record<string, unknown>) {
    return request<Exam>({ method: 'PUT', url: `/campus/exams/${id}`, data: payload })
  },
  deleteExam(id: number) {
    return request<null>({ method: 'DELETE', url: `/campus/exams/${id}` })
  },

  // 作业
  listAssignments(status?: string) {
    return request<Assignment[]>({
      method: 'GET',
      url: '/campus/assignments',
      params: status ? { status } : undefined,
    })
  },
  addAssignment(payload: Record<string, unknown>) {
    return request<Assignment>({ method: 'POST', url: '/campus/assignments', data: payload })
  },
  updateAssignment(id: number, payload: Record<string, unknown>) {
    return request<Assignment>({ method: 'PUT', url: `/campus/assignments/${id}`, data: payload })
  },
  deleteAssignment(id: number) {
    return request<null>({ method: 'DELETE', url: `/campus/assignments/${id}` })
  },

  // 活动
  listActivities() {
    return request<Activity[]>({ method: 'GET', url: '/campus/activities' })
  },

  // 消费
  listExpenses() {
    return request<Expense[]>({ method: 'GET', url: '/campus/expenses' })
  },
  addExpense(payload: Record<string, unknown>) {
    return request<Expense>({ method: 'POST', url: '/campus/expenses', data: payload })
  },
  financeSummary() {
    return request<FinanceSummary>({ method: 'GET', url: '/campus/finance/summary' })
  },
  listBudgets() {
    return request<Budget[]>({ method: 'GET', url: '/campus/budgets' })
  },
  addBudget(payload: Record<string, unknown>) {
    return request<Budget>({ method: 'POST', url: '/campus/budgets', data: payload })
  },

  // 日程 / 任务
  listSchedules() {
    return request<Schedule[]>({ method: 'GET', url: '/campus/schedules' })
  },
  listTasks(status?: string) {
    return request<Task[]>({
      method: 'GET',
      url: '/campus/tasks',
      params: status ? { status } : undefined,
    })
  },

  // 方案 / 执行回放
  latestPlan() {
    return request<Plan | null>({ method: 'GET', url: '/plans/latest' })
  },
  listSessions() {
    return request<AgentSession[]>({ method: 'GET', url: '/plans/sessions' })
  },
  sessionActions(id: number) {
    return request<{ session: AgentSession; actions: AgentAction[] }>({
      method: 'GET',
      url: `/plans/sessions/${id}/actions`,
    })
  },
  getPlan(id: number) {
    return request<Plan>({ method: 'GET', url: `/plans/${id}` })
  },
  completePlan(id: number) {
    return request<null>({ method: 'POST', url: `/plans/${id}/complete` })
  },
}
