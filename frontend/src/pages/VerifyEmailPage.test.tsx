import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { VerifyEmailPage } from './VerifyEmailPage'
import * as authApi from '../api/auth'
import * as authContext from '../context/AuthContext'

vi.mock('../api/auth')
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

function renderWithToken(token: string | null) {
  const initialPath = token ? `/verify-email?token=${token}` : '/verify-email'

  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/verify-email" element={<VerifyEmailPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('VerifyEmailPage', () => {
  it('verifies the token from the URL and shows success', async () => {
    mockAuth()
    vi.mocked(authApi.verifyEmail).mockResolvedValue(undefined)

    renderWithToken('a-real-token')

    expect(await screen.findByText('Your email has been verified.')).toBeInTheDocument()
    expect(authApi.verifyEmail).toHaveBeenCalledWith({ token: 'a-real-token' })
  })

  it('refreshes the cached user when already authenticated', async () => {
    const refreshUser = vi.fn().mockResolvedValue(undefined)
    mockAuth({ status: 'authenticated', refreshUser })
    vi.mocked(authApi.verifyEmail).mockResolvedValue(undefined)

    renderWithToken('a-real-token')

    await screen.findByText('Your email has been verified.')
    expect(refreshUser).toHaveBeenCalled()
  })

  it('shows the API error message on an invalid or expired token', async () => {
    mockAuth()
    vi.mocked(authApi.verifyEmail).mockRejectedValue(
      new Error('This verification link is invalid or has expired.'),
    )

    renderWithToken('a-stale-token')

    expect(
      await screen.findByText('This verification link is invalid or has expired.'),
    ).toBeInTheDocument()
  })

  it('shows a message when the URL has no token', () => {
    mockAuth()

    renderWithToken(null)

    expect(screen.getByText(/This verification link is missing its token/)).toBeInTheDocument()
    expect(authApi.verifyEmail).not.toHaveBeenCalled()
  })
})
