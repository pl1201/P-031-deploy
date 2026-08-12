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

export interface PatientObservation {
  id: string
  profile_id: string
  observation_type: string
  value: number
  unit: string
  measured_at: string
  source: string
  recorded_by: string
  note: string | null
  created_at: string
}

export interface ClinicalNote {
  id: string
  profile_id: string
  author_id: string
  note_type: string
  content: string
  visibility: string
  version: number
  created_at: string
  updated_at: string
}

export interface ReviewEvent {
  id: string
  meal_plan_id: string
  profile_id: string
  reviewer_id: string
  decision: string
  reason: string | null
  notes: string | null
  menu_version: number
  menu_hash: string | null
  nutrition_hash: string | null
  created_at: string
}

export interface MealPlanItem {
  id: string
  slot: 'breakfast' | 'lunch' | 'dinner' | 'snack'
  dish_id?: string | null
  food_id?: number | null
  grams: number
  name_vi: string
  source: string
  source_ref: string
  is_estimated: boolean
  ingredients: MealPlanIngredient[]
}

export interface MealPlanIngredient {
  food_id: number
  name_vi: string
  grams: number
  source: string
  source_ref: string
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
  // actual/limit/unit là NULL với cảnh báo ĐỊNH TÍNH (món chưa tra được, tương
  // tác thuốc–thực phẩm). UI phải render "—", tuyệt đối không thay bằng 0:
  // hiển thị "0 mg" cho thứ chưa đo được chính là bịa số (RULE-2).
  actual: number | null
  limit: number | null
  unit: string | null
  kind: string
  severity: 'hard' | 'soft'
  message_vi: string
  suggestion?: string | null
  rule_id?: string | null
  source_ref?: string | null
  evidence?: string | null
  food_log_id?: string | null
}

// --- Nhật ký ăn uống (BE-07) ---------------------------------------------

export type MatchStatus = 'unmatched' | 'auto' | 'llm' | 'expert' | 'no_data'

export interface MatchSuggestion {
  food_id: number
  name_vi: string
  score: number
  matched_on: string
}

export interface FoodLog {
  id: string
  profile_id: string
  logged_at: string
  free_text_vi: string | null
  food_id: number | null
  food_name_vi: string | null
  grams: number | null
  slot: string | null
  match_status: MatchStatus
  match_confidence: number | null
  note_vi: string | null
  suggestions: MatchSuggestion[]
}

/** `insufficient_data` = KHÔNG kết luận được, khác hẳn "đạt". */
export type Verdict = 'exceeded' | 'below_min' | 'within' | 'insufficient_data'

export interface NutrientVerdict {
  nutrient: string
  label_vi: string
  verdict: Verdict
  counted: number | null
  min_value: number | null
  max_value: number | null
  unit: string | null
}

export interface DaySummary {
  profile_id: string
  day: string
  matched_count: number
  unmatched_count: number
  /** <1 nghĩa là còn món chưa tra được ⇒ mọi con số là MỨC TỐI THIỂU. */
  coverage: number
  is_complete: boolean
  verdicts: NutrientVerdict[]
  violations: Violation[]
}

export interface SafetyFinding {
  code: string
  risk_level: 'P0' | 'P1' | 'P2'
  category: string
  message_vi: string
  suggestion?: string | null
  rule_id?: string | null
  evidence_refs: string[]
  reviewer_override_allowed: boolean
}

export interface ReviewPacket {
  highest_risk: 'P0' | 'P1' | 'P2' | 'none'
  can_approve: boolean
  used_fallback: boolean
  target_gate_reasons: string[]
  findings: SafetyFinding[]
  summary: string
}

export interface MealPlan {
  id: string
  patient_id: string
  plan_date: string
  status: 'drafting' | 'pending_review' | 'manual_review_required' | 'approved' | 'rejected' | 'failed'
  items: MealPlanItem[]
  targets: ClinicalTargets
  computed_nutrition: ComputedNutrition | null
  violations: Violation[]
  safety_findings: SafetyFinding[]
  review_packet: ReviewPacket
  citations: Array<{ source_ref: string; title?: string | null; rule_ids: string[] }>
  explanation_vi: string | null
  highest_risk: 'P0' | 'P1' | 'P2' | 'none'
  menu_version: number
  menu_hash_ready: boolean
  nutrition_hash_ready: boolean
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

export interface ReplacementCandidate {
  dish_id: string
  name_vi: string
  serving_g: number
  region: string | null
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

    const controller = new AbortController()
    const timeout = window.setTimeout(() => controller.abort(), 20000)
    let res: Response
    try { res = await fetch(`${BASE_URL}${path}`, { ...init, headers, signal: init.signal ?? controller.signal }) }
    catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') {
        throw new ApiError(408, 'Máy chủ phản hồi quá chậm. Vui lòng thử lại hoặc kiểm tra kết nối cơ sở dữ liệu.')
      }
      throw new ApiError(0, 'Không kết nối được máy chủ. Hãy kiểm tra Docker/backend rồi thử lại.')
    } finally {
      window.clearTimeout(timeout)
    }

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
    /** Hồ sơ của chính người đang đăng nhập — session chỉ có user_id, API cần profile_id. */
    getMyProfile: () => request<PatientProfile>('/patients/me'),
    createPatient: (data: Omit<PatientProfile, 'id'>) =>
      request<PatientProfile>('/patients', { method: 'POST', body: JSON.stringify(data) }),
    updatePatient: (id: string, data: Partial<PatientProfile>) =>
      request<PatientProfile>(`/patients/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    listObservations: (profileId: string) =>
      request<PatientObservation[]>(`/patients/${profileId}/observations`),
    listClinicalNotes: (profileId: string) =>
      request<ClinicalNote[]>(`/patients/${profileId}/notes`),
    createClinicalNote: (
      profileId: string,
      data: { note_type: string; content: string; visibility: string },
    ) => request<ClinicalNote>(`/patients/${profileId}/notes`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    listPatientReviewEvents: (profileId: string) =>
      request<ReviewEvent[]>(`/patients/${profileId}/review-events`),

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
    recomputeMealPlan: (planId: string, edits: Array<{ item_id: string; grams: number }>) =>
      request<MealPlan>(`/reviews/${planId}/recompute`, {
        method: 'POST',
        body: JSON.stringify({ edits }),
      }),
    listReplacementCandidates: (planId: string, itemId: string) =>
      request<ReplacementCandidate[]>(`/reviews/${planId}/items/${itemId}/replacement-candidates`),
    replaceMealPlanItem: (planId: string, itemId: string, dishId: string, servingG?: number) =>
      request<MealPlan>(`/reviews/${planId}/items/${itemId}/replace`, {
        method: 'POST',
        body: JSON.stringify({ dish_id: dishId, serving_g: servingG ?? null }),
      }),
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

    // Nhật ký ăn uống (BE-07)
    createFoodLog: (data: {
      profile_id: string
      free_text_vi: string
      grams?: number | null
      slot?: string
      note_vi?: string | null
    }) => request<FoodLog>('/food-logs', { method: 'POST', body: JSON.stringify(data) }),

    listFoodLogs: (profileId: string, day?: string) =>
      request<FoodLog[]>(`/food-logs?profile_id=${profileId}${day ? `&day=${day}` : ''}`),

    getDaySummary: (profileId: string, day?: string) =>
      request<DaySummary>(`/food-logs/summary?profile_id=${profileId}${day ? `&day=${day}` : ''}`),

    listUnresolvedLogs: () => request<FoodLog[]>('/food-logs/unresolved'),

    resolveFoodLog: (
      logId: string,
      body: { action: 'map_to_existing' | 'mark_no_data'; food_id?: number; grams?: number; note_vi?: string }
    ) => request<FoodLog>(`/food-logs/${logId}/resolve`, { method: 'POST', body: JSON.stringify(body) }),
  }
}
