import { apiDelete, apiGet, apiPost } from './client'
import type {
  CoachChatRequest,
  CoachChatResponse,
  CoachingSessionDict,
  CoachNarrativeDict,
  FinancialCoachInsightDict,
  MonthlyReviewDict,
  RecommendationExplanationDict,
  SavedNoteDict,
} from '../types/coach'

export function listInsights(): Promise<FinancialCoachInsightDict[]> {
  return apiGet<FinancialCoachInsightDict[]>('/coach/insights')
}

export function getCoachingSession(): Promise<CoachingSessionDict> {
  return apiGet<CoachingSessionDict>('/coach/session')
}

export function getFinancialNarrative(): Promise<CoachNarrativeDict> {
  return apiGet<CoachNarrativeDict>('/coach/narrative')
}

export function explainRecommendation(key: string): Promise<RecommendationExplanationDict> {
  return apiGet<RecommendationExplanationDict>(
    `/coach/recommendations/${encodeURIComponent(key)}/explanation`,
  )
}

export function getMonthlyReview(): Promise<MonthlyReviewDict> {
  return apiGet<MonthlyReviewDict>('/coach/monthly-review')
}

export function saveMonthlyReview(): Promise<MonthlyReviewDict> {
  return apiPost<MonthlyReviewDict>('/coach/monthly-review', {})
}

export function sendChatMessage(request: CoachChatRequest): Promise<CoachChatResponse> {
  return apiPost<CoachChatResponse>('/coach/chat', request)
}

export function listNotes(): Promise<SavedNoteDict[]> {
  return apiGet<SavedNoteDict[]>('/coach/notes')
}

export function saveNote(title: string, content: string): Promise<SavedNoteDict> {
  return apiPost<SavedNoteDict>('/coach/notes', { title, content })
}

export function deleteNote(noteId: number): Promise<SavedNoteDict> {
  return apiDelete<SavedNoteDict>(`/coach/notes/${noteId}`)
}
