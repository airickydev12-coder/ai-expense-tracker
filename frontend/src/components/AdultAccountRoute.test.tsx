import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { AdultAccountRoute } from './AdultAccountRoute'
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
    username: 'alice',
    email: 'alice@example.com',
    is_active: true,
    role: 'user',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    email_verified: true,
    mfa_enabled: false,
    account_type: accountType,
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

function renderAtDashboard() {
  return render(
    <MemoryRouter initialEntries={['/dashboard']}>
      <Routes>
        <Route path="/minor" element={<p>Minor Area</p>} />
        <Route element={<AdultAccountRoute />}>
          <Route path="/dashboard" element={<p>Adult Dashboard</p>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  )
}

describe('AdultAccountRoute', () => {
  it('renders the nested route for an adult account', () => {
    mockAuth(buildUser('adult'))
    renderAtDashboard()
    expect(screen.getByText('Adult Dashboard')).toBeInTheDocument()
  })

  it('redirects a minor account to /minor', () => {
    mockAuth(buildUser('minor'))
    renderAtDashboard()
    expect(screen.getByText('Minor Area')).toBeInTheDocument()
  })
})
