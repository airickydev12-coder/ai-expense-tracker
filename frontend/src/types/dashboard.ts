import type { ExpenseResponse } from './expenses'

export interface DashboardResponse {
  total_expenses: number
  average_expense: number
  highest_expense: ExpenseResponse | null
  lowest_expense: ExpenseResponse | null
  category_totals: Record<string, number>
  budget_count: number
  monthly_budget: number
  remaining_budget: number
  budget_used_percent: number
  recommendation_count: number
  health_score: number
  health_status: string
}
