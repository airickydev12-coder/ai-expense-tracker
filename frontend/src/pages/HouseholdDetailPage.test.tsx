import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { HouseholdDetailPage } from './HouseholdDetailPage'
import * as householdsApi from '../api/households'
import * as authContext from '../context/AuthContext'
import * as stepUpAuthContext from '../context/StepUpAuthContext'
import type { UserResponse } from '../types/auth'

vi.mock('../api/households')
vi.mock('../context/AuthContext')
vi.mock('../context/StepUpAuthContext')

const owner: UserResponse = {
  id: 1,
  username: 'owner',
  email: 'owner@example.com',
  is_active: true,
  role: 'user',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  email_verified: true,
  mfa_enabled: false,
  account_type: 'adult',
}

const household = {
  id: 1,
  name: 'Smith Family',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  members: [
    { user_id: 1, household_role: 'owner' as const, joined_at: '2026-01-01T00:00:00Z' },
    { user_id: 2, household_role: 'adult_member' as const, joined_at: '2026-01-01T00:00:00Z' },
  ],
}

function mockAuth(user: UserResponse) {
  vi.mocked(authContext.useAuth).mockReturnValue({
    status: 'authenticated',
    user,
    login: vi.fn(),
    verifyMfa: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    refreshUser: vi.fn(),
  })
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/households/1']}>
      <Routes>
        <Route path="/households/:id" element={<HouseholdDetailPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  mockAuth(owner)
  vi.mocked(stepUpAuthContext.useStepUpAuth).mockReturnValue({
    runWithStepUp: (action) => action(),
  })
})

afterEach(() => {
  vi.restoreAllMocks()
  vi.clearAllMocks()
})

describe('HouseholdDetailPage', () => {
  it('renders the household name and members once loaded', async () => {
    vi.mocked(householdsApi.getHousehold).mockResolvedValue(household)

    renderPage()

    expect(await screen.findByText('Smith Family')).toBeInTheDocument()
    expect(screen.getByText(/User 1/)).toBeInTheDocument()
    expect(screen.getByText(/User 2/)).toBeInTheDocument()
  })

  it('lets the owner add a member', async () => {
    vi.mocked(householdsApi.getHousehold)
      .mockResolvedValueOnce(household)
      .mockResolvedValueOnce({
        ...household,
        members: [
          ...household.members,
          { user_id: 3, household_role: 'adult_member' as const, joined_at: '2026-01-01T00:00:00Z' },
        ],
      })
    vi.mocked(householdsApi.addMember).mockResolvedValue({
      user_id: 3,
      household_role: 'adult_member',
      joined_at: '2026-01-01T00:00:00Z',
    })

    renderPage()
    await screen.findByText('Smith Family')

    fireEvent.change(screen.getByLabelText('User ID'), { target: { value: '3' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add Member' }))

    expect(await screen.findByText(/User 3/)).toBeInTheDocument()
    expect(householdsApi.addMember).toHaveBeenCalledWith(1, {
      user_id: 3,
      household_role: 'adult_member',
    })
  })

  it('lets the owner remove another member after confirmation', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    vi.mocked(householdsApi.getHousehold)
      .mockResolvedValueOnce(household)
      .mockResolvedValueOnce({ ...household, members: [household.members[0]] })
    vi.mocked(householdsApi.removeMember).mockResolvedValue(undefined)

    renderPage()
    await screen.findByText(/User 2/)

    fireEvent.click(screen.getByRole('button', { name: 'Remove' }))

    expect(householdsApi.removeMember).toHaveBeenCalledWith(1, 2)
  })

  it('creates a child account via the form, using step-up', async () => {
    vi.mocked(householdsApi.getHousehold).mockResolvedValue(household)
    vi.mocked(householdsApi.createChildAccount).mockResolvedValue({
      child: {
        id: 4,
        username: 'kiddo',
        email: 'kiddo@example.com',
        is_active: true,
        role: 'user',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
        email_verified: false,
        mfa_enabled: false,
        account_type: 'minor',
      },
      relationship: {
        id: 1,
        guardian_user_id: 1,
        child_user_id: 4,
        status: 'active',
        created_at: '2026-01-01T00:00:00Z',
        revoked_at: null,
      },
      learning_profile: {
        user_id: 4,
        age_band: '6-9',
        ai_coach_enabled: true,
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      },
      consent_record: {
        id: 1,
        subject_user_id: 4,
        consented_by_user_id: 1,
        consent_type: 'account_creation',
        policy_version: 'v1',
        status: 'granted',
        granted_at: '2026-01-01T00:00:00Z',
        revoked_at: null,
        evidence: 'guardian confirmed via this form',
        created_at: '2026-01-01T00:00:00Z',
      },
    })

    renderPage()
    await screen.findByText('Smith Family')

    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'kiddo' } })
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'kiddo@example.com' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'correct-password' } })
    fireEvent.change(screen.getByLabelText('Consent evidence'), {
      target: { value: 'guardian confirmed via this form' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Create Child Account' }))

    expect(await screen.findByText('Created child account "kiddo".')).toBeInTheDocument()
    expect(householdsApi.createChildAccount).toHaveBeenCalledWith(1, {
      username: 'kiddo',
      email: 'kiddo@example.com',
      password: 'correct-password',
      age_band: '6-9',
      policy_version: 'v1',
      evidence: 'guardian confirmed via this form',
    })
  })

  it('hides management controls for a non-manager member', async () => {
    mockAuth({ ...owner, id: 2 })
    vi.mocked(householdsApi.getHousehold).mockResolvedValue(household)

    renderPage()
    await screen.findByText('Smith Family')

    expect(screen.queryByLabelText('User ID')).not.toBeInTheDocument()
    expect(screen.queryByText('Add a Child Account')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Leave' })).toBeInTheDocument()
  })
})
