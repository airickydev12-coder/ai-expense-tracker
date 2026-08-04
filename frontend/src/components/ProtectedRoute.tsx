import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function ProtectedRoute() {
  const { status } = useAuth()

  if (status === 'bootstrapping') {
    return <p className="p-4 text-gray-600">Loading...</p>
  }

  if (status === 'unauthenticated') {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
