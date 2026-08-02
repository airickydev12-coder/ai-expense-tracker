export interface FinancialSnapshotResponse {
  timestamp: string
  total_income: number
  total_expenses: number
  net_cash_flow: number
  total_account_balance: number
  total_goal_progress: number
  total_debt: number
  net_worth: number
  health_score: number
  health_status: string
}

export type TrendDirection = 'Improving' | 'Declining' | 'Stable' | 'Insufficient Data'
export type OverallMomentum = 'Positive' | 'Negative' | 'Stable' | 'Insufficient Data'

export interface MetricTrend {
  direction: TrendDirection
  change: number
}

export interface TrendSummary {
  net_worth: MetricTrend
  cash_flow: MetricTrend
  income: MetricTrend
  expenses: MetricTrend
  health_score: MetricTrend
  overall_momentum: OverallMomentum
}
