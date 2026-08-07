// API Client — NutriCare Agent
// Gọi tất cả endpoint backend FastAPI

export type Role = 'patient' | 'dietitian' | 'admin'

export interface AuthSession {
  accessToken: string
  refreshToken: string
  role: Role
  userId: string
  expiresAt: number // epoch ms
}

export interface Condition {
  code: string
  stage?: string | null
}

export interface PatientProfile {
  id: string
  user_id: string
  age: number
  sex: 'male' | 'female'
  height_cm: number
  weight_kg: number
  activity_level: 'light' | 'moderate' | 'heavy' | 'very_heavy'
  conditions: Condition[]
  lab_values: Record<string, number>
  allergies: string[]
  medications: string[]
  region: 'north' | 'central' | 'south' | null
}

export interface MealPlanItem {
  id: string
  slot: 'breakfast' | 'lunch' | 'dinner' | 'snack'
  food_id: number
  grams: number
  name_vi: string
  source: string
  source_ref: string
  is_estimated: boolean
}

export interface NutrientTarget {
  nutrient: string
  min_value: number | null
  max_value: number | null
  unit: string
  rule_ids: string[]
  guideline_refs: string[]
}

export interface ComputedNutrition {
  kcal: number
  protein_g: number
  carb_g: number
  fat_g: number
  fiber_g: number
  na_mg: number
  k_mg: number
  p_mg: number
  purine_mg: number
  sugar_g: number
  sugar_is_complete: boolean
  purine_is_complete: boolean
  has_estimated: boolean
  sources: Array<{ food_id: number; name: string; grams: number; source: string; source_ref: string; is_estimated: boolean }>
}

export interface Violation {
  nutrient: string
  actual: number
  limit: number
  unit: string
  kind: string
  severity: 'hard' | 'soft'
  message_vi: string
  suggestion?: string
  rule_id?: string
}

export interface MealPlan {
  id: string
  patient_id: string
  plan_date: string
  status: 'drafting' | 'pending_review' | 'approved' | 'rejected' | 'failed'
  items: MealPlanItem[]
  targets: Record<string, NutrientTarget>
  computed_nutrition: ComputedNutrition | null
  violations: Violation[]
  retry_count: number
  reviewer_id: string | null
  reviewer_notes: string | null
  created_at: string
}

export interface ClinicalTargets {
  patient_id: string
  bmr_kcal: number
  tdee_kcal: number
  targets: Record<string, NutrientTarget>
  applied_rule_ids: string[]
  needs_expert_review: boolean
  conflict_notes: string[]
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

const BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1').replace(/\/$/, '')

function decodeJwt(token: string): { sub: string; role: Role; exp: number } {
  try {
    const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')))
    return payload
  } catch {
    throw new ApiError(401, 'Token không hợp lệ')
  }
}

export function createApiClient(accessToken?: string) {
  async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const headers = new Headers(init.headers)
    headers.set('Content-Type', 'application/json')
    if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`)

    const res = await fetch(`${BASE_URL}${path}`, { ...init, headers })

    if (!res.ok) {
      const body = await res.json().catch(() => null) as { detail?: string } | null
      throw new ApiError(res.status, body?.detail || `Lỗi ${res.status}`)
    }
    return res.json() as Promise<T>
  }

  return {
    // Auth
    login: async (email: string, password: string): Promise<AuthSession> => {
      const r = await request<{ access_token: string; refresh_token: string; expires_in: number }>(
        '/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }
      )
      const claims = decodeJwt(r.access_token)
      return {
        accessToken: r.access_token,
        refreshToken: r.refresh_token,
        role: claims.role,
        userId: claims.sub,
        expiresAt: Date.now() + r.expires_in * 1000,
      }
    },

    // Health
    health: () => request<{ status: string }>('/health'),

    // Patients
    listPatients: (page = 1, pageSize = 20) =>
      request<{ items: PatientProfile[]; total: number; page: number; page_size: number }>(
        `/patients?page=${page}&page_size=${pageSize}`
      ),
    getPatient: (id: string) => request<PatientProfile>(`/patients/${id}`),
    createPatient: (data: Omit<PatientProfile, 'id'>) =>
      request<PatientProfile>('/patients', { method: 'POST', body: JSON.stringify(data) }),
    updatePatient: (id: string, data: Partial<PatientProfile>) =>
      request<PatientProfile>(`/patients/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

    // Targets
    computeTargets: (patientId: string) =>
      request<ClinicalTargets>('/targets/compute', { method: 'POST', body: JSON.stringify({ patient_id: patientId }) }),

    // Meal Plans
    createMealPlan: (patientId: string, planDate?: string) =>
      request<{ plan_id: string; status: string }>('/meal-plans', {
        method: 'POST',
        body: JSON.stringify({ patient_id: patientId, plan_date: planDate || new Date().toISOString().slice(0, 10) }),
      }),
    getMealPlan: (planId: string) => request<MealPlan>(`/meal-plans/${planId}`),
    listMealPlans: (patientId?: string, status?: string, page = 1) =>
      request<{ items: MealPlan[]; total: number; page: number; page_size: number }>(
        `/meal-plans?${patientId ? `patient_id=${patientId}&` : ''}${status ? `status=${status}&` : ''}page=${page}`
      ),

    // Reviews (HITL)
    listPendingReviews: () => request<MealPlan[]>('/reviews/pending'),
    approveMealPlan: (planId: string, edits?: Array<{ item_id: string; grams: number }>, notes?: string) =>
      request<MealPlan>(`/reviews/${planId}/approve`, {
        method: 'POST',
        body: JSON.stringify({ edits: edits ?? null, notes: notes ?? null }),
      }),
    rejectMealPlan: (planId: string, reason: string) =>
      request<MealPlan>(`/reviews/${planId}/reject`, {
        method: 'POST',
        body: JSON.stringify({ reason }),
      }),
  }
}
