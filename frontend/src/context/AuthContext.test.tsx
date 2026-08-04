import { act, renderHook, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthProvider, useAuth } from './AuthContext'
import * as authApi from '../api/auth'

vi.mock('../api/auth')

const alice = {
  id: 1,
  username: 'alice',
  email: 'alice@example.com',
  is_active: true,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

beforeEach(() => {
  localStorage.clear()
})

afterEach(() => {
  vi.restoreAllMocks()
  vi.clearAllMocks()
})

describe('AuthProvider', () => {
  it('goes straight to unauthenticated with no stored token', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider })

    await waitFor(() => expect(result.current.status).toBe('unauthenticated'))
  })

  it('bootstraps to authenticated with a valid stored token', async () => {
    localStorage.setItem('auth_token', 'valid-access-token')
    localStorage.setItem('refresh_token', 'valid-refresh-token')
    vi.mocked(authApi.me).mockResolvedValue(alice)

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider })

    await waitFor(() => expect(result.current.status).toBe('authenticated'))
    expect(result.current.user).toEqual(alice)
  })

  it('refreshes and retries once when the stored access token is expired', async () => {
    localStorage.setItem('auth_token', 'expired-access-token')
    localStorage.setItem('refresh_token', 'valid-refresh-token')
    vi.mocked(authApi.me).mockRejectedValueOnce(new Error('expired')).mockResolvedValueOnce(alice)
    vi.mocked(authApi.refresh).mockResolvedValue({
      access_token: 'new-access-token',
      refresh_token: 'new-refresh-token',
      token_type: 'bearer',
    })

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider })

    await waitFor(() => expect(result.current.status).toBe('authenticated'))
    expect(authApi.refresh).toHaveBeenCalledWith({ refresh_token: 'valid-refresh-token' })
    expect(localStorage.getItem('auth_token')).toBe('new-access-token')
    expect(localStorage.getItem('refresh_token')).toBe('new-refresh-token')
  })

  it('clears the session when refresh also fails', async () => {
    localStorage.setItem('auth_token', 'expired-access-token')
    localStorage.setItem('refresh_token', 'expired-refresh-token')
    vi.mocked(authApi.me).mockRejectedValue(new Error('expired'))
    vi.mocked(authApi.refresh).mockRejectedValue(new Error('invalid refresh token'))

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider })

    await waitFor(() => expect(result.current.status).toBe('unauthenticated'))
    expect(localStorage.getItem('auth_token')).toBeNull()
    expect(localStorage.getItem('refresh_token')).toBeNull()
  })

  it('login stores both tokens and authenticates', async () => {
    vi.mocked(authApi.login).mockResolvedValue({
      access_token: 'access-token',
      refresh_token: 'refresh-token',
      token_type: 'bearer',
    })
    vi.mocked(authApi.me).mockResolvedValue(alice)

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider })
    await waitFor(() => expect(result.current.status).toBe('unauthenticated'))

    await act(() => result.current.login('alice', 'correct-password'))

    expect(result.current.status).toBe('authenticated')
    expect(localStorage.getItem('auth_token')).toBe('access-token')
    expect(localStorage.getItem('refresh_token')).toBe('refresh-token')
  })

  it('logout clears both stored tokens and revokes the refresh token server-side', async () => {
    localStorage.setItem('auth_token', 'valid-access-token')
    localStorage.setItem('refresh_token', 'valid-refresh-token')
    vi.mocked(authApi.me).mockResolvedValue(alice)
    vi.mocked(authApi.logout).mockResolvedValue(undefined)

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider })
    await waitFor(() => expect(result.current.status).toBe('authenticated'))

    act(() => result.current.logout())

    expect(result.current.status).toBe('unauthenticated')
    expect(localStorage.getItem('auth_token')).toBeNull()
    expect(localStorage.getItem('refresh_token')).toBeNull()
    expect(authApi.logout).toHaveBeenCalledWith({ refresh_token: 'valid-refresh-token' })
  })

  it('logout still clears local state even if the revocation request fails', async () => {
    localStorage.setItem('auth_token', 'valid-access-token')
    localStorage.setItem('refresh_token', 'valid-refresh-token')
    vi.mocked(authApi.me).mockResolvedValue(alice)
    vi.mocked(authApi.logout).mockRejectedValue(new Error('network error'))

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider })
    await waitFor(() => expect(result.current.status).toBe('authenticated'))

    act(() => result.current.logout())

    expect(result.current.status).toBe('unauthenticated')
    expect(localStorage.getItem('auth_token')).toBeNull()
  })
})
