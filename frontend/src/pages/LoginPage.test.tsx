import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { LoginPage } from './LoginPage'
import * as authContext from '../context/AuthContext'

vi.mock('../context/AuthContext')

afterEach(() => {
  vi.restoreAllMocks()
  vi.clearAllMocks()
})

function mockAuth(overrides: Partial<ReturnType<typeof authContext.useAuth>> = {}) {
  vi.mocked(authContext.useAuth).mockReturnValue({
    status: 'unauthenticated',
    user: null,
    login: vi.fn(),
    verifyMfa: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    refreshUser: vi.fn(),
    ...overrides,
  })
}

describe('LoginPage', () => {
  it('submits the form and navigates to the dashboard on success', async () => {
    const login = vi.fn().mockResolvedValue({ status: 'authenticated' })
    mockAuth({ login })

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    )

    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'alice' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'correct-password' } })
    fireEvent.click(screen.getByRole('button', { name: 'Log In' }))

    expect(login).toHaveBeenCalledWith('alice', 'correct-password')
  })

  it('shows a validation error when fields are empty', () => {
    mockAuth()

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Log In' }))

    expect(screen.getByText('Username and password are required.')).toBeInTheDocument()
  })

  it('shows the API error message on failed login', async () => {
    const login = vi.fn().mockRejectedValue(new Error('Invalid username or password.'))
    mockAuth({ login })

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    )

    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'alice' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'wrong' } })
    fireEvent.click(screen.getByRole('button', { name: 'Log In' }))

    expect(await screen.findByText('Invalid username or password.')).toBeInTheDocument()
  })

  it('redirects to the dashboard if already authenticated', () => {
    mockAuth({
      status: 'authenticated',
      user: {
        id: 1,
        username: 'alice',
        email: 'alice@example.com',
        is_active: true,
        role: 'user',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
        email_verified: true,
        mfa_enabled: false,
        account_type: 'adult',
      },
    })

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    )

    expect(screen.queryByRole('button', { name: 'Log In' })).not.toBeInTheDocument()
  })

  it('shows the MFA code step when login requires a challenge', async () => {
    const login = vi
      .fn()
      .mockResolvedValue({ status: 'mfa_required', challengeToken: 'a-challenge-token' })
    mockAuth({ login })

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    )

    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'alice' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'correct-password' } })
    fireEvent.click(screen.getByRole('button', { name: 'Log In' }))

    expect(await screen.findByText('Two-Factor Authentication')).toBeInTheDocument()
  })

  it('submits the MFA code to verifyMfa', async () => {
    const login = vi
      .fn()
      .mockResolvedValue({ status: 'mfa_required', challengeToken: 'a-challenge-token' })
    const verifyMfa = vi.fn().mockResolvedValue(undefined)
    mockAuth({ login, verifyMfa })

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    )

    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'alice' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'correct-password' } })
    fireEvent.click(screen.getByRole('button', { name: 'Log In' }))
    await screen.findByText('Two-Factor Authentication')

    fireEvent.change(screen.getByLabelText('Authentication code or recovery code'), {
      target: { value: '123456' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Verify' }))

    expect(verifyMfa).toHaveBeenCalledWith('a-challenge-token', '123456')
  })

  it('shows the API error message on a wrong MFA code', async () => {
    const login = vi
      .fn()
      .mockResolvedValue({ status: 'mfa_required', challengeToken: 'a-challenge-token' })
    const verifyMfa = vi.fn().mockRejectedValue(new Error('Invalid authentication code.'))
    mockAuth({ login, verifyMfa })

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    )

    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'alice' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'correct-password' } })
    fireEvent.click(screen.getByRole('button', { name: 'Log In' }))
    await screen.findByText('Two-Factor Authentication')

    fireEvent.change(screen.getByLabelText('Authentication code or recovery code'), {
      target: { value: '000000' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Verify' }))

    expect(await screen.findByText('Invalid authentication code.')).toBeInTheDocument()
  })
})
