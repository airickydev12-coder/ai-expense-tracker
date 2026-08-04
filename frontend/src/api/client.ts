export const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

let authToken: string | null = null
let unauthorizedHandler: (() => void) | null = null

export function setAuthToken(token: string | null): void {
  authToken = token
}

export function setUnauthorizedHandler(handler: (() => void) | null): void {
  unauthorizedHandler = handler
}

function authHeaders(init?: RequestInit): HeadersInit | undefined {
  if (!authToken) return init?.headers
  return { ...init?.headers, Authorization: `Bearer ${authToken}` }
}

async function fetchOrThrow(path: string, init?: RequestInit): Promise<Response> {
  const res = await fetch(`${BASE_URL}${path}`, { ...init, headers: authHeaders(init) })
  if (!res.ok) {
    let message = `Request to ${path} failed with status ${res.status}`
    try {
      const body = (await res.json()) as { detail?: string }
      if (typeof body?.detail === 'string') message = body.detail
    } catch {
      // response wasn't JSON — keep the generic message
    }
    if (res.status === 401) unauthorizedHandler?.()
    throw new ApiError(res.status, message)
  }
  return res
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetchOrThrow(path, init)
  if (res.status === 204) {
    return undefined as T
  }
  return res.json() as Promise<T>
}

async function requestBlob(path: string, init?: RequestInit): Promise<Blob> {
  const res = await fetchOrThrow(path, init)
  return res.blob()
}

export function apiGet<T>(path: string): Promise<T> {
  return request<T>(path)
}

export function apiGetBlob(path: string): Promise<Blob> {
  return requestBlob(path)
}

export function apiPost<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

export function apiPut<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

export function apiDelete<T>(path: string): Promise<T> {
  return request<T>(path, { method: 'DELETE' })
}

export function apiPatch<T>(path: string): Promise<T> {
  return request<T>(path, { method: 'PATCH' })
}
