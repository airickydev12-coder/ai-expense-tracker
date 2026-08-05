import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

/**
 * Minimal landing page for MINOR accounts -- the real child learning
 * dashboard (age-appropriate content, simulated budgets, guardian
 * approvals, etc.) is planned but not designed yet (blocked on Sprint 6's
 * educational-content system). This page exists so account_type-based
 * routing has somewhere to send a MINOR account instead of the adult
 * financial dashboard, not as a feature in its own right.
 */
export function MinorAccountPage() {
  const { user, logout } = useAuth()

  if (user && user.account_type !== 'minor') {
    return <Navigate to="/dashboard" replace />
  }

  return (
    <div className="mx-auto max-w-sm space-y-4 p-4 pt-16 text-center">
      <h1 className="text-2xl font-semibold text-gray-900">Hi, {user?.username}!</h1>
      <p className="text-sm text-gray-600">
        Your learning dashboard isn't ready yet -- check back soon.
      </p>
      <button
        type="button"
        onClick={logout}
        className="rounded border border-gray-300 px-3 py-1.5 text-sm text-gray-700"
      >
        Log Out
      </button>
    </div>
  )
}
