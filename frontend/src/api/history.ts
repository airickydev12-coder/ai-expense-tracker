import { apiGet, apiPost } from './client'
import type { FinancialSnapshotResponse, TrendSummary } from '../types/history'

export function listHistory(): Promise<FinancialSnapshotResponse[]> {
  return apiGet<FinancialSnapshotResponse[]>('/history')
}

export function getLatestSnapshot(): Promise<FinancialSnapshotResponse> {
  return apiGet<FinancialSnapshotResponse>('/history/latest')
}

export function getTrends(): Promise<TrendSummary> {
  return apiGet<TrendSummary>('/history/trends')
}

export function recordSnapshot(): Promise<FinancialSnapshotResponse> {
  return apiPost<FinancialSnapshotResponse>('/history/snapshot', undefined)
}
