export interface RegisterRequest {
  username: string
  email: string
  password: string
}

export interface LoginRequest {
  username: string
  password: string
}

// The refresh token is never in a JSON response -- the backend sets it as
// an HttpOnly cookie instead, so this only ever carries the access token.
export interface AccessTokenResponse {
  access_token: string
  token_type: string
}

export type PlatformRole = 'user' | 'admin' | 'super_admin'

export interface UserResponse {
  id: number
  username: string
  email: string
  is_active: boolean
  role: PlatformRole
  created_at: string
  updated_at: string
  email_verified: boolean
}

export interface UpdateProfileRequest {
  username?: string
  email?: string
}

export interface ChangePasswordRequest {
  current_password: string
  new_password: string
}

export interface ForgotPasswordRequest {
  email: string
}

export interface ResetPasswordRequest {
  token: string
  new_password: string
}

export interface VerifyEmailRequest {
  token: string
}

export interface SessionResponse {
  id: number
  issued_at: string
  expires_at: string
  user_agent: string | null
  ip_address: string | null
  is_current: boolean
}
