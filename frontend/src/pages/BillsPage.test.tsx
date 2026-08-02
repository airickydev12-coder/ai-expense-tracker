import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { BillsPage } from './BillsPage'
import * as billsApi from '../api/bills'

vi.mock('../api/bills')

const electric = {
  id: 1,
  name: 'Electric',
  amount: 125,
  due_day: 15,
  is_paid: false,
} as const
const electricPaid = { ...electric, is_paid: true }

afterEach(() => {
  vi.restoreAllMocks()
  vi.clearAllMocks()
})

describe('BillsPage', () => {
  it('renders the bill list once loaded', async () => {
    vi.mocked(billsApi.listBills).mockResolvedValue([electric])

    render(<BillsPage />)

    expect(await screen.findByText('Electric')).toBeInTheDocument()
    expect(screen.getByText('Unpaid')).toBeInTheDocument()
  })

  it('submits the create form and refetches the list', async () => {
    vi.mocked(billsApi.listBills).mockResolvedValueOnce([]).mockResolvedValueOnce([electric])
    vi.mocked(billsApi.createBill).mockResolvedValue(electric)

    render(<BillsPage />)

    await screen.findByText('No bills yet.')

    fireEvent.change(screen.getByLabelText('Name'), { target: { value: 'Electric' } })
    fireEvent.change(screen.getByLabelText('Amount'), { target: { value: '125' } })
    fireEvent.change(screen.getByLabelText('Due Day (1-31)'), { target: { value: '15' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add Bill' }))

    expect(await screen.findByText('Electric')).toBeInTheDocument()
    expect(billsApi.createBill).toHaveBeenCalledWith({
      name: 'Electric',
      amount: 125,
      due_day: 15,
      is_paid: false,
    })
  })

  it('marks a bill paid via the toggle action and refetches the list', async () => {
    vi.mocked(billsApi.listBills)
      .mockResolvedValueOnce([electric])
      .mockResolvedValueOnce([electricPaid])
    vi.mocked(billsApi.payBill).mockResolvedValue(electricPaid)

    render(<BillsPage />)

    await screen.findByText('Unpaid')
    fireEvent.click(screen.getByRole('button', { name: 'Mark Paid' }))

    expect(await screen.findByText('Paid')).toBeInTheDocument()
    expect(billsApi.payBill).toHaveBeenCalledWith(1)
  })

  it('deletes a bill after confirmation and refetches the list', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    vi.mocked(billsApi.listBills).mockResolvedValueOnce([electric]).mockResolvedValueOnce([])
    vi.mocked(billsApi.deleteBill).mockResolvedValue(electric)

    render(<BillsPage />)

    await screen.findByText('Electric')
    fireEvent.click(screen.getByRole('button', { name: 'Delete' }))

    expect(await screen.findByText('No bills yet.')).toBeInTheDocument()
    expect(billsApi.deleteBill).toHaveBeenCalledWith(1)
  })

  it('renders an error message when the list fails to load', async () => {
    vi.mocked(billsApi.listBills).mockRejectedValue(new Error('Network error'))

    render(<BillsPage />)

    expect(await screen.findByText(/Failed to load bills/i)).toBeInTheDocument()
  })
})
