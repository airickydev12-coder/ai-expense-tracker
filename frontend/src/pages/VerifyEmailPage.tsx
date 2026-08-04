import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { verifyEmail } from '../api/auth'
import { useAuth } from '../context/AuthContext'

type VerifyState =
  | { status: 'verifying' }
  | { status: 'success' }
  | { status: 'error'; message: string }

export function VerifyEmailPage() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token') ?? ''
  const { status: authStatus, refreshUser } = useAuth()
  const [state, setState] = useState<VerifyState>({ status: 'verifying' })

  useEffect(() => {
    if (!token) {
      setState({
        status: 'error',
        message: 'This verification link is missing its token.',
      })
      return
    }

    verifyEmail({ token })
      .then(() => {
        setState({ status: 'success' })
        // If already logged in, refresh the cached user so the "verify
        // your email" banner disappears immediately instead of waiting
        // for the next natural refetch.
        if (authStatus === 'authenticated') {
          refreshUser().catch(() => {
            // Non-fatal -- verification itself already succeeded.
          })
        }
      })
      .catch((err: unknown) => {
        setState({
          status: 'error',
          message: err instanceof Error ? err.message : 'Failed to verify email',
        })
      })
    // Intentionally runs once for the token from the URL, not on every
    // authStatus/refreshUser identity change.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token])

  return (
    <div className="mx-auto max-w-sm space-y-6 p-4 pt-16">
      <h1 className="text-2xl font-semibold text-gray-900">Verify Email</h1>

      {state.status === 'verifying' && <p className="text-sm text-gray-600">Verifying...</p>}
      {state.status === 'success' && (
        <p className="text-sm text-green-600">Your email has been verified.</p>
      )}
      {state.status === 'error' && <p className="text-sm text-red-600">{state.message}</p>}

      <p className="text-sm text-gray-600">
        <Link to="/dashboard" className="text-blue-600 hover:underline">
          Go to Dashboard
        </Link>
      </p>
    </div>
  )
}
