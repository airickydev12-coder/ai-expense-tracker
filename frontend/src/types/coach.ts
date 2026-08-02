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
