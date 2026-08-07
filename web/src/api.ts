export type Role = 'patient' | 'dietitian' | 'admin'

export type AuthSession = {
  accessToken: string
  refreshToken: string
  role: Role
  expiresIn: number
}

export type PatientProfile = {
  id: string
  user_id: string
  age: number
  sex: string
  height_cm: number
  weight_kg: number
  activity_level: string
  conditions: Array<{ code: string; stage?: string | null }>
  lab_values: Record<string, number>
  allergies: string[]
  medications: string[]
  region: string | null
}

export type MealPlan = {
  id: string
  patient_id: string
  plan_date: string
  status: 'drafting' | 'pending_review' | 'approved' | 'rejected' | 'failed'
  items: Array<{ id: string; slot: string; food_id: number; grams: number; name_vi: string; source: string; source_ref: string; is_estimated: boolean }>
  targets: Record<string, unknown>
  computed_nutrition: Record<string, unknown>
  violations: Array<{ message_vi?: string; severity?: string }>
  reviewer_notes: string | null
}

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

const baseUrl = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1').replace(/\/$/, '')

function decodeRole(accessToken: string): Role {
  try {
    const payload = JSON.parse(atob(accessToken.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')))
    return payload.role as Role
  } catch {
    throw new ApiError(401, 'Không thể đọc phiên đăng nhập.')
  }
}

export function createApiClient(accessToken?: string) {
  async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const headers = new Headers(init.headers)
    headers.set('Content-Type', 'application/json')
    if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`)
    const response = await fetch(`${baseUrl}${path}`, { ...init, headers })
    if (!response.ok) {
      const body = await response.json().catch(() => null) as { detail?: string } | null
      throw new ApiError(response.status, body?.detail || `Yêu cầu thất bại (${response.status}).`)
    }
    return response.json() as Promise<T>
  }

  return {
    health: () => request<{ status?: string }>('/health'),
    login: async (email: string, password: string): Promise<AuthSession> => {
      const result = await request<{ access_token: string; refresh_token: string; expires_in: number }>('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) })
      return { accessToken: result.access_token, refreshToken: result.refresh_token, expiresIn: result.expires_in, role: decodeRole(result.access_token) }
    },
    listPatients: () => request<{ items: PatientProfile[] }>('/patients'),
    computeTargets: (patientId: string) => request<Record<string, unknown>>('/targets/compute', { method: 'POST', body: JSON.stringify({ patient_id: patientId }) }),
    createMealPlan: (patientId: string) => request<{ plan_id: string; status: string }>('/meal-plans', { method: 'POST', body: JSON.stringify({ patient_id: patientId, plan_date: new Date().toISOString().slice(0, 10) }) }),
    getMealPlan: (planId: string) => request<MealPlan>(`/meal-plans/${planId}`),
    approveMealPlan: (planId: string, notes?: string) => request<MealPlan>(`/reviews/${planId}/approve`, { method: 'POST', body: JSON.stringify({ notes }) }),
    listPendingReviews: () => request<MealPlan[]>('/reviews/pending'),
  }
}

export const apiBaseUrl = baseUrl
