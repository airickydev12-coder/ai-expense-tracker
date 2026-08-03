import { fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { RecommendationsPage } from './RecommendationsPage'
import * as recommendationsApi from '../api/recommendations'

vi.mock('../api/recommendations')

const dining = {
  key: 'budget:reduce_dining_expenses',
  priority: 'HIGH',
  category: 'Budget',
  score: 300,
  title: 'Reduce dining expenses',
  message: 'Dining expenses are above your target.',
  action: 'Set a weekly dining limit.',
  rationale: 'Dining represents a large share of spending.',
  source_rule: 'DiningSpendingRule',
  is_actionable: true,
} as const

const categories = [{ name: 'BUDGET', value: 'Budget' }]
const priorities = [{ name: 'HIGH', value: 3, score: 300 }]

const dismissedRecord = {
  recommendation_key: dining.key,
  status: 'DISMISSED',
  created_at: '2026-01-01T00:00:00+00:00',
  updated_at: '2026-01-01T00:00:00+00:00',
  note: '',
}

afterEach(() => {
  vi.restoreAllMocks()
  vi.clearAllMocks()
})

describe('RecommendationsPage', () => {
  it('renders the recommendation list once loaded', async () => {
    vi.mocked(recommendationsApi.getFilteredRecommendations).mockResolvedValue([dining])
    vi.mocked(recommendationsApi.getRecommendationCategories).mockResolvedValue(categories)
    vi.mocked(recommendationsApi.getRecommendationPriorities).mockResolvedValue(priorities)

    render(<RecommendationsPage />)

    const title = await screen.findByText('Reduce dining expenses')
    const listItem = title.closest('li')
    expect(listItem).not.toBeNull()

    const scoped = within(listItem as HTMLElement)
    expect(scoped.getByText('HIGH')).toBeInTheDocument()
    expect(scoped.getByText('Budget')).toBeInTheDocument()
  })

  it('dismisses a recommendation and refetches the list', async () => {
    vi.mocked(recommendationsApi.getFilteredRecommendations)
      .mockResolvedValueOnce([dining])
      .mockResolvedValueOnce([])
    vi.mocked(recommendationsApi.getRecommendationCategories).mockResolvedValue(categories)
    vi.mocked(recommendationsApi.getRecommendationPriorities).mockResolvedValue(priorities)
    vi.mocked(recommendationsApi.dismissRecommendation).mockResolvedValue(dismissedRecord)

    render(<RecommendationsPage />)

    await screen.findByText('Reduce dining expenses')
    fireEvent.click(screen.getByRole('button', { name: 'Dismiss' }))

    expect(await screen.findByText('No recommendations right now.')).toBeInTheDocument()
    expect(recommendationsApi.dismissRecommendation).toHaveBeenCalledWith(dining.key)
  })

  it('refetches with the selected category filter', async () => {
    vi.mocked(recommendationsApi.getFilteredRecommendations).mockResolvedValue([dining])
    vi.mocked(recommendationsApi.getRecommendationCategories).mockResolvedValue(categories)
    vi.mocked(recommendationsApi.getRecommendationPriorities).mockResolvedValue(priorities)

    render(<RecommendationsPage />)

    await screen.findByText('Reduce dining expenses')

    fireEvent.change(screen.getByLabelText('Category'), { target: { value: 'Budget' } })

    expect(await screen.findByText('Reduce dining expenses')).toBeInTheDocument()
    expect(recommendationsApi.getFilteredRecommendations).toHaveBeenLastCalledWith({
      category: 'Budget',
      priority: '',
    })
  })

  it('renders an error message when the list fails to load', async () => {
    vi.mocked(recommendationsApi.getFilteredRecommendations).mockRejectedValue(new Error('Network error'))
    vi.mocked(recommendationsApi.getRecommendationCategories).mockResolvedValue([])
    vi.mocked(recommendationsApi.getRecommendationPriorities).mockResolvedValue([])

    render(<RecommendationsPage />)

    expect(await screen.findByText(/Failed to load recommendations/i)).toBeInTheDocument()
  })
})
