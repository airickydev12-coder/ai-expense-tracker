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
    register: vi.fn(),
    logout: vi.fn(),
    ...overrides,
  })
}

describe('LoginPage', () => {
  it('submits the form and navigates to the dashboard on success', async () => {
    const login = vi.fn().mockResolvedValue(undefined)
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
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      },
    })

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    )

    expect(screen.queryByRole('button', { name: 'Log In' })).not.toBeInTheDocument()
  })
})
