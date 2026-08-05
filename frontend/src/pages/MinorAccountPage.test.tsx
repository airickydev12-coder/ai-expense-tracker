import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { MinorAccountPage } from './MinorAccountPage'
import * as authContext from '../context/AuthContext'
import type { AccountType, UserResponse } from '../types/auth'

vi.mock('../context/AuthContext')

afterEach(() => {
  vi.restoreAllMocks()
  vi.clearAllMocks()
})

function buildUser(accountType: AccountType): UserResponse {
  return {
    id: 1,
    username: 'kiddo',
    email: 'kiddo@example.com',
    is_active: true,
    role: 'user',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    email_verified: true,
    mfa_enabled: false,
    account_type: accountType,
  }
}

function mockAuth(user: UserResponse, logout = vi.fn().mockResolvedValue(undefined)) {
  vi.mocked(authContext.useAuth).mockReturnValue({
    status: 'authenticated',
    user,
    login: vi.fn(),
    verifyMfa: vi.fn(),
    register: vi.fn(),
    logout,
    refreshUser: vi.fn(),
  })
}

function renderAtMinor() {
  return render(
    <MemoryRouter initialEntries={['/minor']}>
      <Routes>
        <Route path="/dashboard" element={<p>Adult Dashboard</p>} />
        <Route path="/minor" element={<MinorAccountPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('MinorAccountPage', () => {
  it('greets a minor account by username', () => {
    mockAuth(buildUser('minor'))
    renderAtMinor()
    expect(screen.getByText('Hi, kiddo!')).toBeInTheDocument()
  })

  it('redirects an adult account to the dashboard', () => {
    mockAuth(buildUser('adult'))
    renderAtMinor()
    expect(screen.getByText('Adult Dashboard')).toBeInTheDocument()
  })

  it('calls logout when the button is clicked', () => {
    const logout = vi.fn().mockResolvedValue(undefined)
    mockAuth(buildUser('minor'), logout)
    renderAtMinor()

    fireEvent.click(screen.getByRole('button', { name: 'Log Out' }))

    expect(logout).toHaveBeenCalled()
  })
})
