import { apiDelete, apiGet, apiPost, apiPut } from './client'
import type {
  ExpenseCreateRequest,
  ExpenseResponse,
  ExpenseUpdateRequest,
} from '../types/expenses'

export function listExpenses(): Promise<ExpenseResponse[]> {
  return apiGet<ExpenseResponse[]>('/expenses')
}

export function createExpense(request: ExpenseCreateRequest): Promise<ExpenseResponse> {
  return apiPost<ExpenseResponse>('/expenses', request)
}

export function updateExpense(
  id: number,
  request: ExpenseUpdateRequest,
): Promise<ExpenseResponse> {
  return apiPut<ExpenseResponse>(`/expenses/${id}`, request)
}

export function deleteExpense(id: number): Promise<ExpenseResponse> {
  return apiDelete<ExpenseResponse>(`/expenses/${id}`)
}
