import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { AccountsPage } from './AccountsPage'
import * as accountsApi from '../api/accounts'

vi.mock('../api/accounts')

const checking = { id: 1, name: 'Checking', account_type: 'Bank', balance: 1500 } as const

afterEach(() => {
  vi.restoreAllMocks()
  vi.clearAllMocks()
})

describe('AccountsPage', () => {
  it('renders the account list once loaded', async () => {
    vi.mocked(accountsApi.listAccounts).mockResolvedValue([checking])

    render(<AccountsPage />)

    expect(await screen.findByText('Checking')).toBeInTheDocument()
  })

  it('submits the create form and refetches the list', async () => {
    vi.mocked(accountsApi.listAccounts).mockResolvedValueOnce([]).mockResolvedValueOnce([checking])
    vi.mocked(accountsApi.createAccount).mockResolvedValue(checking)

    render(<AccountsPage />)

    await screen.findByText('No accounts yet.')

    fireEvent.change(screen.getByLabelText('Name'), { target: { value: 'Checking' } })
    fireEvent.change(screen.getByLabelText('Account Type'), { target: { value: 'Bank' } })
    fireEvent.change(screen.getByLabelText('Balance'), { target: { value: '1500' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add Account' }))

    expect(await screen.findByText('Checking')).toBeInTheDocument()
    expect(accountsApi.createAccount).toHaveBeenCalledWith({
      name: 'Checking',
      account_type: 'Bank',
      balance: 1500,
    })
  })

  it('deletes an account after confirmation and refetches the list', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    vi.mocked(accountsApi.listAccounts).mockResolvedValueOnce([checking]).mockResolvedValueOnce([])
    vi.mocked(accountsApi.deleteAccount).mockResolvedValue(checking)

    render(<AccountsPage />)

    await screen.findByText('Checking')
    fireEvent.click(screen.getByRole('button', { name: 'Delete' }))

    expect(await screen.findByText('No accounts yet.')).toBeInTheDocument()
    expect(accountsApi.deleteAccount).toHaveBeenCalledWith(1)
  })

  it('renders an error message when the list fails to load', async () => {
    vi.mocked(accountsApi.listAccounts).mockRejectedValue(new Error('Network error'))

    render(<AccountsPage />)

    expect(await screen.findByText(/Failed to load accounts/i)).toBeInTheDocument()
  })
})
