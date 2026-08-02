import { apiDelete, apiGet, apiPost, apiPut } from './client'
import type { DebtCreateRequest, DebtResponse, DebtUpdateRequest } from '../types/debt'

export function listDebts(): Promise<DebtResponse[]> {
  return apiGet<DebtResponse[]>('/debts')
}

export function createDebt(request: DebtCreateRequest): Promise<DebtResponse> {
  return apiPost<DebtResponse>('/debts', request)
}

export function updateDebt(id: number, request: DebtUpdateRequest): Promise<DebtResponse> {
  return apiPut<DebtResponse>(`/debts/${id}`, request)
}

export function deleteDebt(id: number): Promise<DebtResponse> {
  return apiDelete<DebtResponse>(`/debts/${id}`)
}

export function applyDebtPayment(id: number, payment: number): Promise<DebtResponse> {
  return apiPost<DebtResponse>(`/debts/${id}/payments`, { payment })
}
