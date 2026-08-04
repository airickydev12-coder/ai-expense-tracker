import { apiDelete, apiGet, apiPatch, apiPost } from './client'
import type {
  AccessTokenResponse,
  ChangePasswordRequest,
  ForgotPasswordRequest,
  LoginRequest,
  ReauthRequest,
  RegisterRequest,
  ResetPasswordRequest,
  SessionResponse,
  UpdateProfileRequest,
  UserResponse,
  VerifyEmailRequest,
} from '../types/auth'

export function register(request: RegisterRequest): Promise<UserResponse> {
  return apiPost<UserResponse>('/auth/register', request, { skipUnauthorizedHandling: true })
}

export function login(request: LoginRequest): Promise<AccessTokenResponse> {
  return apiPost<AccessTokenResponse>('/auth/login', request, { skipUnauthorizedHandling: true })
}

// No request body: the refresh token travels as an HttpOnly cookie the
// browser attaches automatically, never as JS-readable state.
export function refresh(): Promise<AccessTokenResponse> {
  return apiPost<AccessTokenResponse>('/auth/refresh', undefined, { skipUnauthorizedHandling: true })
}

export function logout(): Promise<void> {
  return apiPost<void>('/auth/logout', undefined, { skipUnauthorizedHandling: true })
}

export function me(): Promise<UserResponse> {
  return apiGet<UserResponse>('/auth/me')
}

export function updateProfile(request: UpdateProfileRequest): Promise<UserResponse> {
  return apiPatch<UserResponse>('/auth/me', request)
}

export function changePassword(request: ChangePasswordRequest): Promise<void> {
  return apiPost<void>('/auth/change-password', request)
}

export function reauth(request: ReauthRequest): Promise<AccessTokenResponse> {
  return apiPost<AccessTokenResponse>('/auth/reauth', request)
}

export function forgotPassword(request: ForgotPasswordRequest): Promise<void> {
  return apiPost<void>('/auth/forgot-password', request)
}

export function resetPassword(request: ResetPasswordRequest): Promise<void> {
  return apiPost<void>('/auth/reset-password', request)
}

export function verifyEmail(request: VerifyEmailRequest): Promise<void> {
  return apiPost<void>('/auth/verify-email', request)
}

export function resendVerification(): Promise<void> {
  return apiPost<void>('/auth/resend-verification', undefined)
}

export function listSessions(): Promise<SessionResponse[]> {
  return apiGet<SessionResponse[]>('/auth/sessions')
}

export function revokeSession(sessionId: number): Promise<void> {
  return apiDelete<void>(`/auth/sessions/${sessionId}`)
}

export function revokeAllSessions(): Promise<void> {
  return apiPost<void>('/auth/sessions/revoke-all', undefined)
}
