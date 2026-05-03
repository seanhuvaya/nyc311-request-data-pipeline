import type { DailyMetric, WeeklySummary } from "@/types"

/**
 * Base URL of the backend API.
 *
 * Provided at build time via Vite's `VITE_API_URL` env var (see frontend/.env.example).
 * Falls back to localhost so `npm run dev` works against a locally-running backend
 * without any extra config.
 */
export const API_BASE: string =
  import.meta.env.VITE_API_URL?.replace(/\/+$/, "") ?? "http://localhost:8000"

class ApiError extends Error {
  readonly status: number
  readonly url: string

  constructor(status: number, url: string, message: string) {
    super(message)
    this.name = "ApiError"
    this.status = status
    this.url = url
  }
}

async function getJson<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`
  const res = await fetch(url, {
    ...init,
    headers: { Accept: "application/json", ...(init?.headers ?? {}) },
  })
  if (!res.ok) {
    throw new ApiError(res.status, url, `${res.status} ${res.statusText}`)
  }
  return res.json() as Promise<T>
}

export function getDailySummary(): Promise<DailyMetric[]> {
  return getJson<DailyMetric[]>("/api/v1/overview/30-day-summary")
}

export function getWeeklySummary(): Promise<WeeklySummary> {
  return getJson<WeeklySummary>("/api/v1/overview/weekly-summary")
}

export { ApiError }
