import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

/**
 * Nested inside ProtectedRoute, so by the time this renders the user is
 * always authenticated -- this only adds the account_type check on top.
 * A MINOR account has no access to the adult financial dashboard (see
 * ADR-007's permission matrix) and is redirected to its own minimal view
 * instead.
 */
export function AdultAccountRoute() {
  const { user } = useAuth()

  if (user?.account_type === 'minor') {
    return <Navigate to="/minor" replace />
  }

  return <Outlet />
}
