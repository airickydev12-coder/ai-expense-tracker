import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ForgotPasswordPage } from './ForgotPasswordPage'
import * as authApi from '../api/auth'

vi.mock('../api/auth')

afterEach(() => {
  vi.restoreAllMocks()
  vi.clearAllMocks()
})

describe('ForgotPasswordPage', () => {
  it('submits the email and shows the generic confirmation message', async () => {
    vi.mocked(authApi.forgotPassword).mockResolvedValue(undefined)

    render(
      <MemoryRouter>
        <ForgotPasswordPage />
      </MemoryRouter>,
    )

    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'alice@example.com' } })
    fireEvent.click(screen.getByRole('button', { name: 'Send Reset Link' }))

    expect(
      await screen.findByText('If that email is registered, a password reset link has been sent to it.'),
    ).toBeInTheDocument()
    expect(authApi.forgotPassword).toHaveBeenCalledWith({ email: 'alice@example.com' })
  })

  it('shows the same generic message even when the email is unknown', async () => {
    vi.mocked(authApi.forgotPassword).mockResolvedValue(undefined)

    render(
      <MemoryRouter>
        <ForgotPasswordPage />
      </MemoryRouter>,
    )

    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'nobody@example.com' } })
    fireEvent.click(screen.getByRole('button', { name: 'Send Reset Link' }))

    expect(
      await screen.findByText('If that email is registered, a password reset link has been sent to it.'),
    ).toBeInTheDocument()
  })

  it('shows a validation error for an empty email', () => {
    render(
      <MemoryRouter>
        <ForgotPasswordPage />
      </MemoryRouter>,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Send Reset Link' }))

    expect(screen.getByText('Email is required.')).toBeInTheDocument()
  })
})
