import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ResetPasswordPage } from './ResetPasswordPage'
import * as authApi from '../api/auth'

vi.mock('../api/auth')

afterEach(() => {
  vi.restoreAllMocks()
  vi.clearAllMocks()
})

function renderWithToken(token: string | null) {
  const initialPath = token ? `/reset-password?token=${token}` : '/reset-password'

  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/login" element={<p>Login Page</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('ResetPasswordPage', () => {
  it('submits the new password with the token from the URL and redirects to login', async () => {
    vi.mocked(authApi.resetPassword).mockResolvedValue(undefined)

    renderWithToken('a-real-token')

    fireEvent.change(screen.getByLabelText('New Password'), { target: { value: 'new-password' } })
    fireEvent.click(screen.getByRole('button', { name: 'Reset Password' }))

    expect(await screen.findByText('Login Page')).toBeInTheDocument()
    expect(authApi.resetPassword).toHaveBeenCalledWith({
      token: 'a-real-token',
      new_password: 'new-password',
    })
  })

  it('shows a validation error for a too-short password', () => {
    renderWithToken('a-real-token')

    fireEvent.change(screen.getByLabelText('New Password'), { target: { value: 'short' } })
    fireEvent.click(screen.getByRole('button', { name: 'Reset Password' }))

    expect(screen.getByText('Password must be between 8 and 128 characters.')).toBeInTheDocument()
  })

  it('shows the API error message on an invalid or expired token', async () => {
    vi.mocked(authApi.resetPassword).mockRejectedValue(
      new Error('This password reset link is invalid or has expired.'),
    )

    renderWithToken('a-stale-token')

    fireEvent.change(screen.getByLabelText('New Password'), { target: { value: 'new-password' } })
    fireEvent.click(screen.getByRole('button', { name: 'Reset Password' }))

    expect(
      await screen.findByText('This password reset link is invalid or has expired.'),
    ).toBeInTheDocument()
  })

  it('shows a message when the URL has no token', () => {
    renderWithToken(null)

    expect(screen.getByText(/This reset link is missing its token/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Reset Password' })).not.toBeInTheDocument()
  })
})
