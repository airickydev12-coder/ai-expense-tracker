import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { HouseholdsPage } from './HouseholdsPage'
import * as householdsApi from '../api/households'

vi.mock('../api/households')

const household = {
  id: 1,
  name: 'Smith Family',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  members: [{ user_id: 1, household_role: 'owner' as const, joined_at: '2026-01-01T00:00:00Z' }],
}

const childSummary = {
  child: {
    id: 2,
    username: 'kiddo',
    email: 'kiddo@example.com',
    is_active: true,
    role: 'user' as const,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    email_verified: false,
    mfa_enabled: false,
    account_type: 'minor' as const,
  },
  relationship: {
    id: 1,
    guardian_user_id: 1,
    child_user_id: 2,
    status: 'active' as const,
    created_at: '2026-01-01T00:00:00Z',
    revoked_at: null,
  },
}

function renderPage() {
  return render(
    <MemoryRouter>
      <HouseholdsPage />
    </MemoryRouter>,
  )
}

afterEach(() => {
  vi.restoreAllMocks()
  vi.clearAllMocks()
})

describe('HouseholdsPage', () => {
  it('renders the household list once loaded', async () => {
    vi.mocked(householdsApi.listMyHouseholds).mockResolvedValue([household])
    vi.mocked(householdsApi.listGuardianChildren).mockResolvedValue([])

    renderPage()

    expect(await screen.findByText('Smith Family')).toBeInTheDocument()
  })

  it('shows linked children', async () => {
    vi.mocked(householdsApi.listMyHouseholds).mockResolvedValue([])
    vi.mocked(householdsApi.listGuardianChildren).mockResolvedValue([childSummary])

    renderPage()

    expect(await screen.findByText('kiddo')).toBeInTheDocument()
  })

  it('submits the create-household form and refetches the list', async () => {
    vi.mocked(householdsApi.listMyHouseholds)
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([household])
    vi.mocked(householdsApi.listGuardianChildren).mockResolvedValue([])
    vi.mocked(householdsApi.createHousehold).mockResolvedValue(household)

    renderPage()

    await screen.findByText("You don't belong to any households yet.")

    fireEvent.change(screen.getByLabelText('New household name'), {
      target: { value: 'Smith Family' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Create Household' }))

    expect(await screen.findByText('Smith Family')).toBeInTheDocument()
    expect(householdsApi.createHousehold).toHaveBeenCalledWith({ name: 'Smith Family' })
  })

  it('renders an error message when the list fails to load', async () => {
    vi.mocked(householdsApi.listMyHouseholds).mockRejectedValue(new Error('Network error'))
    vi.mocked(householdsApi.listGuardianChildren).mockResolvedValue([])

    renderPage()

    expect(await screen.findByText(/Failed to load households/i)).toBeInTheDocument()
  })
})
