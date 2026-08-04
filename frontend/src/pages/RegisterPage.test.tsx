import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { RegisterPage } from './RegisterPage'
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
    refreshUser: vi.fn(),
    ...overrides,
  })
}

describe('RegisterPage', () => {
  it('submits the form and navigates to the dashboard on success', async () => {
    const register = vi.fn().mockResolvedValue(undefined)
    mockAuth({ register })

    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>,
    )

    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'alice' } })
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'alice@example.com' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'correct-password' } })
    fireEvent.click(screen.getByRole('button', { name: 'Register' }))

    expect(register).toHaveBeenCalledWith('alice', 'alice@example.com', 'correct-password')
  })

  it('rejects a username that is too short', () => {
    mockAuth()

    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>,
    )

    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'ab' } })
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'alice@example.com' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'correct-password' } })
    fireEvent.click(screen.getByRole('button', { name: 'Register' }))

    expect(screen.getByText('Username must be between 3 and 50 characters.')).toBeInTheDocument()
  })

  it('rejects a password that is too short', () => {
    mockAuth()

    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>,
    )

    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'alice' } })
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'alice@example.com' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'short' } })
    fireEvent.click(screen.getByRole('button', { name: 'Register' }))

    expect(screen.getByText('Password must be between 8 and 128 characters.')).toBeInTheDocument()
  })

  it('shows the API error message on failed registration', async () => {
    const register = vi.fn().mockRejectedValue(new Error("Username 'alice' or email 'alice@example.com' is already registered."))
    mockAuth({ register })

    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>,
    )

    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'alice' } })
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'alice@example.com' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'correct-password' } })
    fireEvent.click(screen.getByRole('button', { name: 'Register' }))

    expect(
      await screen.findByText("Username 'alice' or email 'alice@example.com' is already registered."),
    ).toBeInTheDocument()
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
        <RegisterPage />
      </MemoryRouter>,
    )

    expect(screen.queryByRole('button', { name: 'Register' })).not.toBeInTheDocument()
  })
})
