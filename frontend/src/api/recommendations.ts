import { apiGet } from './client'
import type { RecommendationResponse } from '../types/recommendations'

export function listRecommendationsByCategory(category: string): Promise<RecommendationResponse[]> {
  return apiGet<RecommendationResponse[]>(`/recommendations?category=${encodeURIComponent(category)}`)
}

export function listRecommendations(): Promise<RecommendationResponse[]> {
  return apiGet<RecommendationResponse[]>('/recommendations')
}
