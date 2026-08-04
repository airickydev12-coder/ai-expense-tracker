import { apiGet, apiPatch, apiPost } from './client'
import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  UpdateProfileRequest,
  UserResponse,
} from '../types/auth'

export function register(request: RegisterRequest): Promise<UserResponse> {
  return apiPost<UserResponse>('/auth/register', request)
}

export function login(request: LoginRequest): Promise<TokenResponse> {
  return apiPost<TokenResponse>('/auth/login', request)
}

export function me(): Promise<UserResponse> {
  return apiGet<UserResponse>('/auth/me')
}

export function updateProfile(request: UpdateProfileRequest): Promise<UserResponse> {
  return apiPatch<UserResponse>('/auth/me', request)
}
