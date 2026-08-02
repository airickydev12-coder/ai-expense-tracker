export interface DebtResponse {
  id: number
  name: string
  balance: number
  interest_rate: number
  minimum_payment: number
}

export interface DebtCreateRequest {
  name: string
  balance: number
  interest_rate: number
  minimum_payment: number
}

export interface DebtUpdateRequest {
  name?: string
  balance?: number
  interest_rate?: number
  minimum_payment?: number
}

export interface DebtPaymentRequest {
  payment: number
}
