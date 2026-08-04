import { useState } from 'react'
import { resendVerification } from '../api/auth'

export function EmailVerificationBanner() {
  const [status, setStatus] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  function handleResend() {
    setStatus('sending')
    setErrorMessage(null)
    resendVerification()
      .then(() => setStatus('sent'))
      .catch((err: unknown) => {
        setErrorMessage(err instanceof Error ? err.message : 'Failed to resend verification email')
        setStatus('error')
      })
  }

  return (
    <div className="border-b border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-800">
      <div className="mx-auto flex max-w-4xl flex-wrap items-center gap-2">
        {status === 'sent' ? (
          <span>Verification email sent -- check your inbox.</span>
        ) : (
          <>
            <span>Please verify your email address.</span>
            <button
              type="button"
              onClick={handleResend}
              disabled={status === 'sending'}
              className="font-medium text-amber-900 underline hover:no-underline disabled:opacity-50"
            >
              {status === 'sending' ? 'Sending...' : 'Resend verification email'}
            </button>
            {status === 'error' && errorMessage && <span className="text-red-700">{errorMessage}</span>}
          </>
        )}
      </div>
    </div>
  )
}
