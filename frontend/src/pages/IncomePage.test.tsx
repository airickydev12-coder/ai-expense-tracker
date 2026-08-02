import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { IncomePage } from './IncomePage'
import * as incomeApi from '../api/income'

vi.mock('../api/income')

const salary = { id: 1, source: 'Salary', amount: 3000 } as const

afterEach(() => {
  vi.restoreAllMocks()
  vi.clearAllMocks()
})

describe('IncomePage', () => {
  it('renders the income list once loaded', async () => {
    vi.mocked(incomeApi.listIncome).mockResolvedValue([salary])

    render(<IncomePage />)

    expect(await screen.findByText('Salary')).toBeInTheDocument()
  })

  it('submits the create form and refetches the list', async () => {
    vi.mocked(incomeApi.listIncome).mockResolvedValueOnce([]).mockResolvedValueOnce([salary])
    vi.mocked(incomeApi.createIncome).mockResolvedValue(salary)

    render(<IncomePage />)

    await screen.findByText('No income entries yet.')

    fireEvent.change(screen.getByLabelText('Source'), { target: { value: 'Salary' } })
    fireEvent.change(screen.getByLabelText('Amount'), { target: { value: '3000' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add Income' }))

    expect(await screen.findByText('Salary')).toBeInTheDocument()
    expect(incomeApi.createIncome).toHaveBeenCalledWith({ source: 'Salary', amount: 3000 })
  })

  it('deletes an income entry after confirmation and refetches the list', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    vi.mocked(incomeApi.listIncome).mockResolvedValueOnce([salary]).mockResolvedValueOnce([])
    vi.mocked(incomeApi.deleteIncome).mockResolvedValue(salary)

    render(<IncomePage />)

    await screen.findByText('Salary')
    fireEvent.click(screen.getByRole('button', { name: 'Delete' }))

    expect(await screen.findByText('No income entries yet.')).toBeInTheDocument()
    expect(incomeApi.deleteIncome).toHaveBeenCalledWith(1)
  })

  it('renders an error message when the list fails to load', async () => {
    vi.mocked(incomeApi.listIncome).mockRejectedValue(new Error('Network error'))

    render(<IncomePage />)

    expect(await screen.findByText(/Failed to load income/i)).toBeInTheDocument()
  })
})
