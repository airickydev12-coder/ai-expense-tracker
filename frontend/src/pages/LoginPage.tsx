import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function LoginPage() {
  const { status, login, verifyMfa } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [challengeToken, setChallengeToken] = useState<string | null>(null)
  const [code, setCode] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  if (status === 'authenticated') {
    return <Navigate to="/dashboard" replace />
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()

    if (!username.trim() || !password) {
      setFormError('Username and password are required.')
      return
    }

    setFormError(null)
    setSubmitting(true)
    login(username.trim(), password)
      .then((outcome) => {
        if (outcome.status === 'mfa_required') {
          setChallengeToken(outcome.challengeToken)
          return
        }
        navigate('/dashboard', { replace: true })
      })
      .catch((err: unknown) => {
        setFormError(err instanceof Error ? err.message : 'Failed to log in')
      })
      .finally(() => setSubmitting(false))
  }

  function handleVerifyMfa(e: FormEvent) {
    e.preventDefault()

    if (!challengeToken || !code.trim()) {
      setFormError('Enter your authentication code.')
      return
    }

    setFormError(null)
    setSubmitting(true)
    verifyMfa(challengeToken, code.trim())
      .then(() => navigate('/dashboard', { replace: true }))
      .catch((err: unknown) => {
        setFormError(err instanceof Error ? err.message : 'Failed to verify code')
      })
      .finally(() => setSubmitting(false))
  }

  if (challengeToken) {
    return (
      <div className="mx-auto max-w-sm space-y-6 p-4 pt-16">
        <h1 className="text-2xl font-semibold text-gray-900">Two-Factor Authentication</h1>

        <form
          onSubmit={handleVerifyMfa}
          className="space-y-3 rounded border border-gray-200 p-4"
        >
          {formError && <p className="text-sm text-red-600">{formError}</p>}

          <div className="flex flex-col gap-1">
            <label htmlFor="login-mfa-code" className="text-xs text-gray-500">
              Authentication code or recovery code
            </label>
            <input
              id="login-mfa-code"
              type="text"
              autoFocus
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="rounded border border-gray-300 px-2 py-1 text-sm"
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
          >
            {submitting ? 'Verifying...' : 'Verify'}
          </button>
        </form>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-sm space-y-6 p-4 pt-16">
      <h1 className="text-2xl font-semibold text-gray-900">Log In</h1>

      <form onSubmit={handleSubmit} className="space-y-3 rounded border border-gray-200 p-4">
        {formError && <p className="text-sm text-red-600">{formError}</p>}

        <div className="flex flex-col gap-1">
          <label htmlFor="login-username" className="text-xs text-gray-500">
            Username
          </label>
          <input
            id="login-username"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="rounded border border-gray-300 px-2 py-1 text-sm"
          />
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor="login-password" className="text-xs text-gray-500">
            Password
          </label>
          <input
            id="login-password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="rounded border border-gray-300 px-2 py-1 text-sm"
          />
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        >
          {submitting ? 'Logging in...' : 'Log In'}
        </button>
      </form>

      <p className="text-sm text-gray-600">
        Don&apos;t have an account?{' '}
        <Link to="/register" className="text-blue-600 hover:underline">
          Register
        </Link>
      </p>

      <p className="text-sm text-gray-600">
        <Link to="/forgot-password" className="text-blue-600 hover:underline">
          Forgot password?
        </Link>
      </p>
    </div>
  )
}
