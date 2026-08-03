import { apiGet, apiPost } from './client'
import type {
  RecommendationCategoryResponse,
  RecommendationPriorityResponse,
  RecommendationRecordResponse,
  RecommendationResponse,
} from '../types/recommendations'

export function listRecommendationsByCategory(category: string): Promise<RecommendationResponse[]> {
  return apiGet<RecommendationResponse[]>(`/recommendations?category=${encodeURIComponent(category)}`)
}

export function listRecommendations(): Promise<RecommendationResponse[]> {
  return apiGet<RecommendationResponse[]>('/recommendations')
}

export function getFilteredRecommendations(filters: {
  category?: string
  priority?: string
}): Promise<RecommendationResponse[]> {
  const params = new URLSearchParams()
  if (filters.category) params.set('category', filters.category)
  if (filters.priority) params.set('priority', filters.priority)
  const query = params.toString()
  return apiGet<RecommendationResponse[]>(`/recommendations${query ? `?${query}` : ''}`)
}

export function getRecommendationCategories(): Promise<RecommendationCategoryResponse[]> {
  return apiGet<RecommendationCategoryResponse[]>('/recommendations/categories')
}

export function getRecommendationPriorities(): Promise<RecommendationPriorityResponse[]> {
  return apiGet<RecommendationPriorityResponse[]>('/recommendations/priorities')
}

export function dismissRecommendation(key: string, note = ''): Promise<RecommendationRecordResponse> {
  return apiPost<RecommendationRecordResponse>(`/recommendations/${encodeURIComponent(key)}/dismiss`, { note })
}

export function completeRecommendation(key: string, note = ''): Promise<RecommendationRecordResponse> {
  return apiPost<RecommendationRecordResponse>(`/recommendations/${encodeURIComponent(key)}/complete`, { note })
}

export function suppressRecommendation(key: string, note = ''): Promise<RecommendationRecordResponse> {
  return apiPost<RecommendationRecordResponse>(`/recommendations/${encodeURIComponent(key)}/suppress`, { note })
}
