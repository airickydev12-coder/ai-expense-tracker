import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { AdminOverviewPage } from './AdminOverviewPage'
import * as adminApi from '../api/admin'
import type { UserResponse } from '../types/auth'

vi.mock('../api/admin')

afterEach(() => {
  vi.restoreAllMocks()
  vi.clearAllMocks()
})

function buildUser(id: number, role: UserResponse['role'], createdAt: string): UserResponse {
  return {
    id,
    username: `user${id}`,
    email: `user${id}@example.com`,
    is_active: id !== 3,
    role,
    created_at: createdAt,
    updated_at: createdAt,
    email_verified: true,
  }
}

function statValue(label: string): string | null {
  return screen.getByText(label).closest('div')?.querySelector('p:last-child')?.textContent ?? null
}

describe('AdminOverviewPage', () => {
  it('renders computed stats from the user list', async () => {
    vi.mocked(adminApi.getAdminOverview).mockResolvedValue({
      message: 'Admin access confirmed.',
      admin_username: 'admin',
      admin_role: 'super_admin',
    })
    vi.mocked(adminApi.listUsers).mockResolvedValue([
      buildUser(1, 'super_admin', '2020-01-01T00:00:00Z'),
      buildUser(2, 'user', '2020-01-01T00:00:00Z'),
      buildUser(3, 'user', '2020-01-01T00:00:00Z'),
    ])

    render(<AdminOverviewPage />)

    await screen.findByText('Total Users')
    expect(statValue('Total Users')).toBe('3')
    expect(statValue('Active')).toBe('2')
    expect(statValue('Inactive')).toBe('1')
    expect(statValue('Admins')).toBe('1')
  })

  it('renders an error message when loading fails', async () => {
    vi.mocked(adminApi.getAdminOverview).mockRejectedValue(new Error('Network error'))
    vi.mocked(adminApi.listUsers).mockResolvedValue([])

    render(<AdminOverviewPage />)

    expect(await screen.findByText(/Failed to load admin overview/i)).toBeInTheDocument()
  })
})
