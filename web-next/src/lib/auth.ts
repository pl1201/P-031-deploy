'use client'
// Auth utilities — lưu session vào sessionStorage (không localStorage cho bảo mật)
import type { AuthSession, Role } from './api'

const SESSION_KEY = 'nutricare_session'

export function saveSession(session: AuthSession): void {
  sessionStorage.setItem(SESSION_KEY, JSON.stringify(session))
}

export function getSession(): AuthSession | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = sessionStorage.getItem(SESSION_KEY)
    if (!raw) return null
    const session: AuthSession = JSON.parse(raw)
    // Kiểm tra token còn hạn (buffer 30s)
    if (Date.now() >= session.expiresAt - 30_000) {
      clearSession()
      return null
    }
    return session
  } catch {
    return null
  }
}

export function clearSession(): void {
  sessionStorage.removeItem(SESSION_KEY)
}

export function getRole(): Role | null {
  return getSession()?.role ?? null
}

export function getToken(): string | null {
  return getSession()?.accessToken ?? null
}

export function redirectByRole(role: Role): string {
  switch (role) {
    case 'dietitian': return '/dietitian'
    case 'patient': return '/patient'
    case 'admin': return '/dietitian' // admin dùng view dietitian
    default: return '/login'
  }
}
