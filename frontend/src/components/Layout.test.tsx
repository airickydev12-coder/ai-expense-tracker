import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { Layout } from './Layout'
import * as authContext from '../context/AuthContext'
import type { PlatformRole, UserResponse } from '../types/auth'

vi.mock('../context/AuthContext')

afterEach(() => {
  vi.restoreAllMocks()
  vi.clearAllMocks()
})

function buildUser(role: PlatformRole, emailVerified: boolean): UserResponse {
  return {
    id: 1,
    username: 'alice',
    email: 'alice@example.com',
    is_active: true,
    role,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    email_verified: emailVerified,
    mfa_enabled: false,
  }
}

function mockAuth(user: UserResponse | null) {
  vi.mocked(authContext.useAuth).mockReturnValue({
    status: 'authenticated',
    user,
    login: vi.fn(),
    verifyMfa: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    refreshUser: vi.fn(),
  })
}

function renderLayout() {
  return render(
    <MemoryRouter initialEntries={['/dashboard']}>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/dashboard" element={<p>Dashboard content</p>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  )
}

describe('Layout', () => {
  it('shows the email verification banner for an unverified user', () => {
    mockAuth(buildUser('user', false))

    renderLayout()

    expect(screen.getByText('Please verify your email address.')).toBeInTheDocument()
  })

  it('hides the email verification banner for a verified user', () => {
    mockAuth(buildUser('user', true))

    renderLayout()

    expect(screen.queryByText('Please verify your email address.')).not.toBeInTheDocument()
  })
})
