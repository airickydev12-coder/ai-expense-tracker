import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { EmailVerificationBanner } from './EmailVerificationBanner'
import * as authApi from '../api/auth'

vi.mock('../api/auth')

afterEach(() => {
  vi.restoreAllMocks()
  vi.clearAllMocks()
})

describe('EmailVerificationBanner', () => {
  it('resends the verification email and shows a confirmation', async () => {
    vi.mocked(authApi.resendVerification).mockResolvedValue(undefined)

    render(<EmailVerificationBanner />)
    fireEvent.click(screen.getByRole('button', { name: 'Resend verification email' }))

    expect(await screen.findByText(/Verification email sent/)).toBeInTheDocument()
    expect(authApi.resendVerification).toHaveBeenCalled()
  })

  it('shows an error message when resending fails', async () => {
    vi.mocked(authApi.resendVerification).mockRejectedValue(
      new Error('Too many verification emails requested. Try again in 60 minutes.'),
    )

    render(<EmailVerificationBanner />)
    fireEvent.click(screen.getByRole('button', { name: 'Resend verification email' }))

    expect(
      await screen.findByText('Too many verification emails requested. Try again in 60 minutes.'),
    ).toBeInTheDocument()
  })
})
