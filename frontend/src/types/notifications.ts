export interface NotificationLogEntryResponse {
  id: number
  notification_key: string
  channel: string
  subject: string
  body: string
  sent_at: string
  status: string
}

export interface NotificationCheckResponse {
  new_entry_count: number
  entries: NotificationLogEntryResponse[]
}
