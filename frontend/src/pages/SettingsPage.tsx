import { useState } from 'react'
import type { FormEvent } from 'react'
import { updateProfile } from '../api/auth'
import { useAuth } from '../context/AuthContext'

export function SettingsPage() {
  const { user, refreshUser } = useAuth()
  const [username, setUsername] = useState(user?.username ?? '')
  const [email, setEmail] = useState(user?.email ?? '')
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  function handleSubmit(e: FormEvent) {
    e.preventDefault()

    const trimmedUsername = username.trim()
    const trimmedEmail = email.trim()

    if (trimmedUsername.length < 3 || trimmedUsername.length > 50) {
      setFormError('Username must be between 3 and 50 characters.')
      setSuccessMessage(null)
      return
    }

    if (!trimmedEmail) {
      setFormError('Email is required.')
      setSuccessMessage(null)
      return
    }

    setFormError(null)
    setSuccessMessage(null)
    setSubmitting(true)
    updateProfile({ username: trimmedUsername, email: trimmedEmail })
      .then(() => refreshUser())
      .then(() => setSuccessMessage('Profile updated successfully.'))
      .catch((err: unknown) => {
        setFormError(err instanceof Error ? err.message : 'Failed to update profile')
      })
      .finally(() => setSubmitting(false))
  }

  return (
    <div className="mx-auto max-w-lg space-y-6 p-4">
      <h1 className="text-2xl font-semibold text-gray-900">Account Settings</h1>

      <section className="space-y-3">
        <h2 className="text-lg font-medium text-gray-900">Profile</h2>

        <form onSubmit={handleSubmit} className="space-y-3 rounded border border-gray-200 p-4">
          {formError && <p className="text-sm text-red-600">{formError}</p>}
          {successMessage && <p className="text-sm text-green-600">{successMessage}</p>}

          <div className="flex flex-col gap-1">
            <label htmlFor="settings-username" className="text-xs text-gray-500">
              Username
            </label>
            <input
              id="settings-username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="rounded border border-gray-300 px-2 py-1 text-sm"
            />
          </div>

          <div className="flex flex-col gap-1">
            <label htmlFor="settings-email" className="text-xs text-gray-500">
              Email
            </label>
            <input
              id="settings-email"
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
            {submitting ? 'Saving...' : 'Save Changes'}
          </button>
        </form>
      </section>
    </div>
  )
}
