import { apiGet, apiPost } from './client'
import type {
  CoachChatRequest,
  CoachChatResponse,
  CoachingSessionDict,
  FinancialCoachInsightDict,
} from '../types/coach'

export function listInsights(): Promise<FinancialCoachInsightDict[]> {
  return apiGet<FinancialCoachInsightDict[]>('/coach/insights')
}

export function getCoachingSession(): Promise<CoachingSessionDict> {
  return apiGet<CoachingSessionDict>('/coach/session')
}

export function sendChatMessage(request: CoachChatRequest): Promise<CoachChatResponse> {
  return apiPost<CoachChatResponse>('/coach/chat', request)
}
