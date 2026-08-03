import type { ExpenseCategory } from './expenses'

export const RECURRENCE_FREQUENCIES = ['WEEKLY', 'BIWEEKLY', 'MONTHLY', 'YEARLY'] as const
export type RecurrenceFrequency = (typeof RECURRENCE_FREQUENCIES)[number]

export interface RecurringExpenseTemplateResponse {
  id: number
  name: string
  category: ExpenseCategory
  amount: number
  frequency: RecurrenceFrequency
  next_occurrence: string
  is_active: boolean
}

export interface RecurringExpenseTemplateCreateRequest {
  name: string
  category: ExpenseCategory
  amount: number
  frequency: RecurrenceFrequency
  next_occurrence: string
  is_active?: boolean
}

export interface RecurringExpenseTemplateUpdateRequest {
  name?: string
  category?: ExpenseCategory
  amount?: number
  frequency?: RecurrenceFrequency
  next_occurrence?: string
  is_active?: boolean
}

export interface GeneratedExpensesResponse {
  generated_count: number
  expense_ids: number[]
}
