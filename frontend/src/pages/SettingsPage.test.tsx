import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { SettingsPage } from './SettingsPage'
import * as authApi from '../api/auth'
import * as authContext from '../context/AuthContext'

vi.mock('../api/auth')
vi.mock('../context/AuthContext')

const alice = {
  id: 1,
  username: 'alice',
  email: 'alice@example.com',
  is_active: true,
  role: 'user' as const,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  email_verified: true,
}

beforeEach(() => {
  // SettingsPage now also renders ActiveSessionsSection, which fetches the
  // session list on mount -- every test needs a default so that fetch
  // doesn't reject with "undefined is not a function" (auto-mocked
  // functions have no implementation until one is set).
  vi.mocked(authApi.listSessions).mockResolvedValue([])
})

afterEach(() => {
  vi.restoreAllMocks()
  vi.clearAllMocks()
})

function mockAuth(overrides: Partial<ReturnType<typeof authContext.useAuth>> = {}) {
  vi.mocked(authContext.useAuth).mockReturnValue({
    status: 'authenticated',
    user: alice,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    refreshUser: vi.fn(),
    ...overrides,
  })
}

describe('SettingsPage', () => {
  it('pre-fills the form with the current user', () => {
    mockAuth()

    render(<SettingsPage />)

    expect(screen.getByLabelText('Username')).toHaveValue('alice')
    expect(screen.getByLabelText('Email')).toHaveValue('alice@example.com')
  })

  it('submits the updated profile and refreshes the user', async () => {
    const refreshUser = vi.fn().mockResolvedValue(undefined)
    mockAuth({ refreshUser })
    vi.mocked(authApi.updateProfile).mockResolvedValue({ ...alice, username: 'alice2' })

    render(<SettingsPage />)

    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'alice2' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save Changes' }))

    expect(await screen.findByText('Profile updated successfully.')).toBeInTheDocument()
    expect(authApi.updateProfile).toHaveBeenCalledWith({
      username: 'alice2',
      email: 'alice@example.com',
    })
    expect(refreshUser).toHaveBeenCalled()
  })

  it('shows a validation error for a too-short username', () => {
    mockAuth()

    render(<SettingsPage />)

    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'ab' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save Changes' }))

    expect(screen.getByText('Username must be between 3 and 50 characters.')).toBeInTheDocument()
  })

  it('shows the API error message on failure', async () => {
    mockAuth()
    vi.mocked(authApi.updateProfile).mockRejectedValue(
      new Error("Username 'bob' or email 'alice@example.com' is already registered."),
    )

    render(<SettingsPage />)

    fireEvent.click(screen.getByRole('button', { name: 'Save Changes' }))

    expect(
      await screen.findByText("Username 'bob' or email 'alice@example.com' is already registered."),
    ).toBeInTheDocument()
  })

  it('submits a password change', async () => {
    mockAuth()
    vi.mocked(authApi.changePassword).mockResolvedValue(undefined)

    render(<SettingsPage />)

    fireEvent.change(screen.getByLabelText('Current Password'), {
      target: { value: 'correct-password' },
    })
    fireEvent.change(screen.getByLabelText('New Password'), { target: { value: 'new-password' } })
    fireEvent.click(screen.getByRole('button', { name: 'Change Password' }))

    expect(await screen.findByText('Password changed successfully.')).toBeInTheDocument()
    expect(authApi.changePassword).toHaveBeenCalledWith({
      current_password: 'correct-password',
      new_password: 'new-password',
    })
  })

  it('rejects a new password that is too short', () => {
    mockAuth()

    render(<SettingsPage />)

    fireEvent.change(screen.getByLabelText('Current Password'), {
      target: { value: 'correct-password' },
    })
    fireEvent.change(screen.getByLabelText('New Password'), { target: { value: 'short' } })
    fireEvent.click(screen.getByRole('button', { name: 'Change Password' }))

    expect(screen.getByText('New password must be between 8 and 128 characters.')).toBeInTheDocument()
  })

  it('shows the API error message when the current password is wrong', async () => {
    mockAuth()
    vi.mocked(authApi.changePassword).mockRejectedValue(new Error('Current password is incorrect.'))

    render(<SettingsPage />)

    fireEvent.change(screen.getByLabelText('Current Password'), { target: { value: 'wrong' } })
    fireEvent.change(screen.getByLabelText('New Password'), { target: { value: 'new-password' } })
    fireEvent.click(screen.getByRole('button', { name: 'Change Password' }))

    expect(await screen.findByText('Current password is incorrect.')).toBeInTheDocument()
  })
})
