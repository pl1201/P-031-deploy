'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { Icon } from '@/components/brand-artwork'
import { ApiError, createApiClient } from '@/lib/api'
import { getToken } from '@/lib/auth'

const CARD = 'mx-auto max-w-[520px] rounded-2xl border border-[#d8e1e3] bg-white p-[26px] shadow-[0_9px_28px_rgba(27,83,81,.045)]'

type Step = 'welcome' | 'preferences'

export default function OnboardingPage() {
  const router = useRouter()
  const [step, setStep] = useState<Step>('welcome')
  const [agreed, setAgreed] = useState(false)
  const [dislikedFoods, setDislikedFoods] = useState('')
  const [remindersEnabled, setRemindersEnabled] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const goToPreferences = async () => {
    const token = getToken()
    if (!token || !agreed) return
    setSaving(true)
    setError('')
    try {
      await createApiClient(token).acceptTerms()
      setStep('preferences')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể lưu — thử lại.')
    } finally {
      setSaving(false)
    }
  }

  const finish = async () => {
    const token = getToken()
    if (!token) return
    setSaving(true)
    setError('')
    try {
      const api = createApiClient(token)
      await api.updateMyPreferences({
        disliked_foods: dislikedFoods.split(',').map(s => s.trim()).filter(Boolean),
        usual_meal_times: {},
        meal_reminders_enabled: remindersEnabled,
      })
      await api.completeOnboarding()
      router.replace('/patient')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể lưu — thử lại.')
    } finally {
      setSaving(false)
    }
  }

  return <div className="min-h-screen px-[15px] py-[40px]">
    <div className={CARD}>
      <small className="text-xs font-bold tracking-[.08em] text-[var(--c-green2)]">CHÀO MỪNG ĐẾN VNUTRICARE</small>
      <h1 className="mt-[6px] font-[family-name:var(--f-serif)] text-[28px] leading-[1.2] font-semibold">{step === 'welcome' ? 'Trước khi bắt đầu' : 'Vài điều bạn muốn chúng tôi biết'}</h1>

      {error && <div className="mt-3.5 flex gap-2 rounded-[11px] border border-[#efb4a4] bg-[#fff5f1] p-3 text-sm text-[#8b3d2b]" role="alert"><Icon name="warning" className="w-[18px]" />{error}</div>}

      {step === 'welcome' ? <>
        <p className="mt-3.5 text-base leading-[1.6] text-[var(--c-muted)]">VNutriCare hỗ trợ chuyên gia dinh dưỡng lập thực đơn cho bạn — hệ thống KHÔNG chẩn đoán bệnh, KHÔNG kê đơn hay thay thế bác sĩ. Mọi thực đơn đều do chuyên gia xem xét và duyệt trước khi tới bạn.</p>
        <label className="mt-4 flex items-start gap-2.5 text-sm leading-[1.5]">
          <input type="checkbox" className="mt-0.5 h-4 w-4" checked={agreed} onChange={e => setAgreed(e.target.checked)} />
          <span>Tôi đã đọc và đồng ý <Link href="/terms" target="_blank" className="font-semibold text-[var(--c-green2)] underline">Điều khoản sử dụng</Link>.</span>
        </label>
        <button type="button" disabled={!agreed || saving} onClick={goToPreferences} className="mt-4 flex h-11 w-full items-center justify-center gap-2 rounded-xl bg-[var(--c-green)] text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50">
          {saving ? <span className="spinner" /> : null}Tiếp tục
        </button>
      </> : <>
        <p className="mt-3.5 text-base leading-[1.6] text-[var(--c-muted)]">Thông tin này giúp cá nhân hoá trải nghiệm — KHÔNG dùng để tính toán dinh dưỡng (hồ sơ lâm sàng của bạn vẫn do chuyên gia quản lý riêng).</p>
        <label className="mt-4 grid gap-1.5 text-sm font-semibold">Món bạn không thích ăn (cách nhau bằng dấu phẩy)
          <input type="text" value={dislikedFoods} onChange={e => setDislikedFoods(e.target.value)} placeholder="Ví dụ: mắm tôm, lòng heo" className="h-11 rounded-[9px] border border-[#cad5d8] bg-white px-3 text-base" />
        </label>
        <label className="mt-3.5 flex items-center gap-2.5 text-sm font-semibold">
          <input type="checkbox" className="h-4 w-4" checked={remindersEnabled} onChange={e => setRemindersEnabled(e.target.checked)} />
          Nhắc tôi khi tới giờ bữa ăn theo thực đơn
        </label>
        <button type="button" disabled={saving} onClick={finish} className="mt-5 flex h-11 w-full items-center justify-center gap-2 rounded-xl bg-[var(--c-green)] text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50">
          {saving ? <span className="spinner" /> : <Icon name="check" className="w-4" />}{saving ? 'Đang lưu…' : 'Hoàn tất, vào ứng dụng'}
        </button>
      </>}
    </div>
  </div>
}
