<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import type { Budget, Expense, FinanceSummary } from '../api/types'

const summary = ref<FinanceSummary | null>(null)
const expenses = ref<Expense[]>([])
const budgets = ref<Budget[]>([])
const loading = ref(false)
const error = ref('')

const form = reactive({ amount: '', category: '餐饮', note: '' })
const saving = ref(false)
const formError = ref('')

const budgetForm = reactive({ amount: '', period_type: 'monthly', category: '' })
const budgetSaving = ref(false)
const budgetError = ref('')

const CATEGORIES = ['餐饮', '学习', '交通', '娱乐', '生活', 'other']
const PERIODS = [
  { value: 'monthly', label: '月度' },
  { value: 'weekly', label: '周度' },
  { value: 'daily', label: '每日' },
]

const monthSpent = computed(() => {
  const cats = summary.value?.by_category ?? []
  return cats.reduce((sum, c) => sum + Number(c.total || 0), 0)
})

const maxCat = computed(() => {
  const cats = summary.value?.by_category ?? []
  return Math.max(1, ...cats.map((c) => Number(c.total || 0)))
})

async function loadAll() {
  loading.value = true
  error.value = ''
  try {
    const [fin, exp, bgt] = await Promise.all([
      api.financeSummary(),
      api.listExpenses(),
      api.listBudgets(),
    ])
    summary.value = fin
    expenses.value = exp
    budgets.value = bgt
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载财务数据失败'
  } finally {
    loading.value = false
  }
}

async function addBudget() {
  const amount = Number(budgetForm.amount)
  if (!budgetForm.amount || Number.isNaN(amount) || amount <= 0) {
    budgetError.value = '请输入有效的预算金额'
    return
  }
  budgetSaving.value = true
  budgetError.value = ''
  try {
    await api.addBudget({
      amount,
      period_type: budgetForm.period_type,
      category: budgetForm.category || null,
    })
    budgetForm.amount = ''
    budgetForm.category = ''
    await loadAll()
  } catch (err) {
    budgetError.value = err instanceof Error ? err.message : '保存预算失败'
  } finally {
    budgetSaving.value = false
  }
}

async function addExpense() {
  const amount = Number(form.amount)
  if (!form.amount || Number.isNaN(amount) || amount <= 0) {
    formError.value = '请输入有效金额'
    return
  }
  saving.value = true
  formError.value = ''
  try {
    await api.addExpense({
      amount,
      category: form.category,
      note: form.note || null,
    })
    form.amount = ''
    form.note = ''
    await loadAll()
  } catch (err) {
    formError.value = err instanceof Error ? err.message : '记账失败'
  } finally {
    saving.value = false
  }
}

onMounted(loadAll)
</script>

<template>
  <div>
    <div v-if="error" class="error-banner">{{ error }}</div>
    <div v-if="loading" class="empty">加载中…</div>

    <template v-else>
      <div class="grid cols-3">
        <div class="card">
          <h3>本月消费</h3>
          <div class="big-num">¥{{ monthSpent.toFixed(2) }}</div>
          <div class="muted">共 {{ (summary?.by_category || []).reduce((s, c) => s + c.cnt, 0) }} 笔</div>
        </div>

        <div class="card">
          <h3>分类占比</h3>
          <div v-if="summary?.by_category?.length">
            <div v-for="c in summary.by_category" :key="c.category" class="bar-row">
              <div class="bar-label">
                <span>{{ c.category }}</span>
                <span class="muted">¥{{ Number(c.total).toFixed(2) }}</span>
              </div>
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: (Number(c.total) / maxCat) * 100 + '%' }" />
              </div>
            </div>
          </div>
          <div v-else class="empty">本月暂无消费</div>
        </div>

        <div class="card">
          <h3>预算执行</h3>
          <table v-if="summary?.budget?.length" class="table">
            <thead>
              <tr><th>类别</th><th>预算</th><th>已用</th><th>使用率</th></tr>
            </thead>
            <tbody>
              <tr v-for="b in summary.budget" :key="b.id">
                <td>{{ b.category || '总预算' }}</td>
                <td>¥{{ Number(b.budget_amount).toFixed(2) }}</td>
                <td>¥{{ Number(b.spent).toFixed(2) }}</td>
                <td>
                  <span class="badge" :class="Number(b.used_percent) > 100 ? 'red' : 'green'">
                    {{ Number(b.used_percent).toFixed(0) }}%
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-else class="empty">暂无预算数据</div>
        </div>
      </div>

      <div class="grid cols-2" style="margin-top: 16px">
        <div class="card">
          <h3>消费记录</h3>
          <table v-if="expenses.length" class="table">
            <thead>
              <tr><th>时间</th><th>类别</th><th>金额</th><th>备注</th></tr>
            </thead>
            <tbody>
              <tr v-for="e in expenses" :key="e.id">
                <td>{{ e.paid_at.replace('T', ' ').slice(0, 16) }}</td>
                <td><span class="badge gray">{{ e.category }}</span></td>
                <td>¥{{ Number(e.amount).toFixed(2) }}</td>
                <td>{{ e.note || '—' }}</td>
              </tr>
            </tbody>
          </table>
          <div v-else class="empty">暂无消费记录</div>
        </div>

        <div class="card">
          <h3>记一笔</h3>
          <div v-if="formError" class="error-banner">{{ formError }}</div>
          <div class="field">
            <label>金额（元）*</label>
            <input v-model="form.amount" type="number" step="0.01" min="0" placeholder="0.00" />
          </div>
          <div class="field">
            <label>类别</label>
            <select v-model="form.category">
              <option v-for="c in CATEGORIES" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>
          <div class="field">
            <label>备注</label>
            <input v-model="form.note" placeholder="如：食堂午饭" />
          </div>
          <button class="btn primary" :disabled="saving" @click="addExpense">
            {{ saving ? '保存中…' : '保存' }}
          </button>
        </div>
      </div>

      <div class="grid cols-2" style="margin-top: 16px">
        <div class="card">
          <h3>预算设置</h3>
          <div v-if="budgetError" class="error-banner">{{ budgetError }}</div>
          <div class="field">
            <label>预算金额（元）*</label>
            <input v-model="budgetForm.amount" type="number" step="0.01" min="0" placeholder="0.00" />
          </div>
          <div class="grid cols-2">
            <div class="field">
              <label>周期</label>
              <select v-model="budgetForm.period_type">
                <option v-for="p in PERIODS" :key="p.value" :value="p.value">{{ p.label }}</option>
              </select>
            </div>
            <div class="field">
              <label>类别（空=总预算）</label>
              <select v-model="budgetForm.category">
                <option value="">总预算</option>
                <option v-for="c in CATEGORIES" :key="c" :value="c">{{ c }}</option>
              </select>
            </div>
          </div>
          <button class="btn primary" :disabled="budgetSaving" @click="addBudget">
            {{ budgetSaving ? '保存中…' : '保存预算' }}
          </button>
        </div>

        <div class="card">
          <h3>预算列表</h3>
          <table v-if="budgets.length" class="table">
            <thead>
              <tr><th>周期</th><th>起止</th><th>类别</th><th>金额</th></tr>
            </thead>
            <tbody>
              <tr v-for="b in budgets" :key="b.id">
                <td>{{ b.period_type }}</td>
                <td>{{ b.period_start }} ~ {{ b.period_end }}</td>
                <td>{{ b.category || '总预算' }}</td>
                <td>¥{{ Number(b.amount).toFixed(2) }}</td>
              </tr>
            </tbody>
          </table>
          <div v-else class="empty">暂无预算，请在左侧添加</div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.big-num {
  font-size: 30px;
  font-weight: 700;
  color: var(--primary);
}

.bar-row {
  margin-bottom: 10px;
}

.bar-label {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  margin-bottom: 4px;
}

.bar-track {
  height: 8px;
  background: #f3f4f6;
  border-radius: 999px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: var(--primary);
  border-radius: 999px;
}
</style>
