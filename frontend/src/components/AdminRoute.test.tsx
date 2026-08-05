import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { AdminRoute } from './AdminRoute'
import * as authContext from '../context/AuthContext'
import type { PlatformRole, UserResponse } from '../types/auth'

vi.mock('../context/AuthContext')

afterEach(() => {
  vi.restoreAllMocks()
  vi.clearAllMocks()
})

function buildUser(role: PlatformRole): UserResponse {
  return {
    id: 1,
    username: 'alice',
    email: 'alice@example.com',
    is_active: true,
    role,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    email_verified: true,
    mfa_enabled: false,
    account_type: 'adult',
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

function renderAtAdminRoute() {
  return render(
    <MemoryRouter initialEntries={['/admin']}>
      <Routes>
        <Route path="/dashboard" element={<p>Dashboard</p>} />
        <Route element={<AdminRoute />}>
          <Route path="/admin" element={<p>Admin Area</p>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  )
}

describe('AdminRoute', () => {
  it('renders the nested route for an admin', () => {
    mockAuth(buildUser('admin'))
    renderAtAdminRoute()
    expect(screen.getByText('Admin Area')).toBeInTheDocument()
  })

  it('renders the nested route for a super admin', () => {
    mockAuth(buildUser('super_admin'))
    renderAtAdminRoute()
    expect(screen.getByText('Admin Area')).toBeInTheDocument()
  })

  it('redirects a plain user to the dashboard', () => {
    mockAuth(buildUser('user'))
    renderAtAdminRoute()
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
  })

  it('redirects when there is no authenticated user', () => {
    mockAuth(null)
    renderAtAdminRoute()
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
  })
})
