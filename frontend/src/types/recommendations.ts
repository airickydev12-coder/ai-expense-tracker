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

export interface RecommendationCategoryResponse {
  name: string
  value: string
}

export interface RecommendationPriorityResponse {
  name: string
  value: number
  score: number
}

export interface RecommendationRecordResponse {
  recommendation_key: string
  status: string
  created_at: string
  updated_at: string
  note: string
}
