import { apiDelete, apiGet, apiPost } from './client'
import type {
  AddMemberRequest,
  ChildAccountCreateRequest,
  ChildAccountCreateResponse,
  ChildSummaryResponse,
  HouseholdCreateRequest,
  HouseholdMembershipResponse,
  HouseholdResponse,
} from '../types/households'

export function listMyHouseholds(): Promise<HouseholdResponse[]> {
  return apiGet<HouseholdResponse[]>('/households')
}

export function createHousehold(request: HouseholdCreateRequest): Promise<HouseholdResponse> {
  return apiPost<HouseholdResponse>('/households', request)
}

export function getHousehold(householdId: number): Promise<HouseholdResponse> {
  return apiGet<HouseholdResponse>(`/households/${householdId}`)
}

export function addMember(
  householdId: number,
  request: AddMemberRequest,
): Promise<HouseholdMembershipResponse> {
  return apiPost<HouseholdMembershipResponse>(`/households/${householdId}/members`, request)
}

export function removeMember(householdId: number, userId: number): Promise<void> {
  return apiDelete<void>(`/households/${householdId}/members/${userId}`)
}

export function createChildAccount(
  householdId: number,
  request: ChildAccountCreateRequest,
): Promise<ChildAccountCreateResponse> {
  return apiPost<ChildAccountCreateResponse>(`/households/${householdId}/children`, request)
}

export function listGuardianChildren(): Promise<ChildSummaryResponse[]> {
  return apiGet<ChildSummaryResponse[]>('/guardian/children')
}
