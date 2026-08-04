import { fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { AdminUsersPage } from './AdminUsersPage'
import * as adminApi from '../api/admin'
import * as authContext from '../context/AuthContext'
import * as stepUpAuthContext from '../context/StepUpAuthContext'
import type { UserResponse } from '../types/auth'

vi.mock('../api/admin')
vi.mock('../context/AuthContext')
vi.mock('../context/StepUpAuthContext')

beforeEach(() => {
  // Default: no step-up required, actions run straight through -- the
  // dedicated StepUpAuthContext.test.tsx covers the modal flow itself.
  vi.mocked(stepUpAuthContext.useStepUpAuth).mockReturnValue({
    runWithStepUp: (action) => action(),
  })
})

const admin: UserResponse = {
  id: 1,
  username: 'admin',
  email: 'admin@example.com',
  is_active: true,
  role: 'super_admin',
  created_at: '2020-01-01T00:00:00Z',
  updated_at: '2020-01-01T00:00:00Z',
  email_verified: true,
}

const bob: UserResponse = {
  id: 2,
  username: 'bob',
  email: 'bob@example.com',
  is_active: true,
  role: 'user',
  created_at: '2020-01-01T00:00:00Z',
  updated_at: '2020-01-01T00:00:00Z',
  email_verified: true,
}

function mockAuth(currentUser: UserResponse) {
  vi.mocked(authContext.useAuth).mockReturnValue({
    status: 'authenticated',
    user: currentUser,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    refreshUser: vi.fn(),
  })
}

afterEach(() => {
  vi.restoreAllMocks()
  vi.clearAllMocks()
})

describe('AdminUsersPage', () => {
  it('renders the user list once loaded', async () => {
    mockAuth(admin)
    vi.mocked(adminApi.listUsers).mockResolvedValue([admin, bob])

    render(<AdminUsersPage />)

    expect(await screen.findByText('bob')).toBeInTheDocument()
    expect(screen.getByText('admin')).toBeInTheDocument()
  })

  it('filters the list by search text', async () => {
    mockAuth(admin)
    vi.mocked(adminApi.listUsers).mockResolvedValue([admin, bob])

    render(<AdminUsersPage />)
    await screen.findByText('bob')

    fireEvent.change(screen.getByLabelText('Search'), { target: { value: 'bob' } })

    expect(screen.getByText('bob')).toBeInTheDocument()
    expect(screen.queryByText('admin')).not.toBeInTheDocument()
  })

  it('deactivates a user after confirmation', async () => {
    mockAuth(admin)
    vi.mocked(adminApi.listUsers).mockResolvedValue([admin, bob])
    vi.mocked(adminApi.setUserActive).mockResolvedValue({ ...bob, is_active: false })
    vi.spyOn(window, 'confirm').mockReturnValue(true)

    render(<AdminUsersPage />)
    const bobRow = (await screen.findByText('bob')).closest('li') as HTMLElement

    fireEvent.click(within(bobRow).getByRole('button', { name: 'Deactivate' }))

    expect(adminApi.setUserActive).toHaveBeenCalledWith(2, { is_active: false })
  })

  it('does not deactivate when the confirmation is declined', async () => {
    mockAuth(admin)
    vi.mocked(adminApi.listUsers).mockResolvedValue([admin, bob])
    vi.spyOn(window, 'confirm').mockReturnValue(false)

    render(<AdminUsersPage />)
    const bobRow = (await screen.findByText('bob')).closest('li') as HTMLElement

    fireEvent.click(within(bobRow).getByRole('button', { name: 'Deactivate' }))

    expect(adminApi.setUserActive).not.toHaveBeenCalled()
  })

  it("disables the deactivate button and role control for the admin's own row", async () => {
    mockAuth(admin)
    vi.mocked(adminApi.listUsers).mockResolvedValue([admin, bob])

    render(<AdminUsersPage />)
    const adminRow = (await screen.findByText('admin')).closest('li') as HTMLElement

    expect(within(adminRow).getByRole('button', { name: 'Deactivate' })).toBeDisabled()
    expect(within(adminRow).getByLabelText('Role for admin')).toBeDisabled()
  })

  it('assigns a new role when the current user is a super admin', async () => {
    mockAuth(admin)
    vi.mocked(adminApi.listUsers).mockResolvedValue([admin, bob])
    vi.mocked(adminApi.assignUserRole).mockResolvedValue({ ...bob, role: 'admin' })

    render(<AdminUsersPage />)
    const bobRow = (await screen.findByText('bob')).closest('li') as HTMLElement

    fireEvent.change(within(bobRow).getByLabelText('Role for bob'), { target: { value: 'admin' } })

    expect(adminApi.assignUserRole).toHaveBeenCalledWith(2, { role: 'admin' })
  })

  it('hides the role selector for an admin who is not a super admin', async () => {
    mockAuth({ ...admin, role: 'admin' })
    vi.mocked(adminApi.listUsers).mockResolvedValue([admin, bob])

    render(<AdminUsersPage />)
    await screen.findByText('bob')

    expect(screen.queryByLabelText('Role for bob')).not.toBeInTheDocument()
  })

  it('revokes sessions after confirmation', async () => {
    mockAuth(admin)
    vi.mocked(adminApi.listUsers).mockResolvedValue([admin, bob])
    vi.mocked(adminApi.revokeUserSessions).mockResolvedValue(undefined)
    vi.spyOn(window, 'confirm').mockReturnValue(true)

    render(<AdminUsersPage />)
    const bobRow = (await screen.findByText('bob')).closest('li') as HTMLElement

    fireEvent.click(within(bobRow).getByRole('button', { name: 'Revoke Sessions' }))

    expect(adminApi.revokeUserSessions).toHaveBeenCalledWith(2)
  })

  it('renders an error message when the list fails to load', async () => {
    mockAuth(admin)
    vi.mocked(adminApi.listUsers).mockRejectedValue(new Error('Network error'))

    render(<AdminUsersPage />)

    expect(await screen.findByText(/Failed to load users/i)).toBeInTheDocument()
  })
})
