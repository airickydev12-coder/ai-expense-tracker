import type { PlatformRole } from './auth'

export interface AdminOverviewResponse {
  message: string
  admin_username: string
  admin_role: PlatformRole
}

export interface UpdateUserActiveRequest {
  is_active: boolean
}

export interface AssignRoleRequest {
  role: PlatformRole
}
