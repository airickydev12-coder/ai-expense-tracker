export interface FinancialCoachInsightDict {
  key: string
  title: string
  message: string
  category: string
  severity: 'Positive' | 'Informational' | 'Warning' | 'Critical'
  metric: string
  current_value: number | null
  benchmark_value: number | null
  action: string
}

export interface CoachingAdvice {
  key: string
  title: string
  message: string
  action: string
  reason: string
  priority: string
  category: string
  expected_impact: string
  source_scenario: string
  score: number | null
  warnings: string[]
}

export interface AdviceExplanation {
  advice_key: string
  summary: string
  why_it_matters: string
  projected_effects: string[]
  assumptions: string[]
  risks: string[]
}

export interface CoachingSessionDict {
  generated_at: string
  financial_health_score: number
  financial_health_status: string
  summary: string
  advice: CoachingAdvice[]
  explanations: AdviceExplanation[]
  insights: FinancialCoachInsightDict[]
  next_steps: string[]
  warnings: string[]
}

export interface CoachNarrativeDict {
  narrative: string
}

export interface RecommendationEvidenceDict {
  type: 'debt' | 'aggregate'
  debt_name: string | null
  debt_balance: number | null
  interest_rate: number | null
  minimum_payment: number | null
  extra_monthly_payment: number | null
  payoff_months_saved: number | null
  total_interest_saved: number | null
  total_debt: number
  total_income: number | null
  debt_to_income_ratio: number | null
  total_account_balance: number | null
  total_goal_progress: number | null
}

export interface RecommendationExplanationDict {
  recommendation_key: string
  reason: string
  evidence: RecommendationEvidenceDict
  expected_impact: string
  confidence: 'Low' | 'Medium' | 'High'
  assumptions: string[]
}

export interface MonthlyReviewSectionDict {
  narrative: string
}

export interface MonthlyReviewIncomeExpensesDict extends MonthlyReviewSectionDict {
  income_change: number
  expense_change: number
}

export interface MonthlyReviewCashFlowDict extends MonthlyReviewSectionDict {
  change: number
  direction: string
}

export interface MonthlyReviewDebtProgressDict extends MonthlyReviewSectionDict {
  total_debt: number
}

export interface MonthlyReviewHealthScoreDict extends MonthlyReviewSectionDict {
  change: number
  direction: string
  current_score: number
}

export interface MonthlyReviewNextActionDict {
  key: string
  title: string
  message: string
  action: string
  priority: string
}

export interface MonthlyReviewDict {
  status: 'ok' | 'no_history' | 'insufficient_recent_history'
  message: string | null
  last_recorded_snapshot: string | null
  period_start: string | null
  period_end: string | null
  overall_summary: string | null
  income_vs_expenses: MonthlyReviewIncomeExpensesDict | null
  cash_flow: MonthlyReviewCashFlowDict | null
  debt_progress: MonthlyReviewDebtProgressDict | null
  savings_progress: MonthlyReviewSectionDict | null
  goal_status: MonthlyReviewSectionDict | null
  health_score: MonthlyReviewHealthScoreDict | null
  top_actions: MonthlyReviewNextActionDict[] | null
  known_gaps: string[] | null
}

export interface CoachChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface CoachChatRequest {
  messages: CoachChatMessage[]
}

export interface CoachChatResponse {
  reply: string
}
