import { act, renderHook, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { AuthProvider, useAuth } from './AuthContext'
import * as authApi from '../api/auth'

vi.mock('../api/auth')

const alice = {
  id: 1,
  username: 'alice',
  email: 'alice@example.com',
  is_active: true,
  role: 'user' as const,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  email_verified: true,
}

afterEach(() => {
  vi.restoreAllMocks()
  vi.clearAllMocks()
})

describe('AuthProvider', () => {
  it('goes to unauthenticated when there is no valid refresh-token cookie', async () => {
    vi.mocked(authApi.refresh).mockRejectedValue(new Error('no session'))

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider })

    await waitFor(() => expect(result.current.status).toBe('unauthenticated'))
  })

  it('bootstraps to authenticated by silently refreshing via the cookie', async () => {
    vi.mocked(authApi.refresh).mockResolvedValue({
      access_token: 'new-access-token',
      token_type: 'bearer',
    })
    vi.mocked(authApi.me).mockResolvedValue(alice)

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider })

    await waitFor(() => expect(result.current.status).toBe('authenticated'))
    expect(result.current.user).toEqual(alice)
  })

  it('clears the session when the silent refresh succeeds but /me fails', async () => {
    vi.mocked(authApi.refresh).mockResolvedValue({
      access_token: 'new-access-token',
      token_type: 'bearer',
    })
    vi.mocked(authApi.me).mockRejectedValue(new Error('expired'))

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider })

    await waitFor(() => expect(result.current.status).toBe('unauthenticated'))
  })

  it('login authenticates without touching localStorage', async () => {
    vi.mocked(authApi.refresh).mockRejectedValue(new Error('no session'))
    vi.mocked(authApi.login).mockResolvedValue({
      access_token: 'access-token',
      token_type: 'bearer',
    })
    vi.mocked(authApi.me).mockResolvedValue(alice)

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider })
    await waitFor(() => expect(result.current.status).toBe('unauthenticated'))

    await act(() => result.current.login('alice', 'correct-password'))

    expect(result.current.status).toBe('authenticated')
    expect(authApi.login).toHaveBeenCalledWith({ username: 'alice', password: 'correct-password' })
  })

  it('logout clears the session and revokes server-side with no arguments', async () => {
    vi.mocked(authApi.refresh).mockResolvedValue({
      access_token: 'new-access-token',
      token_type: 'bearer',
    })
    vi.mocked(authApi.me).mockResolvedValue(alice)
    vi.mocked(authApi.logout).mockResolvedValue(undefined)

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider })
    await waitFor(() => expect(result.current.status).toBe('authenticated'))

    await act(() => result.current.logout())

    expect(result.current.status).toBe('unauthenticated')
    expect(authApi.logout).toHaveBeenCalledWith()
  })

  it('logout still clears local state even if the revocation request fails', async () => {
    vi.mocked(authApi.refresh).mockResolvedValue({
      access_token: 'new-access-token',
      token_type: 'bearer',
    })
    vi.mocked(authApi.me).mockResolvedValue(alice)
    vi.mocked(authApi.logout).mockRejectedValue(new Error('network error'))

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider })
    await waitFor(() => expect(result.current.status).toBe('authenticated'))

    await act(() => result.current.logout())

    expect(result.current.status).toBe('unauthenticated')
  })
})
