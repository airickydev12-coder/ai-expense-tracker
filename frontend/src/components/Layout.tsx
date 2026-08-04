import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function Layout() {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b border-gray-200 bg-white px-4 py-3">
        <div className="mx-auto flex max-w-4xl items-center gap-6">
          <h1 className="text-lg font-semibold text-gray-900">AI Expense Tracker</h1>
          <nav className="flex flex-wrap gap-4 text-sm">
            <NavLink
              to="/dashboard"
              className={({ isActive }) => (isActive ? 'font-medium text-blue-600' : 'text-gray-600')}
            >
              Dashboard
            </NavLink>
            <NavLink
              to="/expenses"
              className={({ isActive }) => (isActive ? 'font-medium text-blue-600' : 'text-gray-600')}
            >
              Expenses
            </NavLink>
            <NavLink
              to="/recurring-expenses"
              className={({ isActive }) => (isActive ? 'font-medium text-blue-600' : 'text-gray-600')}
            >
              Recurring Expenses
            </NavLink>
            <NavLink
              to="/accounts"
              className={({ isActive }) => (isActive ? 'font-medium text-blue-600' : 'text-gray-600')}
            >
              Accounts
            </NavLink>
            <NavLink
              to="/bills"
              className={({ isActive }) => (isActive ? 'font-medium text-blue-600' : 'text-gray-600')}
            >
              Bills
            </NavLink>
            <NavLink
              to="/income"
              className={({ isActive }) => (isActive ? 'font-medium text-blue-600' : 'text-gray-600')}
            >
              Income
            </NavLink>
            <NavLink
              to="/debts"
              className={({ isActive }) => (isActive ? 'font-medium text-blue-600' : 'text-gray-600')}
            >
              Debt
            </NavLink>
            <NavLink
              to="/goals"
              className={({ isActive }) => (isActive ? 'font-medium text-blue-600' : 'text-gray-600')}
            >
              Goals
            </NavLink>
            <NavLink
              to="/history"
              className={({ isActive }) => (isActive ? 'font-medium text-blue-600' : 'text-gray-600')}
            >
              History
            </NavLink>
            <NavLink
              to="/forecasting"
              className={({ isActive }) => (isActive ? 'font-medium text-blue-600' : 'text-gray-600')}
            >
              Forecasting
            </NavLink>
            <NavLink
              to="/scenarios"
              className={({ isActive }) => (isActive ? 'font-medium text-blue-600' : 'text-gray-600')}
            >
              Scenarios
            </NavLink>
            <NavLink
              to="/coach"
              className={({ isActive }) => (isActive ? 'font-medium text-blue-600' : 'text-gray-600')}
            >
              Coach
            </NavLink>
            <NavLink
              to="/recommendations"
              className={({ isActive }) => (isActive ? 'font-medium text-blue-600' : 'text-gray-600')}
            >
              Recommendations
            </NavLink>
            <NavLink
              to="/notifications"
              className={({ isActive }) => (isActive ? 'font-medium text-blue-600' : 'text-gray-600')}
            >
              Notifications
            </NavLink>
          </nav>
          <div className="ml-auto flex items-center gap-3 text-sm">
            {user && <span className="text-gray-600">{user.username}</span>}
            <button
              type="button"
              onClick={logout}
              className="rounded border border-gray-300 px-2 py-1 text-gray-700"
            >
              Log Out
            </button>
          </div>
        </div>
      </header>
      <Outlet />
    </div>
  )
}
