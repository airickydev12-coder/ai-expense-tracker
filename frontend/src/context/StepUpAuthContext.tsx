import { createContext, useContext, useRef, useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import * as authApi from '../api/auth'
import { ApiError, setAuthToken } from '../api/client'

interface StepUpAuthContextValue {
  /**
   * Runs `action`; if it fails with a 403 step_up_required response, opens
   * a password-confirmation modal, reauthenticates, and retries `action`
   * once -- resolving/rejecting with that retry's own result. Any other
   * failure (including a cancelled or failed reauth) propagates as-is.
   */
  runWithStepUp: <T>(action: () => Promise<T>) => Promise<T>
}

interface PendingRequest {
  retry: () => Promise<unknown>
  resolve: (value: unknown) => void
  reject: (reason: unknown) => void
}

const StepUpAuthContext = createContext<StepUpAuthContextValue | null>(null)

function isStepUpRequired(error: unknown): boolean {
  return error instanceof ApiError && error.status === 403 && error.code === 'step_up_required'
}

export function StepUpAuthProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false)
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const pendingRef = useRef<PendingRequest | null>(null)

  function runWithStepUp<T>(action: () => Promise<T>): Promise<T> {
    return Promise.resolve()
      .then(action)
      .catch((err: unknown) => {
        if (!isStepUpRequired(err)) throw err

        return new Promise<T>((resolve, reject) => {
          pendingRef.current = {
            retry: action as unknown as () => Promise<unknown>,
            resolve: resolve as unknown as (value: unknown) => void,
            reject,
          }
          setError(null)
          setPassword('')
          setOpen(true)
        })
      })
  }

  function closeModal() {
    const pending = pendingRef.current
    pendingRef.current = null
    setOpen(false)
    setPassword('')
    setError(null)
    setSubmitting(false)
    pending?.reject(new Error('Re-authentication cancelled.'))
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const pending = pendingRef.current
    if (!pending) return

    setSubmitting(true)
    setError(null)
    authApi
      .reauth({ password })
      .then((token) => {
        setAuthToken(token.access_token)
        pendingRef.current = null
        setOpen(false)
        setPassword('')
        pending.retry().then(pending.resolve).catch(pending.reject)
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to re-authenticate')
      })
      .finally(() => setSubmitting(false))
  }

  return (
    <StepUpAuthContext.Provider value={{ runWithStepUp }}>
      {children}
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
          <div className="w-full max-w-sm rounded bg-white p-4 shadow-lg">
            <h2 className="text-lg font-medium text-gray-900">Confirm your password</h2>
            <p className="mt-1 text-sm text-gray-600">
              This action requires you to re-enter your password.
            </p>
            <form onSubmit={handleSubmit} className="mt-3 space-y-3">
              {error && <p className="text-sm text-red-600">{error}</p>}
              <div className="flex flex-col gap-1">
                <label htmlFor="step-up-password" className="text-xs text-gray-500">
                  Password
                </label>
                <input
                  id="step-up-password"
                  type="password"
                  autoFocus
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="rounded border border-gray-300 px-2 py-1 text-sm"
                />
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={closeModal}
                  className="rounded px-3 py-1.5 text-sm font-medium text-gray-600 hover:underline"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting || !password}
                  className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
                >
                  {submitting ? 'Confirming...' : 'Confirm'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </StepUpAuthContext.Provider>
  )
}

export function useStepUpAuth(): StepUpAuthContextValue {
  const context = useContext(StepUpAuthContext)
  if (!context) {
    throw new Error('useStepUpAuth must be used within a StepUpAuthProvider')
  }
  return context
}
