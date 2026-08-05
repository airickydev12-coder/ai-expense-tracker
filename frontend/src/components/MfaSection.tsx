import QRCode from 'qrcode'
import { useState } from 'react'
import type { FormEvent } from 'react'
import {
  beginMfaEnrollment,
  confirmMfaEnrollment,
  disableMfa,
  regenerateRecoveryCodes,
} from '../api/auth'
import { useAuth } from '../context/AuthContext'
import { useStepUpAuth } from '../context/StepUpAuthContext'

interface EnrollmentState {
  secret: string
  otpauthUri: string
  qrDataUrl: string | null
}

export function MfaSection() {
  const { user, refreshUser } = useAuth()
  const { runWithStepUp } = useStepUpAuth()
  const [enrolling, setEnrolling] = useState<EnrollmentState | null>(null)
  const [code, setCode] = useState('')
  const [recoveryCodes, setRecoveryCodes] = useState<string[] | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!user) return null

  function handleBeginEnroll() {
    setError(null)
    setBusy(true)
    runWithStepUp(() => beginMfaEnrollment())
      .then(({ secret, otpauth_uri }) => {
        setEnrolling({ secret, otpauthUri: otpauth_uri, qrDataUrl: null })
        QRCode.toDataURL(otpauth_uri)
          .then((qrDataUrl) => {
            setEnrolling((prev) => (prev ? { ...prev, qrDataUrl } : prev))
          })
          .catch(() => {
            // No QR image -- the manual-entry secret below still works.
          })
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to start MFA enrollment')
      })
      .finally(() => setBusy(false))
  }

  function handleCancelEnroll() {
    setEnrolling(null)
    setCode('')
    setError(null)
  }

  function handleConfirm(e: FormEvent) {
    e.preventDefault()
    if (!code.trim()) return

    setError(null)
    setBusy(true)
    runWithStepUp(() => confirmMfaEnrollment({ code: code.trim() }))
      .then(({ recovery_codes }) => {
        setEnrolling(null)
        setCode('')
        setRecoveryCodes(recovery_codes)
        return refreshUser()
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Invalid code')
      })
      .finally(() => setBusy(false))
  }

  function handleDisable() {
    if (!window.confirm('Disable two-factor authentication?')) return

    setError(null)
    setBusy(true)
    runWithStepUp(() => disableMfa())
      .then(() => refreshUser())
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to disable MFA')
      })
      .finally(() => setBusy(false))
  }

  function handleRegenerate() {
    if (
      !window.confirm(
        'Regenerate recovery codes? Your existing codes will stop working immediately.',
      )
    ) {
      return
    }

    setError(null)
    setBusy(true)
    runWithStepUp(() => regenerateRecoveryCodes())
      .then(({ recovery_codes }) => setRecoveryCodes(recovery_codes))
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to regenerate recovery codes')
      })
      .finally(() => setBusy(false))
  }

  return (
    <section className="space-y-3">
      <h2 className="text-lg font-medium text-gray-900">Two-Factor Authentication</h2>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {recoveryCodes ? (
        <div className="space-y-3 rounded border border-gray-200 p-4">
          <p className="text-sm text-gray-900">
            Save these recovery codes somewhere safe. Each one can be used once to sign in if
            you lose access to your authenticator app. They won&apos;t be shown again.
          </p>
          <ul className="grid grid-cols-2 gap-1 rounded bg-gray-50 p-3 font-mono text-sm text-gray-900">
            {recoveryCodes.map((recoveryCode) => (
              <li key={recoveryCode}>{recoveryCode}</li>
            ))}
          </ul>
          <button
            type="button"
            onClick={() => setRecoveryCodes(null)}
            className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white"
          >
            I&apos;ve saved these codes
          </button>
        </div>
      ) : enrolling ? (
        <form
          onSubmit={handleConfirm}
          className="space-y-3 rounded border border-gray-200 p-4"
        >
          <p className="text-sm text-gray-600">
            Scan this code with your authenticator app, or enter the secret manually.
          </p>
          {enrolling.qrDataUrl && (
            <img src={enrolling.qrDataUrl} alt="MFA enrollment QR code" className="h-40 w-40" />
          )}
          <p className="break-all font-mono text-xs text-gray-500">{enrolling.secret}</p>

          <div className="flex flex-col gap-1">
            <label htmlFor="mfa-confirm-code" className="text-xs text-gray-500">
              Enter the 6-digit code from your app
            </label>
            <input
              id="mfa-confirm-code"
              type="text"
              autoFocus
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="rounded border border-gray-300 px-2 py-1 text-sm"
            />
          </div>

          <div className="flex gap-2">
            <button
              type="submit"
              disabled={busy}
              className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
            >
              {busy ? 'Confirming...' : 'Confirm'}
            </button>
            <button
              type="button"
              onClick={handleCancelEnroll}
              className="rounded px-3 py-1.5 text-sm font-medium text-gray-600 hover:underline"
            >
              Cancel
            </button>
          </div>
        </form>
      ) : user.mfa_enabled ? (
        <div className="flex flex-wrap items-center gap-3 rounded border border-gray-200 p-4 text-sm">
          <p className="flex-1 text-gray-900">Two-factor authentication is enabled.</p>
          <button
            type="button"
            disabled={busy}
            onClick={handleRegenerate}
            className="text-blue-600 hover:underline disabled:opacity-50"
          >
            Regenerate recovery codes
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={handleDisable}
            className="text-red-600 hover:underline disabled:opacity-50"
          >
            Disable
          </button>
        </div>
      ) : (
        <div className="rounded border border-gray-200 p-4">
          <button
            type="button"
            disabled={busy}
            onClick={handleBeginEnroll}
            className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
          >
            Enable two-factor authentication
          </button>
        </div>
      )}
    </section>
  )
}
