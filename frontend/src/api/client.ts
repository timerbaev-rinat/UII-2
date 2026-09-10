// HTTP-клиент на базе fetch с Bearer-авторизацией и автообновлением токена.

import type { TokenPair } from '@/types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'

// Ключи localStorage
const ACCESS_KEY = 'asset_access_token'
const REFRESH_KEY = 'asset_refresh_token'

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_KEY)
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY)
}

export function setTokens(tokens: TokenPair): void {
  localStorage.setItem(ACCESS_KEY, tokens.access_token)
  localStorage.setItem(REFRESH_KEY, tokens.refresh_token)
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

interface ApiErrorBody {
  detail?: string
}

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getRefreshToken()
  if (!refreshToken) return null
  try {
    const res = await fetch(`${BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })
    if (!res.ok) return null
    const tokens = (await res.json()) as TokenPair
    setTokens(tokens)
    return tokens.access_token
  } catch {
    return null
  }
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  body?: unknown
  params?: Record<string, string | number | boolean | undefined | null>
}

export async function api<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, params } = options

  let url = `${BASE_URL}${path}`
  if (params) {
    const search = new URLSearchParams()
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null && value !== '') {
        search.set(key, String(value))
      }
    }
    const qs = search.toString()
    if (qs) url += `?${qs}`
  }

  const doRequest = async (token: string | null): Promise<Response> => {
    const headers: Record<string, string> = {}
    if (body !== undefined) headers['Content-Type'] = 'application/json'
    if (token) headers['Authorization'] = `Bearer ${token}`
    return fetch(url, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  }

  let response = await doRequest(getAccessToken())

  // Если 401 — пробуем обновить токен и повторить запрос
  if (response.status === 401) {
    const newToken = await refreshAccessToken()
    if (newToken) {
      response = await doRequest(newToken)
    } else {
      clearTokens()
      throw new ApiError(401, 'Сессия истекла')
    }
  }

  if (!response.ok) {
    let message = `Ошибка запроса (${response.status})`
    try {
      const data = (await response.json()) as ApiErrorBody
      if (data.detail) message = data.detail
    } catch {
      // тело не JSON — оставляем стандартное сообщение
    }
    throw new ApiError(response.status, message)
  }

  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}

// Загрузка файла (multipart/form-data) с авторизацией и автообновлением токена.
export async function apiUpload<T>(path: string, file: File): Promise<T> {
  const url = `${BASE_URL}${path}`
  const formData = new FormData()
  formData.append('file', file)

  const doRequest = async (token: string | null): Promise<Response> => {
    const headers: Record<string, string> = {}
    if (token) headers['Authorization'] = `Bearer ${token}`
    // Content-Type не задаём: браузер сам выставит boundary для multipart.
    return fetch(url, { method: 'POST', headers, body: formData })
  }

  let response = await doRequest(getAccessToken())
  if (response.status === 401) {
    const newToken = await refreshAccessToken()
    if (newToken) {
      response = await doRequest(newToken)
    } else {
      clearTokens()
      throw new ApiError(401, 'Сессия истекла')
    }
  }

  if (!response.ok) {
    let message = `Ошибка загрузки (${response.status})`
    try {
      const data = (await response.json()) as ApiErrorBody
      if (data.detail) message = data.detail
    } catch {
      // тело не JSON
    }
    throw new ApiError(response.status, message)
  }
  return (await response.json()) as T
}

// Получение файла (например, фото) как Blob с Bearer-авторизацией.
export async function getAuthorizedBlob(path: string): Promise<Blob> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { Authorization: `Bearer ${getAccessToken()}` },
  })
  if (!response.ok) {
    throw new ApiError(response.status, `Не удалось получить файл (${response.status})`)
  }
  return response.blob()
}