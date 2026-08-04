import { apiGet, apiPatch, apiPost } from './client'
import type {
  ChangePasswordRequest,
  ForgotPasswordRequest,
  LoginRequest,
  LogoutRequest,
  RefreshRequest,
  RegisterRequest,
  ResetPasswordRequest,
  TokenResponse,
  UpdateProfileRequest,
  UserResponse,
} from '../types/auth'

export function register(request: RegisterRequest): Promise<UserResponse> {
  return apiPost<UserResponse>('/auth/register', request, { skipUnauthorizedHandling: true })
}

export function login(request: LoginRequest): Promise<TokenResponse> {
  return apiPost<TokenResponse>('/auth/login', request, { skipUnauthorizedHandling: true })
}

export function refresh(request: RefreshRequest): Promise<TokenResponse> {
  return apiPost<TokenResponse>('/auth/refresh', request, { skipUnauthorizedHandling: true })
}

export function logout(request: LogoutRequest): Promise<void> {
  return apiPost<void>('/auth/logout', request, { skipUnauthorizedHandling: true })
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

export function forgotPassword(request: ForgotPasswordRequest): Promise<void> {
  return apiPost<void>('/auth/forgot-password', request)
}

export function resetPassword(request: ResetPasswordRequest): Promise<void> {
  return apiPost<void>('/auth/reset-password', request)
}
