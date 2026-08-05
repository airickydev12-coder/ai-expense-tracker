import { createContext, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import * as authApi from '../api/auth'
import { setAuthToken, setUnauthorizedHandler } from '../api/client'
import type { UserResponse } from '../types/auth'

type AuthState =
  | { status: 'bootstrapping' }
  | { status: 'unauthenticated' }
  | { status: 'authenticated'; user: UserResponse }

export type LoginOutcome =
  | { status: 'authenticated' }
  | { status: 'mfa_required'; challengeToken: string }

interface AuthContextValue {
  status: AuthState['status']
  user: UserResponse | null
  login: (username: string, password: string) => Promise<LoginOutcome>
  verifyMfa: (challengeToken: string, code: string) => Promise<void>
  register: (username: string, email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

let refreshPromise: Promise<boolean> | null = null

/**
 * Attempt one token refresh using the HttpOnly refresh-token cookie (sent
 * automatically by the browser), deduplicating concurrent callers onto a
 * single in-flight attempt -- the refresh token rotates on use, so two
 * parallel refresh calls would have the second one fail against an
 * already-rotated cookie even though the session is fine.
 */
function attemptRefresh(): Promise<boolean> {
  if (refreshPromise) return refreshPromise

  refreshPromise = authApi
    .refresh()
    .then((token) => {
      setAuthToken(token.access_token)
      return true
    })
    .catch(() => false)
    .finally(() => {
      refreshPromise = null
    })

  return refreshPromise
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({ status: 'bootstrapping' })

  function clearSession() {
    setAuthToken(null)
    setState({ status: 'unauthenticated' })
  }

  useEffect(() => {
    // Background 401s (a page's API call hitting an expired in-memory
    // access token mid-session) get one silent refresh attempt; only clear
    // the session if that also fails. This doesn't retry the original
    // failed request -- the caller's own error handling still surfaces it
    // -- but the session itself survives so the next action succeeds.
    setUnauthorizedHandler(() => {
      attemptRefresh().then((refreshed) => {
        if (!refreshed) clearSession()
      })
    })
    return () => setUnauthorizedHandler(null)
  }, [])

  useEffect(() => {
    // The access token lives in memory only now (never persisted to
    // localStorage), so every fresh page load starts from nothing and must
    // re-establish the session via the HttpOnly refresh-token cookie, if
    // one exists -- there's no stored access token to try first anymore.
    attemptRefresh().then((refreshed) => {
      if (!refreshed) {
        setState({ status: 'unauthenticated' })
        return
      }
      authApi
        .me()
        .then((user) => setState({ status: 'authenticated', user }))
        .catch(() => clearSession())
    })
  }, [])

  async function login(username: string, password: string): Promise<LoginOutcome> {
    const result = await authApi.login({ username, password })

    if ('mfa_required' in result) {
      // No session/cookie exists yet -- the caller (LoginPage) must collect
      // a TOTP/recovery code and call verifyMfa() to actually finish.
      return { status: 'mfa_required', challengeToken: result.challenge_token }
    }

    setAuthToken(result.access_token)
    const user = await authApi.me()
    setState({ status: 'authenticated', user })
    return { status: 'authenticated' }
  }

  async function verifyMfa(challengeToken: string, code: string): Promise<void> {
    const token = await authApi.verifyMfa({ challenge_token: challengeToken, code })
    setAuthToken(token.access_token)
    const user = await authApi.me()
    setState({ status: 'authenticated', user })
  }

  async function register(username: string, email: string, password: string) {
    await authApi.register({ username, email, password })
    // A brand-new account never has MFA enabled (enrollment requires being
    // logged in first), so this always resolves 'authenticated' -- routed
    // through login() anyway to keep exactly one place that turns a
    // successful credential check into session state.
    await login(username, password)
  }

  async function logout() {
    // Unlike the old localStorage-based logout, this *must* wait for the
    // response: an HttpOnly cookie can only be cleared by the server's
    // Set-Cookie header, so clearing local state before that response
    // lands would show "logged out" while the browser is still silently
    // holding a valid refresh-token cookie. The catch still clears local
    // state even if the request itself fails outright (offline, etc.), so
    // a network failure doesn't strand the user "logged in" with no way
    // to retry -- it just means the cookie may persist until it expires
    // naturally in that edge case.
    try {
      await authApi.logout()
    } catch {
      // Ignored -- see comment above.
    } finally {
      clearSession()
    }
  }

  async function refreshUser() {
    const user = await authApi.me()
    setState({ status: 'authenticated', user })
  }

  const value: AuthContextValue = {
    status: state.status,
    user: state.status === 'authenticated' ? state.user : null,
    login,
    verifyMfa,
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
