import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { GoalsPage } from './GoalsPage'
import * as goalsApi from '../api/goals'

vi.mock('../api/goals')

const emergencyFund = {
  id: 1,
  name: 'Emergency Fund',
  target_amount: 1000,
  current_amount: 250,
} as const

const ledgerEntries = [
  {
    entry_id: 'entry-1',
    goal_id: 1,
    entry_type: 'CONTRIBUTION' as const,
    amount: 250,
    effective_date: '2026-08-01',
    created_at: '2026-08-01T12:00:00+00:00',
    source: 'MANUAL',
    note: '',
    correlation_id: null,
    reverses_entry_id: null,
  },
]

afterEach(() => {
  vi.restoreAllMocks()
  vi.clearAllMocks()
})

describe('GoalsPage', () => {
  it('renders the goal list once loaded', async () => {
    vi.mocked(goalsApi.listGoals).mockResolvedValue([emergencyFund])

    render(<GoalsPage />)

    expect(await screen.findByText('Emergency Fund')).toBeInTheDocument()
  })

  it('submits the create form and refetches the list', async () => {
    vi.mocked(goalsApi.listGoals)
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([emergencyFund])
    vi.mocked(goalsApi.createGoal).mockResolvedValue(emergencyFund)

    render(<GoalsPage />)

    await screen.findByText('No goals yet.')

    fireEvent.change(screen.getByLabelText('Name'), { target: { value: 'Emergency Fund' } })
    fireEvent.change(screen.getByLabelText('Target Amount'), { target: { value: '1000' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add Goal' }))

    expect(await screen.findByText('Emergency Fund')).toBeInTheDocument()
    expect(goalsApi.createGoal).toHaveBeenCalledWith({
      name: 'Emergency Fund',
      target_amount: 1000,
      current_amount: 0,
    })
  })

  it('deletes a goal after confirmation and refetches the list', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    vi.mocked(goalsApi.listGoals)
      .mockResolvedValueOnce([emergencyFund])
      .mockResolvedValueOnce([])
    vi.mocked(goalsApi.deleteGoal).mockResolvedValue(emergencyFund)

    render(<GoalsPage />)

    await screen.findByText('Emergency Fund')
    fireEvent.click(screen.getByRole('button', { name: 'Delete' }))

    expect(await screen.findByText('No goals yet.')).toBeInTheDocument()
    expect(goalsApi.deleteGoal).toHaveBeenCalledWith(1)
  })

  it('renders an error message when the list fails to load', async () => {
    vi.mocked(goalsApi.listGoals).mockRejectedValue(new Error('Network error'))

    render(<GoalsPage />)

    expect(await screen.findByText(/Failed to load goals/i)).toBeInTheDocument()
  })

  it('expands the ledger panel and submits a contribution', async () => {
    vi.mocked(goalsApi.listGoals).mockResolvedValue([emergencyFund])
    vi.mocked(goalsApi.getGoalLedgerEntries).mockResolvedValue(ledgerEntries)
    vi.mocked(goalsApi.reconcileGoal).mockResolvedValue({
      is_reconciled: true,
      ledger_balance: 250,
    })
    vi.mocked(goalsApi.contributeToGoal).mockResolvedValue({
      ...emergencyFund,
      current_amount: 350,
    })

    render(<GoalsPage />)

    await screen.findByText('Emergency Fund')
    fireEvent.click(screen.getByRole('button', { name: 'View Ledger' }))

    expect(await screen.findByText('Reconciled')).toBeInTheDocument()
    expect(screen.getByText('CONTRIBUTION')).toBeInTheDocument()

    fireEvent.change(screen.getByPlaceholderText('Amount'), { target: { value: '100' } })
    fireEvent.click(screen.getByRole('button', { name: 'Contribute' }))

    expect(goalsApi.contributeToGoal).toHaveBeenCalledWith(1, { amount: 100 })
  })
})
