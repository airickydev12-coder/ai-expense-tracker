import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { NotificationsPage } from './NotificationsPage'
import * as notificationsApi from '../api/notifications'

vi.mock('../api/notifications')

const sentEntry = {
  id: 1,
  notification_key: 'bill_due:1:2026-09-01',
  channel: 'EMAIL',
  subject: 'Financial Tracker: 1 item(s) need your attention',
  body: 'Bill due soon: Electric ($125.00, due day 15)',
  sent_at: '2026-09-01T12:00:00+00:00',
  status: 'SENT',
} as const

afterEach(() => {
  vi.restoreAllMocks()
  vi.clearAllMocks()
})

describe('NotificationsPage', () => {
  it('renders the notification log once loaded', async () => {
    vi.mocked(notificationsApi.getNotificationLog).mockResolvedValue([sentEntry])

    render(<NotificationsPage />)

    expect(await screen.findByText(sentEntry.subject)).toBeInTheDocument()
    expect(screen.getByText('SENT')).toBeInTheDocument()
  })

  it('renders an empty state when there are no logged notifications', async () => {
    vi.mocked(notificationsApi.getNotificationLog).mockResolvedValue([])

    render(<NotificationsPage />)

    expect(await screen.findByText('No notifications logged yet.')).toBeInTheDocument()
  })

  it('checks now and shows a confirmation message with new entries', async () => {
    vi.mocked(notificationsApi.getNotificationLog).mockResolvedValue([])
    vi.mocked(notificationsApi.checkNotificationsNow).mockResolvedValue({
      new_entry_count: 1,
      entries: [sentEntry],
    })

    render(<NotificationsPage />)

    await screen.findByText('No notifications logged yet.')
    fireEvent.click(screen.getByRole('button', { name: 'Check Now' }))

    expect(await screen.findByText('1 new notification(s).')).toBeInTheDocument()
  })

  it('checks now and reports when nothing new was found', async () => {
    vi.mocked(notificationsApi.getNotificationLog).mockResolvedValue([])
    vi.mocked(notificationsApi.checkNotificationsNow).mockResolvedValue({
      new_entry_count: 0,
      entries: [],
    })

    render(<NotificationsPage />)

    await screen.findByText('No notifications logged yet.')
    fireEvent.click(screen.getByRole('button', { name: 'Check Now' }))

    expect(await screen.findByText('No new notifications right now.')).toBeInTheDocument()
  })

  it('renders an error message when the log fails to load', async () => {
    vi.mocked(notificationsApi.getNotificationLog).mockRejectedValue(new Error('Network error'))

    render(<NotificationsPage />)

    expect(await screen.findByText(/Failed to load notifications/i)).toBeInTheDocument()
  })
})
