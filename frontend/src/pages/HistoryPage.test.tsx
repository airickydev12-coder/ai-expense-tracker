import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { HistoryPage } from './HistoryPage'
import * as historyApi from '../api/history'

vi.mock('../api/history')

const snapshot1 = {
  timestamp: '2026-07-01T12:00:00+00:00',
  total_income: 3000,
  total_expenses: 1500,
  net_cash_flow: 1500,
  total_account_balance: 5000,
  total_goal_progress: 250,
  total_debt: 2000,
  net_worth: 3000,
  health_score: 65,
  health_status: 'Fair',
} as const

const snapshot2 = { ...snapshot1, timestamp: '2026-08-01T12:00:00+00:00', net_worth: 3500 }

const trends = {
  net_worth: { direction: 'Improving' as const, change: 500 },
  cash_flow: { direction: 'Stable' as const, change: 0 },
  income: { direction: 'Stable' as const, change: 0 },
  expenses: { direction: 'Stable' as const, change: 0 },
  health_score: { direction: 'Stable' as const, change: 5 },
  overall_momentum: 'Positive' as const,
}

afterEach(() => {
  vi.restoreAllMocks()
  vi.clearAllMocks()
})

describe('HistoryPage', () => {
  it('renders snapshots and trends once loaded', async () => {
    vi.mocked(historyApi.listHistory).mockResolvedValue([snapshot1, snapshot2])
    vi.mocked(historyApi.getTrends).mockResolvedValue(trends)

    render(<HistoryPage />)

    expect(await screen.findByText('Improving')).toBeInTheDocument()
    expect(screen.getByText('Positive')).toBeInTheDocument()
    expect(screen.getByText('$3000.00')).toBeInTheDocument()
    expect(screen.getByText('$3500.00')).toBeInTheDocument()
  })

  it('records a new snapshot and refetches', async () => {
    vi.mocked(historyApi.listHistory)
      .mockResolvedValueOnce([snapshot1])
      .mockResolvedValueOnce([snapshot1, snapshot2])
    vi.mocked(historyApi.getTrends).mockResolvedValue(trends)
    vi.mocked(historyApi.recordSnapshot).mockResolvedValue(snapshot2)

    render(<HistoryPage />)

    await screen.findByText('$3000.00')
    fireEvent.click(screen.getByRole('button', { name: 'Record Snapshot Now' }))

    expect(await screen.findByText('$3500.00')).toBeInTheDocument()
    expect(historyApi.recordSnapshot).toHaveBeenCalled()
    expect(historyApi.listHistory).toHaveBeenCalledTimes(2)
  })

  it('renders an error message when history fails to load', async () => {
    vi.mocked(historyApi.listHistory).mockRejectedValue(new Error('Network error'))
    vi.mocked(historyApi.getTrends).mockResolvedValue(trends)

    render(<HistoryPage />)

    expect(await screen.findByText(/Failed to load history/i)).toBeInTheDocument()
  })
})
