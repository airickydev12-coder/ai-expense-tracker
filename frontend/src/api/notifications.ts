import { apiGet, apiPost } from './client'
import type {
  NotificationCheckResponse,
  NotificationLogEntryResponse,
} from '../types/notifications'

export function getNotificationLog(): Promise<NotificationLogEntryResponse[]> {
  return apiGet<NotificationLogEntryResponse[]>('/notifications/log')
}

export function checkNotificationsNow(): Promise<NotificationCheckResponse> {
  return apiPost<NotificationCheckResponse>('/notifications/check-now', {})
}
