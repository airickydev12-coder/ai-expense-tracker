import { apiDelete, apiGet, apiPatch, apiPost, apiPut } from './client'
import type { BillCreateRequest, BillResponse, BillUpdateRequest } from '../types/bills'

export function listBills(): Promise<BillResponse[]> {
  return apiGet<BillResponse[]>('/bills')
}

export function createBill(request: BillCreateRequest): Promise<BillResponse> {
  return apiPost<BillResponse>('/bills', request)
}

export function updateBill(id: number, request: BillUpdateRequest): Promise<BillResponse> {
  return apiPut<BillResponse>(`/bills/${id}`, request)
}

export function deleteBill(id: number): Promise<BillResponse> {
  return apiDelete<BillResponse>(`/bills/${id}`)
}

export function payBill(id: number): Promise<BillResponse> {
  return apiPatch<BillResponse>(`/bills/${id}/pay`)
}

export function unpayBill(id: number): Promise<BillResponse> {
  return apiPatch<BillResponse>(`/bills/${id}/unpay`)
}
