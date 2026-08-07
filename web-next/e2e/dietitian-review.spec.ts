import { test, expect, APIRequestContext } from '@playwright/test'

// Luồng HITL đầy đủ: đăng nhập chuyên gia → xem hàng chờ duyệt → mở 1 thực đơn
// → kiểm tra RULE-2 (chip nguồn từng món) → duyệt → về lại dashboard.
// Setup dùng gọi API trực tiếp (không qua UI generate) để không phụ thuộc
// LLM/CP-SAT timing trong lúc thu thập selector; sinh thực đơn thật (CP-SAT,
// không tốn key LLM khi khả thi) rồi verify bằng UI thật.

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1'
const DIETITIAN = { email: 'dietitian1@nutricare.demo', password: 'Demo1234' }

async function login(request: APIRequestContext) {
  const res = await request.post(`${API_BASE}/auth/login`, { data: DIETITIAN })
  expect(res.ok()).toBeTruthy()
  return (await res.json()).access_token as string
}

async function createPendingPlan(request: APIRequestContext, token: string): Promise<string> {
  const patients = await request.get(`${API_BASE}/patients`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  const { items } = await patients.json()
  const patient = items.find((p: { conditions: Array<{ code: string }> }) =>
    p.conditions.some((c) => c.code === 'T2DM'))
  expect(patient, 'cần ít nhất 1 bệnh nhân T2DM trong dữ liệu demo').toBeTruthy()

  // Backend chặn 2 thực đơn cùng ngày/bệnh nhân — tái dùng bản pending có sẵn
  // (VD do chạy test nhiều lần trong ngày) thay vì luôn tạo mới.
  const existing = await request.get(
    `${API_BASE}/meal-plans?patient_id=${patient.id}&status=pending_review`,
    { headers: { Authorization: `Bearer ${token}` } },
  )
  const existingPlans = (await existing.json()).items
  if (existingPlans.length > 0) return existingPlans[0].id

  const created = await request.post(`${API_BASE}/meal-plans`, {
    headers: { Authorization: `Bearer ${token}` },
    data: { patient_id: patient.id, plan_date: new Date().toISOString().slice(0, 10) },
  })
  expect(created.ok(), await created.text()).toBeTruthy()
  const { plan_id } = await created.json()

  for (let i = 0; i < 15; i++) {
    await new Promise((r) => setTimeout(r, 2000))
    const r = await request.get(`${API_BASE}/meal-plans/${plan_id}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    const plan = await r.json()
    if (plan.status !== 'drafting') return plan_id
  }
  throw new Error('Thực đơn không sinh xong sau 30s — kiểm tra generator/backend log')
}

test.describe('Chuyên gia duyệt thực đơn (HITL)', () => {
  test('xem hàng chờ, mở thực đơn, thấy nguồn từng món, duyệt thành công', async ({ page, request }) => {
    const token = await login(request)
    const planId = await createPendingPlan(request, token)

    await page.goto('/login')
    await page.fill('#email', DIETITIAN.email)
    await page.fill('#password', DIETITIAN.password)
    await page.click('button[type="submit"]')
    await expect(page).toHaveURL(/\/dietitian/, { timeout: 10_000 })

    await page.goto(`/dietitian/reviews/${planId}`)

    // RULE-3: không có vi phạm cứng thì phải cho duyệt; có thì nút bị disable — cả hai đều hợp lệ, chỉ assert bảng nguồn hiển thị.
    const sourceChips = page.locator('.source-chip')
    await expect(sourceChips.first()).toBeVisible({ timeout: 10_000 })
    const chipCount = await sourceChips.count()
    expect(chipCount).toBeGreaterThan(0)

    // RULE-2: bấm vào 1 chip nguồn phải hiện popover có source_ref
    await sourceChips.first().click()
    await expect(page.getByText(/NIN|USDA/).first()).toBeVisible()

    const hardBadge = page.locator('.safety-strip-error')
    const hasHardViolation = await hardBadge.count()

    if (hasHardViolation === 0) {
      await page.getByRole('button', { name: /Duyệt thực đơn/ }).click()
      await page.getByRole('button', { name: /Xác nhận duyệt/ }).click()
      await expect(page.getByText(/Đã duyệt thực đơn/)).toBeVisible({ timeout: 10_000 })
      await expect(page).toHaveURL(/\/dietitian$/, { timeout: 10_000 })
    } else {
      await expect(page.getByRole('button', { name: /Duyệt thực đơn/ })).toBeDisabled()
    }
  })
})
