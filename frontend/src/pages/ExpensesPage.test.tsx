import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ExpensesPage } from './ExpensesPage'
import * as expensesApi from '../api/expenses'

vi.mock('../api/expenses')

const rent = { id: 1, name: 'Rent', category: 'Housing', amount: 1200 } as const
const coffee = { id: 2, name: 'Coffee', category: 'Food', amount: 5 } as const

afterEach(() => {
  vi.restoreAllMocks()
  vi.clearAllMocks()
})

describe('ExpensesPage', () => {
  it('renders the expense list once loaded', async () => {
    vi.mocked(expensesApi.listExpenses).mockResolvedValue([rent, coffee])

    render(<ExpensesPage />)

    expect(await screen.findByText('Rent')).toBeInTheDocument()
    expect(await screen.findByText('Coffee')).toBeInTheDocument()
  })

  it('submits the create form and refetches the list', async () => {
    vi.mocked(expensesApi.listExpenses)
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([rent])
    vi.mocked(expensesApi.createExpense).mockResolvedValue(rent)

    render(<ExpensesPage />)

    await screen.findByText('No expenses yet.')

    fireEvent.change(screen.getByLabelText('Name'), { target: { value: 'Rent' } })
    fireEvent.change(screen.getByLabelText('Amount'), { target: { value: '1200' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add Expense' }))

    expect(await screen.findByText('Rent')).toBeInTheDocument()
    expect(expensesApi.createExpense).toHaveBeenCalledWith({
      name: 'Rent',
      category: 'Food',
      amount: 1200,
    })
    expect(expensesApi.listExpenses).toHaveBeenCalledTimes(2)
  })

  it('deletes an expense after confirmation and refetches the list', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    vi.mocked(expensesApi.listExpenses)
      .mockResolvedValueOnce([rent])
      .mockResolvedValueOnce([])
    vi.mocked(expensesApi.deleteExpense).mockResolvedValue(rent)

    render(<ExpensesPage />)

    await screen.findByText('Rent')
    fireEvent.click(screen.getByRole('button', { name: 'Delete' }))

    expect(await screen.findByText('No expenses yet.')).toBeInTheDocument()
    expect(expensesApi.deleteExpense).toHaveBeenCalledWith(1)
  })

  it('renders an error message when the list fails to load', async () => {
    vi.mocked(expensesApi.listExpenses).mockRejectedValue(new Error('Network error'))

    render(<ExpensesPage />)

    expect(await screen.findByText(/Failed to load expenses/i)).toBeInTheDocument()
  })
})
