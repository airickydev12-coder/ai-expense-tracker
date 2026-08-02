import { apiDelete, apiGet, apiPost, apiPut } from './client'
import type {
  GoalCreateRequest,
  GoalLedgerEntryResponse,
  GoalLedgerOperationRequest,
  GoalReconcileResponse,
  GoalResponse,
  GoalReversalRequest,
  GoalUpdateRequest,
} from '../types/goals'

export function listGoals(): Promise<GoalResponse[]> {
  return apiGet<GoalResponse[]>('/goals')
}

export function createGoal(request: GoalCreateRequest): Promise<GoalResponse> {
  return apiPost<GoalResponse>('/goals', request)
}

export function updateGoal(id: number, request: GoalUpdateRequest): Promise<GoalResponse> {
  return apiPut<GoalResponse>(`/goals/${id}`, request)
}

export function deleteGoal(id: number): Promise<GoalResponse> {
  return apiDelete<GoalResponse>(`/goals/${id}`)
}

export function contributeToGoal(
  id: number,
  request: GoalLedgerOperationRequest,
): Promise<GoalResponse> {
  return apiPost<GoalResponse>(`/goals/${id}/contributions`, request)
}

export function withdrawFromGoal(
  id: number,
  request: GoalLedgerOperationRequest,
): Promise<GoalResponse> {
  return apiPost<GoalResponse>(`/goals/${id}/withdrawals`, request)
}

export function adjustGoalBalance(
  id: number,
  request: GoalLedgerOperationRequest,
): Promise<GoalResponse> {
  return apiPost<GoalResponse>(`/goals/${id}/adjustments`, request)
}

export function reverseGoalLedgerEntry(
  id: number,
  request: GoalReversalRequest,
): Promise<GoalResponse> {
  return apiPost<GoalResponse>(`/goals/${id}/reversals`, request)
}

export function getGoalLedgerEntries(id: number): Promise<GoalLedgerEntryResponse[]> {
  return apiGet<GoalLedgerEntryResponse[]>(`/goals/${id}/ledger`)
}

export function reconcileGoal(id: number): Promise<GoalReconcileResponse> {
  return apiGet<GoalReconcileResponse>(`/goals/${id}/reconcile`)
}
