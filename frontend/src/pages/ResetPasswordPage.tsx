import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { resetPassword } from '../api/auth'

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token') ?? ''
  const navigate = useNavigate()
  const [newPassword, setNewPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  function handleSubmit(e: FormEvent) {
    e.preventDefault()

    if (newPassword.length < 8 || newPassword.length > 128) {
      setFormError('Password must be between 8 and 128 characters.')
      return
    }

    setFormError(null)
    setSubmitting(true)
    resetPassword({ token, new_password: newPassword })
      .then(() => navigate('/login', { replace: true }))
      .catch((err: unknown) => {
        setFormError(err instanceof Error ? err.message : 'Failed to reset password')
      })
      .finally(() => setSubmitting(false))
  }

  if (!token) {
    return (
      <div className="mx-auto max-w-sm space-y-6 p-4 pt-16">
        <h1 className="text-2xl font-semibold text-gray-900">Reset Password</h1>
        <p className="text-sm text-red-600">
          This reset link is missing its token. Request a new one from the{' '}
          <Link to="/forgot-password" className="text-blue-600 hover:underline">
            forgot password
          </Link>{' '}
          page.
        </p>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-sm space-y-6 p-4 pt-16">
      <h1 className="text-2xl font-semibold text-gray-900">Reset Password</h1>

      <form onSubmit={handleSubmit} className="space-y-3 rounded border border-gray-200 p-4">
        {formError && <p className="text-sm text-red-600">{formError}</p>}

        <div className="flex flex-col gap-1">
          <label htmlFor="reset-password-new-password" className="text-xs text-gray-500">
            New Password
          </label>
          <input
            id="reset-password-new-password"
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            className="rounded border border-gray-300 px-2 py-1 text-sm"
          />
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        >
          {submitting ? 'Resetting...' : 'Reset Password'}
        </button>
      </form>
    </div>
  )
}
