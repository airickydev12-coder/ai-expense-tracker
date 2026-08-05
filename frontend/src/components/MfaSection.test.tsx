import { fireEvent, render, screen } from '@testing-library/react'
import QRCode from 'qrcode'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MfaSection } from './MfaSection'
import * as authApi from '../api/auth'
import * as authContext from '../context/AuthContext'
import * as stepUpAuthContext from '../context/StepUpAuthContext'
import type { UserResponse } from '../types/auth'

vi.mock('../api/auth')
vi.mock('../context/AuthContext')
vi.mock('../context/StepUpAuthContext')
vi.mock('qrcode')

const baseUser: UserResponse = {
  id: 1,
  username: 'alice',
  email: 'alice@example.com',
  is_active: true,
  role: 'user',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  email_verified: true,
  mfa_enabled: false,
  account_type: 'adult',
}

function mockAuth(user: UserResponse, refreshUser = vi.fn().mockResolvedValue(undefined)) {
  vi.mocked(authContext.useAuth).mockReturnValue({
    status: 'authenticated',
    user,
    login: vi.fn(),
    verifyMfa: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    refreshUser,
  })
}

beforeEach(() => {
  // Default: no step-up required, actions run straight through -- the
  // dedicated StepUpAuthContext.test.tsx covers the modal flow itself.
  vi.mocked(stepUpAuthContext.useStepUpAuth).mockReturnValue({
    runWithStepUp: (action) => action(),
  })
  // QRCode.toDataURL is overloaded (promise-returning vs. callback-style),
  // which makes vi.mocked() infer the wrong overload's resolved type here --
  // `as never` sidesteps that without weakening the mock's actual behavior.
  vi.mocked(QRCode.toDataURL).mockResolvedValue('data:image/png;base64,fake' as never)
})

afterEach(() => {
  vi.restoreAllMocks()
  vi.clearAllMocks()
})

describe('MfaSection', () => {
  it('shows an enable button when MFA is not enabled', () => {
    mockAuth(baseUser)

    render(<MfaSection />)

    expect(screen.getByRole('button', { name: 'Enable two-factor authentication' })).toBeInTheDocument()
  })

  it('starts enrollment and shows the secret and QR code', async () => {
    mockAuth(baseUser)
    vi.mocked(authApi.beginMfaEnrollment).mockResolvedValue({
      secret: 'ABCDEFGHIJKLMNOP',
      otpauth_uri: 'otpauth://totp/AI%20Expense%20Tracker:alice?secret=ABCDEFGHIJKLMNOP',
    })

    render(<MfaSection />)
    fireEvent.click(screen.getByRole('button', { name: 'Enable two-factor authentication' }))

    expect(await screen.findByText('ABCDEFGHIJKLMNOP')).toBeInTheDocument()
    expect(await screen.findByAltText('MFA enrollment QR code')).toHaveAttribute(
      'src',
      'data:image/png;base64,fake',
    )
  })

  it('confirms enrollment and shows recovery codes once', async () => {
    const refreshUser = vi.fn().mockResolvedValue(undefined)
    mockAuth(baseUser, refreshUser)
    vi.mocked(authApi.beginMfaEnrollment).mockResolvedValue({
      secret: 'ABCDEFGHIJKLMNOP',
      otpauth_uri: 'otpauth://totp/AI%20Expense%20Tracker:alice?secret=ABCDEFGHIJKLMNOP',
    })
    vi.mocked(authApi.confirmMfaEnrollment).mockResolvedValue({
      recovery_codes: ['AAAA-1111', 'BBBB-2222'],
    })

    render(<MfaSection />)
    fireEvent.click(screen.getByRole('button', { name: 'Enable two-factor authentication' }))
    await screen.findByText('ABCDEFGHIJKLMNOP')

    fireEvent.change(screen.getByLabelText('Enter the 6-digit code from your app'), {
      target: { value: '123456' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Confirm' }))

    expect(await screen.findByText('AAAA-1111')).toBeInTheDocument()
    expect(screen.getByText('BBBB-2222')).toBeInTheDocument()
    expect(authApi.confirmMfaEnrollment).toHaveBeenCalledWith({ code: '123456' })
    expect(refreshUser).toHaveBeenCalled()

    fireEvent.click(screen.getByRole('button', { name: "I've saved these codes" }))
    expect(screen.queryByText('AAAA-1111')).not.toBeInTheDocument()
  })

  it('shows an error for a wrong confirmation code', async () => {
    mockAuth(baseUser)
    vi.mocked(authApi.beginMfaEnrollment).mockResolvedValue({
      secret: 'ABCDEFGHIJKLMNOP',
      otpauth_uri: 'otpauth://totp/AI%20Expense%20Tracker:alice?secret=ABCDEFGHIJKLMNOP',
    })
    vi.mocked(authApi.confirmMfaEnrollment).mockRejectedValue(
      new Error('Invalid authentication code.'),
    )

    render(<MfaSection />)
    fireEvent.click(screen.getByRole('button', { name: 'Enable two-factor authentication' }))
    await screen.findByText('ABCDEFGHIJKLMNOP')

    fireEvent.change(screen.getByLabelText('Enter the 6-digit code from your app'), {
      target: { value: '000000' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Confirm' }))

    expect(await screen.findByText('Invalid authentication code.')).toBeInTheDocument()
  })

  it('cancels enrollment', async () => {
    mockAuth(baseUser)
    vi.mocked(authApi.beginMfaEnrollment).mockResolvedValue({
      secret: 'ABCDEFGHIJKLMNOP',
      otpauth_uri: 'otpauth://totp/AI%20Expense%20Tracker:alice?secret=ABCDEFGHIJKLMNOP',
    })

    render(<MfaSection />)
    fireEvent.click(screen.getByRole('button', { name: 'Enable two-factor authentication' }))
    await screen.findByText('ABCDEFGHIJKLMNOP')

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))

    expect(screen.queryByText('ABCDEFGHIJKLMNOP')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Enable two-factor authentication' })).toBeInTheDocument()
  })

  it('shows enabled status with disable and regenerate controls', () => {
    mockAuth({ ...baseUser, mfa_enabled: true })

    render(<MfaSection />)

    expect(screen.getByText('Two-factor authentication is enabled.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Disable' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Regenerate recovery codes' })).toBeInTheDocument()
  })

  it('disables MFA after confirmation', async () => {
    const refreshUser = vi.fn().mockResolvedValue(undefined)
    mockAuth({ ...baseUser, mfa_enabled: true }, refreshUser)
    vi.mocked(authApi.disableMfa).mockResolvedValue(undefined)
    vi.spyOn(window, 'confirm').mockReturnValue(true)

    render(<MfaSection />)
    fireEvent.click(screen.getByRole('button', { name: 'Disable' }))

    expect(authApi.disableMfa).toHaveBeenCalled()
    await vi.waitFor(() => expect(refreshUser).toHaveBeenCalled())
  })

  it('does not disable MFA when the confirmation is declined', () => {
    mockAuth({ ...baseUser, mfa_enabled: true })
    vi.spyOn(window, 'confirm').mockReturnValue(false)

    render(<MfaSection />)
    fireEvent.click(screen.getByRole('button', { name: 'Disable' }))

    expect(authApi.disableMfa).not.toHaveBeenCalled()
  })

  it('regenerates recovery codes after confirmation', async () => {
    mockAuth({ ...baseUser, mfa_enabled: true })
    vi.mocked(authApi.regenerateRecoveryCodes).mockResolvedValue({
      recovery_codes: ['CCCC-3333'],
    })
    vi.spyOn(window, 'confirm').mockReturnValue(true)

    render(<MfaSection />)
    fireEvent.click(screen.getByRole('button', { name: 'Regenerate recovery codes' }))

    expect(await screen.findByText('CCCC-3333')).toBeInTheDocument()
  })
})
