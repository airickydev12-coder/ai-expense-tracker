import { apiGet, apiPatch, apiPost } from './client'
import type { AdminOverviewResponse, AssignRoleRequest, UpdateUserActiveRequest } from '../types/admin'
import type { UserResponse } from '../types/auth'

export function getAdminOverview(): Promise<AdminOverviewResponse> {
  return apiGet<AdminOverviewResponse>('/admin/overview')
}

export function listUsers(): Promise<UserResponse[]> {
  return apiGet<UserResponse[]>('/admin/users')
}

export function setUserActive(userId: number, request: UpdateUserActiveRequest): Promise<UserResponse> {
  return apiPatch<UserResponse>(`/admin/users/${userId}/active`, request)
}

export function assignUserRole(userId: number, request: AssignRoleRequest): Promise<UserResponse> {
  return apiPatch<UserResponse>(`/admin/users/${userId}/role`, request)
}

export function revokeUserSessions(userId: number): Promise<void> {
  return apiPost<void>(`/admin/users/${userId}/revoke-sessions`, undefined)
}
