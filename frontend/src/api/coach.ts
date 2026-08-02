import { apiGet } from './client'
import type { CoachingSessionDict, FinancialCoachInsightDict } from '../types/coach'

export function listInsights(): Promise<FinancialCoachInsightDict[]> {
  return apiGet<FinancialCoachInsightDict[]>('/coach/insights')
}

export function getCoachingSession(): Promise<CoachingSessionDict> {
  return apiGet<CoachingSessionDict>('/coach/session')
}
