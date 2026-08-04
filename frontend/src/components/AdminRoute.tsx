import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const ADMIN_ROLES = ['admin', 'super_admin']

/**
 * Nested inside ProtectedRoute, so by the time this renders the user is
 * always authenticated -- this only adds the role check on top.
 */
export function AdminRoute() {
  const { user } = useAuth()

  if (!user || !ADMIN_ROLES.includes(user.role)) {
    return <Navigate to="/dashboard" replace />
  }

  return <Outlet />
}
