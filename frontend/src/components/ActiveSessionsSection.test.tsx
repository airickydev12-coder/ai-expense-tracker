import { fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ActiveSessionsSection } from './ActiveSessionsSection'
import * as authApi from '../api/auth'
import type { SessionResponse } from '../types/auth'

vi.mock('../api/auth')

const currentSession: SessionResponse = {
  id: 1,
  issued_at: '2026-01-01T00:00:00Z',
  expires_at: '2026-01-31T00:00:00Z',
  user_agent: 'Mozilla/5.0 (current)',
  ip_address: '127.0.0.1',
  is_current: true,
}

const otherSession: SessionResponse = {
  id: 2,
  issued_at: '2026-01-02T00:00:00Z',
  expires_at: '2026-02-01T00:00:00Z',
  user_agent: 'Mozilla/5.0 (other)',
  ip_address: '10.0.0.5',
  is_current: false,
}

afterEach(() => {
  vi.restoreAllMocks()
  vi.clearAllMocks()
})

describe('ActiveSessionsSection', () => {
  it('renders the session list once loaded', async () => {
    vi.mocked(authApi.listSessions).mockResolvedValue([currentSession, otherSession])

    render(<ActiveSessionsSection />)

    expect(await screen.findByText('Mozilla/5.0 (current)')).toBeInTheDocument()
    expect(screen.getByText('Mozilla/5.0 (other)')).toBeInTheDocument()
    expect(screen.getByText('(this device)')).toBeInTheDocument()
  })

  it('disables revoking the current session', async () => {
    vi.mocked(authApi.listSessions).mockResolvedValue([currentSession])

    render(<ActiveSessionsSection />)
    const row = (await screen.findByText('Mozilla/5.0 (current)')).closest('li') as HTMLElement

    expect(within(row).getByRole('button', { name: 'Revoke' })).toBeDisabled()
  })

  it('revokes another session after confirmation', async () => {
    vi.mocked(authApi.listSessions).mockResolvedValue([currentSession, otherSession])
    vi.mocked(authApi.revokeSession).mockResolvedValue(undefined)
    vi.spyOn(window, 'confirm').mockReturnValue(true)

    render(<ActiveSessionsSection />)
    const row = (await screen.findByText('Mozilla/5.0 (other)')).closest('li') as HTMLElement

    fireEvent.click(within(row).getByRole('button', { name: 'Revoke' }))

    expect(authApi.revokeSession).toHaveBeenCalledWith(2)
  })

  it('does not revoke when the confirmation is declined', async () => {
    vi.mocked(authApi.listSessions).mockResolvedValue([currentSession, otherSession])
    vi.spyOn(window, 'confirm').mockReturnValue(false)

    render(<ActiveSessionsSection />)
    const row = (await screen.findByText('Mozilla/5.0 (other)')).closest('li') as HTMLElement

    fireEvent.click(within(row).getByRole('button', { name: 'Revoke' }))

    expect(authApi.revokeSession).not.toHaveBeenCalled()
  })

  it('hides the "log out of all devices" button when there are no sessions', async () => {
    vi.mocked(authApi.listSessions).mockResolvedValue([])

    render(<ActiveSessionsSection />)

    expect(await screen.findByText('Active Sessions')).toBeInTheDocument()
    expect(
      screen.queryByRole('button', { name: 'Log out of all devices' }),
    ).not.toBeInTheDocument()
  })

  it('renders an error message when the list fails to load', async () => {
    vi.mocked(authApi.listSessions).mockRejectedValue(new Error('Network error'))

    render(<ActiveSessionsSection />)

    expect(await screen.findByText(/Failed to load sessions/i)).toBeInTheDocument()
  })
})
