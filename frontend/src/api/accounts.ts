import { apiDelete, apiGet, apiPost, apiPut } from './client'
import type {
  AccountCreateRequest,
  AccountResponse,
  AccountUpdateRequest,
} from '../types/accounts'

export function listAccounts(): Promise<AccountResponse[]> {
  return apiGet<AccountResponse[]>('/accounts')
}

export function createAccount(request: AccountCreateRequest): Promise<AccountResponse> {
  return apiPost<AccountResponse>('/accounts', request)
}

export function updateAccount(
  id: number,
  request: AccountUpdateRequest,
): Promise<AccountResponse> {
  return apiPut<AccountResponse>(`/accounts/${id}`, request)
}

export function deleteAccount(id: number): Promise<AccountResponse> {
  return apiDelete<AccountResponse>(`/accounts/${id}`)
}
