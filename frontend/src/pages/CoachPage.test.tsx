import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { CoachPage } from './CoachPage'
import * as coachApi from '../api/coach'
import type { CoachingSessionDict, FinancialCoachInsightDict } from '../types/coach'

vi.mock('../api/coach')

const insights: FinancialCoachInsightDict[] = [
  {
    key: 'low-savings',
    title: 'Low Savings Rate',
    message: 'Your savings rate is below target.',
    category: 'Savings',
    severity: 'Critical',
    metric: 'Savings Rate',
    current_value: 5,
    benchmark_value: 20,
    action: 'Increase monthly savings',
  },
]

const session: CoachingSessionDict = {
  generated_at: '2026-08-01T12:00:00+00:00',
  financial_health_score: 65,
  financial_health_status: 'Fair',
  summary: 'Your finances are stable but could improve.',
  advice: [
    {
      key: 'advice-1',
      title: 'Pay down credit card debt',
      message: 'Focus extra payments on your highest-interest debt.',
      action: 'Apply an extra $100/month',
      reason: 'Reduces interest paid over time',
      priority: 'Warning',
      category: 'Debt',
      expected_impact: 'Saves $500 in interest',
      source_scenario: 'Extra Debt Payment',
      score: 80,
      warnings: [],
    },
  ],
  explanations: [
    {
      advice_key: 'advice-1',
      summary: 'Paying more reduces total interest.',
      why_it_matters: 'High-interest debt compounds quickly.',
      projected_effects: ['Debt paid off 6 months sooner'],
      assumptions: [],
      risks: [],
    },
  ],
  insights,
  next_steps: ['Set up an automatic transfer to savings'],
  warnings: [],
}

afterEach(() => {
  vi.restoreAllMocks()
  vi.clearAllMocks()
})

describe('CoachPage', () => {
  it('renders both the insights and session sections from a realistic fixture', async () => {
    vi.mocked(coachApi.listInsights).mockResolvedValue(insights)
    vi.mocked(coachApi.getCoachingSession).mockResolvedValue(session)

    render(<CoachPage />)

    expect((await screen.findAllByText('Low Savings Rate')).length).toBeGreaterThan(0)
    expect(await screen.findByText('Your finances are stable but could improve.')).toBeInTheDocument()
    expect(screen.getByText('Pay down credit card debt')).toBeInTheDocument()
  })

  it('renders a severity badge with the expected text', async () => {
    vi.mocked(coachApi.listInsights).mockResolvedValue(insights)
    vi.mocked(coachApi.getCoachingSession).mockResolvedValue(session)

    render(<CoachPage />)

    const criticalBadges = await screen.findAllByText('Critical')
    expect(criticalBadges.length).toBeGreaterThan(0)
  })

  it('shows an error for insights while the session still renders successfully', async () => {
    vi.mocked(coachApi.listInsights).mockRejectedValue(new Error('Network error'))
    vi.mocked(coachApi.getCoachingSession).mockResolvedValue(session)

    render(<CoachPage />)

    expect(await screen.findByText(/Failed to load insights/i)).toBeInTheDocument()
    expect(await screen.findByText('Your finances are stable but could improve.')).toBeInTheDocument()
  })
})
