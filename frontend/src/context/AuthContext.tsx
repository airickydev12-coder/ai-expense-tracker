import { createContext, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import * as authApi from '../api/auth'
import { setAuthToken, setUnauthorizedHandler } from '../api/client'
import type { UserResponse } from '../types/auth'

const TOKEN_STORAGE_KEY = 'auth_token'

type AuthState =
  | { status: 'bootstrapping' }
  | { status: 'unauthenticated' }
  | { status: 'authenticated'; user: UserResponse }

interface AuthContextValue {
  status: AuthState['status']
  user: UserResponse | null
  login: (username: string, password: string) => Promise<void>
  register: (username: string, email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

async function establishSession(username: string, password: string): Promise<UserResponse> {
  const token = await authApi.login({ username, password })
  localStorage.setItem(TOKEN_STORAGE_KEY, token.access_token)
  setAuthToken(token.access_token)
  return authApi.me()
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({ status: 'bootstrapping' })

  function clearSession() {
    localStorage.removeItem(TOKEN_STORAGE_KEY)
    setAuthToken(null)
    setState({ status: 'unauthenticated' })
  }

  useEffect(() => {
    setUnauthorizedHandler(clearSession)
    return () => setUnauthorizedHandler(null)
  }, [])

  useEffect(() => {
    const storedToken = localStorage.getItem(TOKEN_STORAGE_KEY)
    if (!storedToken) {
      setState({ status: 'unauthenticated' })
      return
    }

    setAuthToken(storedToken)
    authApi
      .me()
      .then((user) => setState({ status: 'authenticated', user }))
      .catch(() => clearSession())
  }, [])

  async function login(username: string, password: string) {
    const user = await establishSession(username, password)
    setState({ status: 'authenticated', user })
  }

  async function register(username: string, email: string, password: string) {
    await authApi.register({ username, email, password })
    const user = await establishSession(username, password)
    setState({ status: 'authenticated', user })
  }

  function logout() {
    clearSession()
  }

  const value: AuthContextValue = {
    status: state.status,
    user: state.status === 'authenticated' ? state.user : null,
    login,
    register,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
