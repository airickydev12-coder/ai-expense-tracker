import { apiDelete, apiGet, apiPost, apiPut } from './client'
import type { IncomeCreateRequest, IncomeResponse, IncomeUpdateRequest } from '../types/income'

export function listIncome(): Promise<IncomeResponse[]> {
  return apiGet<IncomeResponse[]>('/income')
}

export function createIncome(request: IncomeCreateRequest): Promise<IncomeResponse> {
  return apiPost<IncomeResponse>('/income', request)
}

export function updateIncome(id: number, request: IncomeUpdateRequest): Promise<IncomeResponse> {
  return apiPut<IncomeResponse>(`/income/${id}`, request)
}

export function deleteIncome(id: number): Promise<IncomeResponse> {
  return apiDelete<IncomeResponse>(`/income/${id}`)
}
