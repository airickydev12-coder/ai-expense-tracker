import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
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
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

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
})
