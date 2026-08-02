export interface AccountResponse {
  id: number
  name: string
  account_type: string
  balance: number
}

export interface AccountCreateRequest {
  name: string
  account_type: string
  balance: number
}

export interface AccountUpdateRequest {
  name?: string
  account_type?: string
  balance?: number
}
