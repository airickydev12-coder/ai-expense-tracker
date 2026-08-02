import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { DebtPage } from './DebtPage'
import * as debtApi from '../api/debt'

vi.mock('../api/debt')

const creditCard = {
  id: 1,
  name: 'Credit Card',
  balance: 2500,
  interest_rate: 24.99,
  minimum_payment: 75,
} as const
const creditCardPaidDown = { ...creditCard, balance: 2000 }

afterEach(() => {
  vi.restoreAllMocks()
  vi.clearAllMocks()
})

describe('DebtPage', () => {
  it('renders the debt list once loaded', async () => {
    vi.mocked(debtApi.listDebts).mockResolvedValue([creditCard])

    render(<DebtPage />)

    expect(await screen.findByText('Credit Card')).toBeInTheDocument()
  })

  it('submits the create form and refetches the list', async () => {
    vi.mocked(debtApi.listDebts).mockResolvedValueOnce([]).mockResolvedValueOnce([creditCard])
    vi.mocked(debtApi.createDebt).mockResolvedValue(creditCard)

    render(<DebtPage />)

    await screen.findByText('No debts yet.')

    fireEvent.change(screen.getByLabelText('Name'), { target: { value: 'Credit Card' } })
    fireEvent.change(screen.getByLabelText('Balance'), { target: { value: '2500' } })
    fireEvent.change(screen.getByLabelText('Interest Rate (%)'), { target: { value: '24.99' } })
    fireEvent.change(screen.getByLabelText('Minimum Payment'), { target: { value: '75' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add Debt' }))

    expect(await screen.findByText('Credit Card')).toBeInTheDocument()
    expect(debtApi.createDebt).toHaveBeenCalledWith({
      name: 'Credit Card',
      balance: 2500,
      interest_rate: 24.99,
      minimum_payment: 75,
    })
  })

  it('applies a payment via the prompt action and refetches the list', async () => {
    vi.spyOn(window, 'prompt').mockReturnValue('500')
    vi.mocked(debtApi.listDebts)
      .mockResolvedValueOnce([creditCard])
      .mockResolvedValueOnce([creditCardPaidDown])
    vi.mocked(debtApi.applyDebtPayment).mockResolvedValue(creditCardPaidDown)

    render(<DebtPage />)

    await screen.findByText('Credit Card')
    fireEvent.click(screen.getByRole('button', { name: 'Apply Payment' }))

    expect(await screen.findByText('$2000.00')).toBeInTheDocument()
    expect(debtApi.applyDebtPayment).toHaveBeenCalledWith(1, 500)
  })

  it('deletes a debt after confirmation and refetches the list', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    vi.mocked(debtApi.listDebts).mockResolvedValueOnce([creditCard]).mockResolvedValueOnce([])
    vi.mocked(debtApi.deleteDebt).mockResolvedValue(creditCard)

    render(<DebtPage />)

    await screen.findByText('Credit Card')
    fireEvent.click(screen.getByRole('button', { name: 'Delete' }))

    expect(await screen.findByText('No debts yet.')).toBeInTheDocument()
    expect(debtApi.deleteDebt).toHaveBeenCalledWith(1)
  })

  it('renders an error message when the list fails to load', async () => {
    vi.mocked(debtApi.listDebts).mockRejectedValue(new Error('Network error'))

    render(<DebtPage />)

    expect(await screen.findByText(/Failed to load debts/i)).toBeInTheDocument()
  })
})
