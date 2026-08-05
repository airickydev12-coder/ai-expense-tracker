import type { UserResponse } from './auth'

export type HouseholdRole = 'owner' | 'guardian' | 'adult_member' | 'child_learner'

export type RelationshipStatus = 'pending' | 'active' | 'revoked'

export type AgeBand = '6-9' | '10-13' | '14-17'

export interface HouseholdCreateRequest {
  name: string
}

export interface HouseholdMembershipResponse {
  user_id: number
  household_role: HouseholdRole
  joined_at: string
}

export interface HouseholdResponse {
  id: number
  name: string
  created_at: string
  updated_at: string
  members: HouseholdMembershipResponse[]
}

export interface AddMemberRequest {
  user_id: number
  household_role: HouseholdRole
}

export interface GuardianChildRelationshipResponse {
  id: number
  guardian_user_id: number
  child_user_id: number
  status: RelationshipStatus
  created_at: string
  revoked_at: string | null
}

export interface LearningProfileResponse {
  user_id: number
  age_band: AgeBand
  ai_coach_enabled: boolean
  created_at: string
  updated_at: string
}

export interface ChildAccountCreateRequest {
  username: string
  email: string
  password: string
  age_band: AgeBand
  policy_version: string
  evidence: string
}

export interface ConsentRecordResponse {
  id: number
  subject_user_id: number
  consented_by_user_id: number | null
  consent_type: string
  policy_version: string
  status: string
  granted_at: string | null
  revoked_at: string | null
  evidence: string
  created_at: string
}

export interface ChildAccountCreateResponse {
  child: UserResponse
  relationship: GuardianChildRelationshipResponse
  learning_profile: LearningProfileResponse
  consent_record: ConsentRecordResponse
}

export interface ChildSummaryResponse {
  child: UserResponse
  relationship: GuardianChildRelationshipResponse
}
