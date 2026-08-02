import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { CoachPage } from './CoachPage'
import * as coachApi from '../api/coach'
import * as recommendationsApi from '../api/recommendations'
import type { CoachingSessionDict, FinancialCoachInsightDict, MonthlyReviewDict } from '../types/coach'
import type { RecommendationResponse } from '../types/recommendations'

vi.mock('../api/coach')
vi.mock('../api/recommendations')

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

const debtRecommendations: RecommendationResponse[] = [
  {
    key: 'debt:high_interest_debt',
    priority: 'HIGH',
    category: 'Debt',
    score: 300,
    title: 'High Interest Debt',
    message: 'Card A has a high interest rate of 27.40%.',
    action: 'Prioritize this debt for repayment.',
    rationale: '',
    source_rule: 'HighInterestDebtRule',
    is_actionable: true,
  },
]

const monthlyReview: MonthlyReviewDict = {
  status: 'no_history',
  message: 'No financial snapshot has been recorded yet.',
  last_recorded_snapshot: null,
  generated_at: null,
  period_start: null,
  period_end: null,
  overall_summary: null,
  income_vs_expenses: null,
  cash_flow: null,
  debt_progress: null,
  savings_progress: null,
  goal_status: null,
  health_score: null,
  top_actions: null,
  known_gaps: null,
}

afterEach(() => {
  vi.restoreAllMocks()
  vi.clearAllMocks()
})

beforeEach(() => {
  vi.mocked(coachApi.getFinancialNarrative).mockResolvedValue({
    narrative: 'Your finances look healthy overall.',
  })
  vi.mocked(coachApi.getMonthlyReview).mockResolvedValue(monthlyReview)
  vi.mocked(recommendationsApi.listRecommendationsByCategory).mockResolvedValue(debtRecommendations)
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

  it('renders the financial narrative', async () => {
    vi.mocked(coachApi.listInsights).mockResolvedValue(insights)
    vi.mocked(coachApi.getCoachingSession).mockResolvedValue(session)

    render(<CoachPage />)

    expect(await screen.findByText('Your finances look healthy overall.')).toBeInTheDocument()
  })

  it('renders debt recommendations and fetches an explanation on click', async () => {
    vi.mocked(coachApi.listInsights).mockResolvedValue(insights)
    vi.mocked(coachApi.getCoachingSession).mockResolvedValue(session)
    vi.mocked(coachApi.explainRecommendation).mockResolvedValue({
      recommendation_key: 'debt:high_interest_debt',
      reason: 'Card A has the highest APR.',
      evidence: {
        type: 'debt',
        debt_name: 'Card A',
        debt_balance: 4800,
        interest_rate: 27.4,
        minimum_payment: 145,
        extra_monthly_payment: 250,
        payoff_months_saved: 11,
        total_interest_saved: 620,
        total_debt: 4800,
        total_income: null,
        debt_to_income_ratio: null,
        total_account_balance: null,
        total_goal_progress: null,
      },
      expected_impact: 'Payoff about 11 months sooner.',
      confidence: 'High',
      assumptions: ['Income remains stable.'],
    })

    render(<CoachPage />)

    const explainButton = await screen.findByRole('button', { name: 'Explain' })
    fireEvent.click(explainButton)

    expect(await screen.findByText(/Card A has the highest APR/)).toBeInTheDocument()
  })

  it('shows the monthly review message when there is no history yet', async () => {
    vi.mocked(coachApi.listInsights).mockResolvedValue(insights)
    vi.mocked(coachApi.getCoachingSession).mockResolvedValue(session)

    render(<CoachPage />)

    expect(await screen.findByText('No financial snapshot has been recorded yet.')).toBeInTheDocument()
  })

  it('saves a monthly review and shows the saved confirmation', async () => {
    vi.mocked(coachApi.listInsights).mockResolvedValue(insights)
    vi.mocked(coachApi.getCoachingSession).mockResolvedValue(session)

    const okReview: MonthlyReviewDict = {
      status: 'ok',
      message: null,
      last_recorded_snapshot: null,
      generated_at: null,
      period_start: '2026-07-01T00:00:00+00:00',
      period_end: '2026-08-01T00:00:00+00:00',
      overall_summary: 'Overall summary.',
      income_vs_expenses: null,
      cash_flow: null,
      debt_progress: null,
      savings_progress: null,
      goal_status: null,
      health_score: null,
      top_actions: null,
      known_gaps: null,
    }

    vi.mocked(coachApi.getMonthlyReview).mockResolvedValue(okReview)
    vi.mocked(coachApi.saveMonthlyReview).mockResolvedValue({
      ...okReview,
      generated_at: '2026-08-02T12:00:00+00:00',
    })

    render(<CoachPage />)

    const saveButton = await screen.findByRole('button', { name: 'Save This Review' })
    fireEvent.click(saveButton)

    expect(await screen.findByText(/Saved/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Save This Review' })).not.toBeInTheDocument()
  })
})
