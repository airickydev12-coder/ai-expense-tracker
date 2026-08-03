import { fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { RecurringExpensesPage } from './RecurringExpensesPage'
import * as recurringExpensesApi from '../api/recurringExpenses'

vi.mock('../api/recurringExpenses')

const streaming = {
  id: 1,
  name: 'Streaming Subscription',
  category: 'Entertainment',
  amount: 15.99,
  frequency: 'MONTHLY',
  next_occurrence: '2026-09-01',
  is_active: true,
} as const

afterEach(() => {
  vi.restoreAllMocks()
  vi.clearAllMocks()
})

describe('RecurringExpensesPage', () => {
  it('renders the recurring expense list once loaded', async () => {
    vi.mocked(recurringExpensesApi.listRecurringExpenseTemplates).mockResolvedValue([streaming])

    render(<RecurringExpensesPage />)

    const title = await screen.findByText('Streaming Subscription')
    const listItem = title.closest('li')
    expect(listItem).not.toBeNull()
    expect(within(listItem as HTMLElement).getByText('Active')).toBeInTheDocument()
  })

  it('submits the create form and refetches the list', async () => {
    vi.mocked(recurringExpensesApi.listRecurringExpenseTemplates)
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([streaming])
    vi.mocked(recurringExpensesApi.createRecurringExpenseTemplate).mockResolvedValue(streaming)

    render(<RecurringExpensesPage />)

    await screen.findByText('No recurring expenses yet.')

    fireEvent.change(screen.getByLabelText('Name'), { target: { value: 'Streaming Subscription' } })
    fireEvent.change(screen.getByLabelText('Amount'), { target: { value: '15.99' } })
    fireEvent.change(screen.getByLabelText('Next Occurrence'), { target: { value: '2026-09-01' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add Recurring Expense' }))

    expect(await screen.findByText('Streaming Subscription')).toBeInTheDocument()
    expect(recurringExpensesApi.createRecurringExpenseTemplate).toHaveBeenCalledWith({
      name: 'Streaming Subscription',
      category: 'Food',
      amount: 15.99,
      frequency: 'MONTHLY',
      next_occurrence: '2026-09-01',
      is_active: true,
    })
  })

  it('generates due expenses and shows a confirmation message', async () => {
    vi.mocked(recurringExpensesApi.listRecurringExpenseTemplates).mockResolvedValue([streaming])
    vi.mocked(recurringExpensesApi.generateDueExpenses).mockResolvedValue({
      generated_count: 2,
      expense_ids: [10, 11],
    })

    render(<RecurringExpensesPage />)

    await screen.findByText('Streaming Subscription')
    fireEvent.click(screen.getByRole('button', { name: 'Generate Due Expenses' }))

    expect(await screen.findByText('Generated 2 expense(s).')).toBeInTheDocument()
  })

  it('deletes a recurring expense after confirmation and refetches the list', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    vi.mocked(recurringExpensesApi.listRecurringExpenseTemplates)
      .mockResolvedValueOnce([streaming])
      .mockResolvedValueOnce([])
    vi.mocked(recurringExpensesApi.deleteRecurringExpenseTemplate).mockResolvedValue(streaming)

    render(<RecurringExpensesPage />)

    await screen.findByText('Streaming Subscription')
    fireEvent.click(screen.getByRole('button', { name: 'Delete' }))

    expect(await screen.findByText('No recurring expenses yet.')).toBeInTheDocument()
    expect(recurringExpensesApi.deleteRecurringExpenseTemplate).toHaveBeenCalledWith(1)
  })

  it('renders an error message when the list fails to load', async () => {
    vi.mocked(recurringExpensesApi.listRecurringExpenseTemplates).mockRejectedValue(new Error('Network error'))

    render(<RecurringExpensesPage />)

    expect(await screen.findByText(/Failed to load recurring expenses/i)).toBeInTheDocument()
  })
})
