export interface MetricProjectionResponse {
  metric: string
  current_value: number
  projected_value: number
  projected_change: number
  daily_change: number
  horizon_days: number
}

export interface FinancialForecastResponse {
  generated_at: string
  horizon_days: number
  history_points: number
  net_worth: MetricProjectionResponse
  cash_flow: MetricProjectionResponse
  account_balance: MetricProjectionResponse
  goal_progress: MetricProjectionResponse
  total_debt: MetricProjectionResponse
  health_score: MetricProjectionResponse
}
