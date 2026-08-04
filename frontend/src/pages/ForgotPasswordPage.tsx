import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { forgotPassword } from '../api/auth'

const GENERIC_MESSAGE = 'If that email is registered, a password reset link has been sent to it.'

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [submitted, setSubmitted] = useState(false)

  function handleSubmit(e: FormEvent) {
    e.preventDefault()

    if (!email.trim()) {
      setFormError('Email is required.')
      return
    }

    setFormError(null)
    setSubmitting(true)
    forgotPassword({ email: email.trim() })
      .then(() => setSubmitted(true))
      .catch((err: unknown) => {
        setFormError(err instanceof Error ? err.message : 'Failed to request a password reset')
      })
      .finally(() => setSubmitting(false))
  }

  return (
    <div className="mx-auto max-w-sm space-y-6 p-4 pt-16">
      <h1 className="text-2xl font-semibold text-gray-900">Forgot Password</h1>

      {submitted ? (
        <p className="text-sm text-gray-600">{GENERIC_MESSAGE}</p>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-3 rounded border border-gray-200 p-4">
          {formError && <p className="text-sm text-red-600">{formError}</p>}

          <div className="flex flex-col gap-1">
            <label htmlFor="forgot-password-email" className="text-xs text-gray-500">
              Email
            </label>
            <input
              id="forgot-password-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="rounded border border-gray-300 px-2 py-1 text-sm"
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
          >
            {submitting ? 'Sending...' : 'Send Reset Link'}
          </button>
        </form>
      )}

      <p className="text-sm text-gray-600">
        <Link to="/login" className="text-blue-600 hover:underline">
          Back to Log In
        </Link>
      </p>
    </div>
  )
}
