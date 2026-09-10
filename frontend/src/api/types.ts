// 与后端 app/schemas + db/models 对齐的类型定义
export interface ApiResponse<T = unknown> {
  ok: boolean
  data: T | null
  message: string
}

export interface Course {
  id: number
  user_id: number
  name: string
  teacher?: string | null
  location?: string | null
  weekday?: number | null
  start_time?: string | null
  end_time?: string | null
  semester?: string | null
  credit?: number | string | null
  start_date?: string | null
  end_date?: string | null
  note?: string | null
  created_at?: string
  updated_at?: string
}

export interface Exam {
  id: number
  user_id: number
  course_id?: number | null
  name: string
  exam_date: string
  start_time?: string | null
  end_time?: string | null
  location?: string | null
  weight?: number | string | null
  importance?: number | null
  status?: string | null
  note?: string | null
}

export interface Assignment {
  id: number
  user_id: number
  course_id?: number | null
  title: string
  kind?: string | null
  description?: string | null
  deadline: string
  estimated_hours?: number | string | null
  priority?: number | null
  status?: string | null
  note?: string | null
}

export interface Activity {
  id: number
  user_id: number
  name: string
  category?: string | null
  start_time: string
  end_time?: string | null
  location?: string | null
  importance?: number | null
  note?: string | null
}

export interface Expense {
  id: number
  user_id: number
  amount: number | string
  category?: string | null
  paid_at: string
  note?: string | null
  created_at?: string
}

export interface Schedule {
  id: number
  user_id: number
  day: string
  start_time: string
  end_time: string
  schedule_type: string
  ref_type?: string | null
  ref_id?: number | null
  title?: string | null
  location?: string | null
  status?: string | null
}

export interface Task {
  id: number
  user_id: number
  title: string
  description?: string | null
  task_type?: string | null
  source_type?: string | null
  priority?: number | null
  status?: string | null
  deadline?: string | null
  estimated_hours?: number | string | null
  plan_date?: string | null
  created_at?: string
}

export interface PlanItem {
  id: number
  plan_id: number
  task_id?: number | null
  content: string
  reason?: string | null
  day?: string | null
  start_time?: string | null
  end_time?: string | null
  status?: string | null
  sort_order?: number | null
}

export interface Plan {
  id: number
  user_id: number
  conversation_id?: number | null
  title?: string | null
  goal?: string | null
  summary?: string | null
  status?: string | null
  replan_of_id?: number | null
  created_at?: string
  updated_at?: string
  items?: PlanItem[]
}

export interface Conversation {
  id: number
  title?: string | null
  status?: string | null
}

export interface Message {
  id: number
  role: string
  content?: string | null
  agent_name?: string | null
}

export interface AgentSession {
  id: number
  user_id: number
  conversation_id?: number | null
  input_text?: string | null
  status?: string | null
  error?: string | null
  plan_id?: number | null
  replan_of_id?: number | null
  started_at?: string | null
  ended_at?: string | null
}

export interface AgentAction {
  id: number
  session_id: number
  agent_name?: string | null
  action?: string | null
  status?: string | null
  request?: string | null
  response?: string | null
  started_at?: string | null
  ended_at?: string | null
}

export interface UserInfo {
  id: number
  username: string
  nickname?: string | null
  email?: string | null
  avatar_url?: string | null
}

export interface AuthResult {
  token: string
  user: UserInfo
  preference: Preference | null
}

export interface Preference {
  user_id: number
  study_start?: string | null
  study_end?: string | null
  weekly_study_hours?: number | string | null
  monthly_budget?: number | string | null
  notification_enabled?: boolean | null
}

export interface AgentResult {
  agent: string
  ok: boolean
  text: string
  has_items: boolean
}

export interface ChatResult {
  ok: boolean
  conversation_id?: number | null
  agent_session_id?: number | null
  goal?: string | null
  answer?: string | null
  plan?: Plan | null
  agent_results?: AgentResult[]
  agent_status?: Record<string, string>
}

export interface CategoryStat {
  category: string
  cnt: number
  total: number | string
  avg_amount: number | string
}

export interface BudgetRow {
  id: number
  category?: string | null
  budget_amount: number | string
  spent: number | string
  remaining: number | string
  used_percent: number | string
}

export interface Budget {
  id: number
  user_id: number
  period_type: string
  period_start: string
  period_end: string
  category?: string | null
  amount: number | string
  created_at?: string
  updated_at?: string
}

export interface FinanceSummary {
  has_data: boolean
  expenses?: Expense[]
  by_category?: CategoryStat[]
  budget?: BudgetRow[]
  error?: string
}

export interface HealthInfo {
  mysql: boolean
  redis: boolean
  agents: Array<{ name?: string; display_name?: string }>
}
