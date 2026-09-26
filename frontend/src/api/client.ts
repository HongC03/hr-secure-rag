import { API_PATHS, ROUTES, TEXT } from '../constants.ts'

const REDIRECT_ERROR_KEY = 'peoplevault.redirectError'

export function takeRedirectError(): string {
  const message = window.sessionStorage.getItem(REDIRECT_ERROR_KEY) ?? ''
  window.sessionStorage.removeItem(REDIRECT_ERROR_KEY)
  return message
}

export class ApiRequestError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message)
  }
}

export function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : TEXT.errors.invalidResponse
}

export async function api<T = unknown>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  let response
  try {
    response = await fetch(path, {
      ...options,
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', ...options.headers },
    })
  } catch {
    throw new Error(TEXT.errors.connection)
  }

  const data: unknown = await response.json().catch(() => null)
  if (!response.ok) {
    const errorText =
      data && typeof data === 'object' && 'error' in data
        ? data.error
        : undefined
    const message =
      typeof errorText === 'string' && errorText.trim()
        ? errorText
        : TEXT.errors.requestFailed(response.status)
    if (
      response.status === 401 &&
      path !== API_PATHS.login &&
      path !== API_PATHS.register
    ) {
      window.sessionStorage.setItem(REDIRECT_ERROR_KEY, message)
      window.location.replace(ROUTES.login)
    }
    throw new ApiRequestError(message, response.status)
  }
  if (!data) throw new Error(TEXT.errors.invalidResponse)
  return data as T
}
