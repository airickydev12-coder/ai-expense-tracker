export const EXPENSE_CATEGORIES = [
  'Food',
  'Transportation',
  'Housing',
  'Utilities',
  'Healthcare',
  'Clothing',
  'Maintenance',
  'Entertainment',
  'Education',
  'Insurance',
  'Savings',
  'Other',
] as const

export type ExpenseCategory = (typeof EXPENSE_CATEGORIES)[number]

export interface ExpenseResponse {
  id: number
  name: string
  category: ExpenseCategory
  amount: number
}

export interface ExpenseCreateRequest {
  name: string
  category: ExpenseCategory
  amount: number
}

export interface ExpenseUpdateRequest {
  name?: string
  category?: ExpenseCategory
  amount?: number
}
