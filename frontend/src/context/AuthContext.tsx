import { createContext, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import * as authApi from '../api/auth'
import { setAuthToken, setUnauthorizedHandler } from '../api/client'
import type { UserResponse } from '../types/auth'

const TOKEN_STORAGE_KEY = 'auth_token'
const REFRESH_TOKEN_STORAGE_KEY = 'refresh_token'

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
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

function storeTokens(accessToken: string, refreshToken: string): void {
  localStorage.setItem(TOKEN_STORAGE_KEY, accessToken)
  localStorage.setItem(REFRESH_TOKEN_STORAGE_KEY, refreshToken)
  setAuthToken(accessToken)
}

function clearStoredTokens(): void {
  localStorage.removeItem(TOKEN_STORAGE_KEY)
  localStorage.removeItem(REFRESH_TOKEN_STORAGE_KEY)
  setAuthToken(null)
}

async function establishSession(username: string, password: string): Promise<UserResponse> {
  const token = await authApi.login({ username, password })
  storeTokens(token.access_token, token.refresh_token)
  return authApi.me()
}

let refreshPromise: Promise<boolean> | null = null

/**
 * Attempt one token refresh using the stored refresh token, deduplicating
 * concurrent callers onto a single in-flight attempt -- refresh tokens
 * rotate on use, so two parallel refresh calls would have the second one
 * fail against an already-rotated token even though the session is fine.
 */
function attemptRefresh(): Promise<boolean> {
  if (refreshPromise) return refreshPromise

  refreshPromise = (async () => {
    const storedRefreshToken = localStorage.getItem(REFRESH_TOKEN_STORAGE_KEY)
    if (!storedRefreshToken) return false

    try {
      const token = await authApi.refresh({ refresh_token: storedRefreshToken })
      storeTokens(token.access_token, token.refresh_token)
      return true
    } catch {
      return false
    }
  })().finally(() => {
    refreshPromise = null
  })

  return refreshPromise
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({ status: 'bootstrapping' })

  function clearSession() {
    clearStoredTokens()
    setState({ status: 'unauthenticated' })
  }

  useEffect(() => {
    // Background 401s (a page's API call hitting an expired access token
    // mid-session) get one silent refresh attempt; only clear the session
    // if that also fails. This doesn't retry the original failed request --
    // the caller's own error handling still surfaces it -- but the session
    // itself survives so the next action succeeds.
    setUnauthorizedHandler(() => {
      attemptRefresh().then((refreshed) => {
        if (!refreshed) clearSession()
      })
    })
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
      .catch(() =>
        attemptRefresh().then((refreshed) => {
          if (!refreshed) {
            clearSession()
            return
          }
          authApi
            .me()
            .then((user) => setState({ status: 'authenticated', user }))
            .catch(() => clearSession())
        }),
      )
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

  async function refreshUser() {
    const user = await authApi.me()
    setState({ status: 'authenticated', user })
  }

  const value: AuthContextValue = {
    status: state.status,
    user: state.status === 'authenticated' ? state.user : null,
    login,
    register,
    logout,
    refreshUser,
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
