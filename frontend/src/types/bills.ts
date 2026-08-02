export interface BillResponse {
  id: number
  name: string
  amount: number
  due_day: number
  is_paid: boolean
}

export interface BillCreateRequest {
  name: string
  amount: number
  due_day: number
  is_paid?: boolean
}

export interface BillUpdateRequest {
  name?: string
  amount?: number
  due_day?: number
  is_paid?: boolean
}
