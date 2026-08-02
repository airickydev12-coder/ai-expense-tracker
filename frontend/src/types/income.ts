export interface IncomeResponse {
  id: number
  source: string
  amount: number
}

export interface IncomeCreateRequest {
  source: string
  amount: number
}

export interface IncomeUpdateRequest {
  source?: string
  amount?: number
}
