import { NavLink, Outlet } from 'react-router-dom'

function tabClassName({ isActive }: { isActive: boolean }): string {
  return isActive
    ? 'border-b-2 border-blue-600 px-3 py-2 text-sm font-medium text-blue-600'
    : 'border-b-2 border-transparent px-3 py-2 text-sm text-gray-600 hover:text-gray-900'
}

export function AdminLayout() {
  return (
    <div className="mx-auto max-w-4xl p-4">
      <h1 className="text-2xl font-semibold text-gray-900">Admin Console</h1>
      <nav className="mt-4 flex gap-2 border-b border-gray-200">
        <NavLink to="/admin" end className={tabClassName}>
          Overview
        </NavLink>
        <NavLink to="/admin/users" className={tabClassName}>
          Users
        </NavLink>
      </nav>
      <div className="mt-6">
        <Outlet />
      </div>
    </div>
  )
}
