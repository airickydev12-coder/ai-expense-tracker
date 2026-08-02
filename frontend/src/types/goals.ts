export interface GoalResponse {
  id: number
  name: string
  target_amount: number
  current_amount: number
}

export interface GoalCreateRequest {
  name: string
  target_amount: number
  current_amount?: number
}

export interface GoalUpdateRequest {
  name?: string
  target_amount?: number
  current_amount?: number
}

export interface GoalLedgerOperationRequest {
  amount: number
  effective_date?: string
  source?: string
  note?: string
  correlation_id?: string
}

export interface GoalReversalRequest {
  entry_id: string
  effective_date?: string
  source?: string
  note?: string
  correlation_id?: string
}

export type GoalLedgerEntryType =
  | 'OPENING_BALANCE'
  | 'CONTRIBUTION'
  | 'WITHDRAWAL'
  | 'ADJUSTMENT'
  | 'REVERSAL'

export interface GoalLedgerEntryResponse {
  entry_id: string
  goal_id: number
  entry_type: GoalLedgerEntryType
  amount: number
  effective_date: string
  created_at: string
  source: string
  note: string
  correlation_id: string | null
  reverses_entry_id: string | null
}

export interface GoalReconcileResponse {
  is_reconciled: boolean
  ledger_balance: number
}
