import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { DashboardPage } from './DashboardPage'
import * as dashboardApi from '../api/dashboard'
import * as healthApi from '../api/health'

vi.mock('../api/dashboard')
vi.mock('../api/health')

describe('DashboardPage', () => {
  it('renders dashboard data once loaded', async () => {
    vi.mocked(dashboardApi.getDashboard).mockResolvedValue({
      total_expenses: 500,
      average_expense: 50,
      highest_expense: { id: 1, name: 'Rent', category: 'Housing', amount: 200 },
      lowest_expense: { id: 2, name: 'Coffee', category: 'Food', amount: 5 },
      category_totals: { Housing: 200, Food: 50 },
      budget_count: 3,
      monthly_budget: 1000,
      remaining_budget: 500,
      budget_used_percent: 50,
      recommendation_count: 2,
      health_score: 80,
      health_status: 'Good',
    })
    vi.mocked(healthApi.getHealth).mockResolvedValue({
      status: 'healthy',
      service: 'AI Expense Tracker API',
      version: '1.0.0',
    })

    render(<DashboardPage />)

    expect(await screen.findByText(/healthy/i)).toBeInTheDocument()
    expect(await screen.findByText(/Rent/)).toBeInTheDocument()
  })

  it('renders an error message when the API call fails', async () => {
    vi.mocked(dashboardApi.getDashboard).mockRejectedValue(new Error('Network error'))
    vi.mocked(healthApi.getHealth).mockResolvedValue({
      status: 'healthy',
      service: 'AI Expense Tracker API',
      version: '1.0.0',
    })

    render(<DashboardPage />)

    expect(await screen.findByText(/Failed to load dashboard/i)).toBeInTheDocument()
  })
})
