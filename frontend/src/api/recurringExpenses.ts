import { apiDelete, apiGet, apiPost, apiPut } from './client'
import type {
  GeneratedExpensesResponse,
  RecurringExpenseTemplateCreateRequest,
  RecurringExpenseTemplateResponse,
  RecurringExpenseTemplateUpdateRequest,
} from '../types/recurringExpenses'

export function listRecurringExpenseTemplates(): Promise<RecurringExpenseTemplateResponse[]> {
  return apiGet<RecurringExpenseTemplateResponse[]>('/recurring-expenses')
}

export function createRecurringExpenseTemplate(
  request: RecurringExpenseTemplateCreateRequest,
): Promise<RecurringExpenseTemplateResponse> {
  return apiPost<RecurringExpenseTemplateResponse>('/recurring-expenses', request)
}

export function updateRecurringExpenseTemplate(
  id: number,
  request: RecurringExpenseTemplateUpdateRequest,
): Promise<RecurringExpenseTemplateResponse> {
  return apiPut<RecurringExpenseTemplateResponse>(`/recurring-expenses/${id}`, request)
}

export function deleteRecurringExpenseTemplate(id: number): Promise<RecurringExpenseTemplateResponse> {
  return apiDelete<RecurringExpenseTemplateResponse>(`/recurring-expenses/${id}`)
}

export function generateDueExpenses(): Promise<GeneratedExpensesResponse> {
  return apiPost<GeneratedExpensesResponse>('/recurring-expenses/generate', {})
}
