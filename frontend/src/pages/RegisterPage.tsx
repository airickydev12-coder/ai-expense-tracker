import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function RegisterPage() {
  const { status, register } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  if (status === 'authenticated') {
    return <Navigate to="/dashboard" replace />
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()

    const trimmedUsername = username.trim()
    const trimmedEmail = email.trim()

    if (trimmedUsername.length < 3 || trimmedUsername.length > 50) {
      setFormError('Username must be between 3 and 50 characters.')
      return
    }

    if (!trimmedEmail) {
      setFormError('Email is required.')
      return
    }

    if (password.length < 8 || password.length > 128) {
      setFormError('Password must be between 8 and 128 characters.')
      return
    }

    setFormError(null)
    setSubmitting(true)
    register(trimmedUsername, trimmedEmail, password)
      .then(() => navigate('/dashboard', { replace: true }))
      .catch((err: unknown) => {
        setFormError(err instanceof Error ? err.message : 'Failed to register')
      })
      .finally(() => setSubmitting(false))
  }

  return (
    <div className="mx-auto max-w-sm space-y-6 p-4 pt-16">
      <h1 className="text-2xl font-semibold text-gray-900">Register</h1>

      <form onSubmit={handleSubmit} className="space-y-3 rounded border border-gray-200 p-4">
        {formError && <p className="text-sm text-red-600">{formError}</p>}

        <div className="flex flex-col gap-1">
          <label htmlFor="register-username" className="text-xs text-gray-500">
            Username
          </label>
          <input
            id="register-username"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="rounded border border-gray-300 px-2 py-1 text-sm"
          />
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor="register-email" className="text-xs text-gray-500">
            Email
          </label>
          <input
            id="register-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="rounded border border-gray-300 px-2 py-1 text-sm"
          />
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor="register-password" className="text-xs text-gray-500">
            Password
          </label>
          <input
            id="register-password"
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
          {submitting ? 'Registering...' : 'Register'}
        </button>
      </form>

      <p className="text-sm text-gray-600">
        Already have an account?{' '}
        <Link to="/login" className="text-blue-600 hover:underline">
          Log In
        </Link>
      </p>
    </div>
  )
}
