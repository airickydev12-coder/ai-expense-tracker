import { apiGet } from './client'
import type { DashboardResponse } from '../types/dashboard'

export function getDashboard(): Promise<DashboardResponse> {
  return apiGet<DashboardResponse>('/dashboard')
}
