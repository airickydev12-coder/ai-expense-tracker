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

export type AccountType = 'adult' | 'minor'

export interface UserResponse {
  id: number
  username: string
  email: string
  is_active: boolean
  role: PlatformRole
  created_at: string
  updated_at: string
  email_verified: boolean
  mfa_enabled: boolean
  account_type: AccountType
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

export interface ReauthRequest {
  password: string
}

// Returned by POST /auth/login instead of AccessTokenResponse when the
// account has MFA enabled -- no session/cookie exists yet at this point.
export interface MfaChallengeResponse {
  mfa_required: true
  challenge_token: string
}

export interface MfaVerifyRequest {
  challenge_token: string
  code: string
}

export interface MfaEnrollResponse {
  secret: string
  otpauth_uri: string
}

export interface MfaConfirmRequest {
  code: string
}

export interface MfaRecoveryCodesResponse {
  recovery_codes: string[]
}
