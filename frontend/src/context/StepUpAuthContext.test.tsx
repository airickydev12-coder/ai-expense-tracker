import { act, fireEvent, renderHook, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { StepUpAuthProvider, useStepUpAuth } from './StepUpAuthContext'
import * as authApi from '../api/auth'
import { ApiError, setAuthToken } from '../api/client'

vi.mock('../api/auth')

vi.mock('../api/client', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../api/client')>()
  return { ...actual, setAuthToken: vi.fn() }
})

function stepUpError() {
  return new ApiError(403, 'Recent authentication required for this action.', 'step_up_required')
}

afterEach(() => {
  vi.restoreAllMocks()
  vi.clearAllMocks()
})

describe('StepUpAuthProvider', () => {
  it('passes through a successful action without opening the modal', async () => {
    const { result } = renderHook(() => useStepUpAuth(), { wrapper: StepUpAuthProvider })

    const value = await result.current.runWithStepUp(() => Promise.resolve('ok'))

    expect(value).toBe('ok')
    expect(screen.queryByText('Confirm your password')).not.toBeInTheDocument()
  })

  it('propagates a non-step-up error without opening the modal', async () => {
    const { result } = renderHook(() => useStepUpAuth(), { wrapper: StepUpAuthProvider })

    await expect(
      result.current.runWithStepUp(() => Promise.reject(new Error('boom'))),
    ).rejects.toThrow('boom')
    expect(screen.queryByText('Confirm your password')).not.toBeInTheDocument()
  })

  it('opens the modal, reauthenticates, and retries the action on success', async () => {
    vi.mocked(authApi.reauth).mockResolvedValue({ access_token: 'fresh-token', token_type: 'bearer' })
    const action = vi
      .fn()
      .mockRejectedValueOnce(stepUpError())
      .mockResolvedValueOnce('retried-ok')

    const { result } = renderHook(() => useStepUpAuth(), { wrapper: StepUpAuthProvider })

    let outcome!: Promise<unknown>
    act(() => {
      outcome = result.current.runWithStepUp(action)
    })

    expect(await screen.findByText('Confirm your password')).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'correct-password' } })
    fireEvent.click(screen.getByRole('button', { name: 'Confirm' }))

    await waitFor(() => expect(screen.queryByText('Confirm your password')).not.toBeInTheDocument())
    await expect(outcome).resolves.toBe('retried-ok')
    expect(action).toHaveBeenCalledTimes(2)
    expect(authApi.reauth).toHaveBeenCalledWith({ password: 'correct-password' })
    expect(setAuthToken).toHaveBeenCalledWith('fresh-token')
  })

  it('shows an inline error and keeps the modal open on a wrong password', async () => {
    vi.mocked(authApi.reauth).mockRejectedValue(new Error('Current password is incorrect.'))
    const action = vi.fn().mockRejectedValueOnce(stepUpError())

    const { result } = renderHook(() => useStepUpAuth(), { wrapper: StepUpAuthProvider })

    act(() => {
      result.current.runWithStepUp(action).catch(() => {})
    })

    expect(await screen.findByText('Confirm your password')).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'wrong-password' } })
    fireEvent.click(screen.getByRole('button', { name: 'Confirm' }))

    expect(await screen.findByText('Current password is incorrect.')).toBeInTheDocument()
    expect(screen.getByText('Confirm your password')).toBeInTheDocument()
    expect(action).toHaveBeenCalledTimes(1)
  })

  it('rejects the original call when the modal is cancelled', async () => {
    const action = vi.fn().mockRejectedValueOnce(stepUpError())

    const { result } = renderHook(() => useStepUpAuth(), { wrapper: StepUpAuthProvider })

    let outcome!: Promise<unknown>
    act(() => {
      outcome = result.current.runWithStepUp(action)
    })

    expect(await screen.findByText('Confirm your password')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))

    await expect(outcome).rejects.toThrow('Re-authentication cancelled.')
    expect(screen.queryByText('Confirm your password')).not.toBeInTheDocument()
  })
})
