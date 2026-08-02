export interface RecommendationResponse {
  key: string
  priority: string
  category: string
  score: number
  title: string
  message: string
  action: string
  rationale: string
  source_rule: string
  is_actionable: boolean
}
