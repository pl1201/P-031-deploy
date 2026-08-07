import { test, expect } from '@playwright/test'

// Tài khoản demo seed qua scripts/seed_demo_users.py (mật khẩu chung Demo1234).
// Backend đọc key từ .env (GEMINI_API_KEY*, JWT_SECRET…) — test này không cần
// gọi LLM nên không phụ thuộc tên biến Gemini/OpenAI cụ thể.
const DIETITIAN = { email: 'dietitian1@nutricare.demo', password: 'Demo1234' }
const PATIENT = { email: 'patient1@nutricare.demo', password: 'Demo1234' }

test.describe('Đăng nhập', () => {
  test('sai mật khẩu hiển thị lỗi, không điều hướng', async ({ page }) => {
    await page.goto('/login')
    await page.fill('#email', DIETITIAN.email)
    await page.fill('#password', 'sai-mat-khau')
    await page.click('button[type="submit"]')

    await expect(page.getByText(/không thể đăng nhập|không đúng|lỗi/i)).toBeVisible({ timeout: 10_000 })
    await expect(page).toHaveURL(/\/login/)
  })

  test('chuyên gia đăng nhập đúng → vào /dietitian', async ({ page }) => {
    await page.goto('/login')
    await page.fill('#email', DIETITIAN.email)
    await page.fill('#password', DIETITIAN.password)
    await page.click('button[type="submit"]')

    await expect(page).toHaveURL(/\/dietitian/, { timeout: 10_000 })
    await expect(page.getByRole('heading', { name: 'Hàng chờ duyệt' })).toBeVisible()
  })

  test('bệnh nhân đăng nhập đúng → vào /patient', async ({ page }) => {
    await page.goto('/login')
    await page.fill('#email', PATIENT.email)
    await page.fill('#password', PATIENT.password)
    await page.click('button[type="submit"]')

    await expect(page).toHaveURL(/\/patient/, { timeout: 10_000 })
    await expect(page.getByRole('heading', { name: 'Thực đơn của tôi' })).toBeVisible()
  })

  test('click tài khoản demo tự điền form', async ({ page }) => {
    await page.goto('/login')
    await page.getByText(DIETITIAN.email, { exact: false }).click()

    await expect(page.locator('#email')).toHaveValue(DIETITIAN.email)
    await expect(page.locator('#password')).toHaveValue(DIETITIAN.password)
  })
})
