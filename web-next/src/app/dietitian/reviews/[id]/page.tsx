'use client'
import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { createApiClient, type MealPlan, type MealPlanItem, ApiError } from '@/lib/api'
import { getToken } from '@/lib/auth'

const SLOT_LABELS: Record<string, string> = {
  breakfast: 'Bữa sáng',
  lunch: 'Bữa trưa',
  dinner: 'Bữa tối',
  snack: 'Bữa phụ',
}
const SLOT_TIMES: Record<string, string> = {
  breakfast: '07:00',
  lunch: '12:00',
  dinner: '18:30',
  snack: '15:00',
}

function NutritionBar({ label, value, max, unit, colorClass }: {
  label: string; value: number; max?: number; unit: string; colorClass: string
}) {
  const pct = max ? Math.min((value / max) * 100, 120) : 0
  const over = pct > 100
  return (
    <div className="nutrition-bar-row">
      <span className="nutrition-bar-label">{label}</span>
      <div className="nutrition-bar-track">
        <div
          className={`nutrition-bar-fill ${over ? 'bar-over' : colorClass}`}
          style={{ width: `${Math.min(pct, 100)}%` }}
        />
      </div>
      <span className="nutrition-bar-val" style={{ color: over ? 'var(--c-red)' : undefined }}>
        {value.toFixed(0)} <span style={{ fontWeight: 400, color: 'var(--c-muted)', fontSize: 10 }}>{unit}</span>
      </span>
    </div>
  )
}

function SourcePopover({ item }: { item: MealPlanItem }) {
  const [open, setOpen] = useState(false)
  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      <button
        className="source-chip"
        onClick={() => setOpen(o => !o)}
        title={`Nguồn: ${item.source_ref}`}
      >
        ⌘ {item.source}
        {item.is_estimated && <span className="badge badge-estimated" style={{ padding: '1px 4px', marginLeft: 4 }}>~</span>}
      </button>
      {open && (
        <div style={{
          position: 'absolute', bottom: 'calc(100% + 6px)', left: 0, zIndex: 50,
          background: 'var(--c-card)', border: '1px solid var(--c-border)',
          borderRadius: 'var(--r-md)', padding: '12px 14px',
          boxShadow: 'var(--shadow-md)', minWidth: 240, maxWidth: 320,
          fontSize: 12, lineHeight: 1.5,
        }}>
          <div style={{ fontWeight: 700, marginBottom: 4 }}>{item.name_vi}</div>
          <div style={{ color: 'var(--c-muted)', marginBottom: 2 }}>Nguồn: <strong>{item.source}</strong></div>
          <div style={{ color: 'var(--c-muted)', fontSize: 11 }}>{item.source_ref}</div>
          {item.is_estimated && (
            <div style={{ marginTop: 6, color: 'var(--c-purple)', fontSize: 11 }}>
              ⚠ Dữ liệu ước tính — cần chuyên gia kiểm tra
            </div>
          )}
          <button
            onClick={() => setOpen(false)}
            style={{ position: 'absolute', top: 6, right: 8, color: 'var(--c-muted)', fontSize: 16 }}
          >×</button>
        </div>
      )}
    </div>
  )
}

export default function MealPlanReviewPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const [plan, setPlan] = useState<MealPlan | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [toast, setToast] = useState('')
  const [toastType, setToastType] = useState<'success' | 'error'>('success')
  const [gramEdits, setGramEdits] = useState<Record<string, number>>({})
  const [rejectReason, setRejectReason] = useState('')
  const [showRejectDialog, setShowRejectDialog] = useState(false)
  const [showApproveDialog, setShowApproveDialog] = useState(false)
  const [notes, setNotes] = useState('')

  const showToast = (msg: string, type: 'success' | 'error' = 'success') => {
    setToast(msg)
    setToastType(type)
    setTimeout(() => setToast(''), 3000)
  }

  useEffect(() => {
    const token = getToken()
    if (!token || !id) return

    let cancelled = false
    void createApiClient(token).getMealPlan(id as string)
      .then(p => {
        if (cancelled) return
        setPlan(p)
        const initial: Record<string, number> = {}
        p.items.forEach(item => { initial[item.id] = item.grams })
        setGramEdits(initial)
      })
      .catch(e => {
        if (!cancelled) setError(e.message)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => { cancelled = true }
  }, [id])

  const handleApprove = async () => {
    const token = getToken()
    if (!token || !plan) return
    setSaving(true)
    try {
      const edits = Object.entries(gramEdits)
        .filter(([itemId, grams]) => {
          const orig = plan.items.find(i => i.id === itemId)
          return orig && orig.grams !== grams
        })
        .map(([item_id, grams]) => ({ item_id, grams }))

      await createApiClient(token).approveMealPlan(plan.id, edits.length ? edits : undefined, notes || undefined)
      showToast(`Đã duyệt thực đơn #${plan.id.slice(0, 8)}`)
      setShowApproveDialog(false)
      setTimeout(() => router.push('/dietitian'), 1500)
    } catch (e) {
      showToast(e instanceof ApiError ? e.message : 'Không thể duyệt thực đơn', 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleReject = async () => {
    if (rejectReason.length < 10) {
      showToast('Lý do từ chối phải ít nhất 10 ký tự', 'error')
      return
    }
    const token = getToken()
    if (!token || !plan) return
    setSaving(true)
    try {
      await createApiClient(token).rejectMealPlan(plan.id, rejectReason)
      showToast('Đã từ chối thực đơn')
      setShowRejectDialog(false)
      setTimeout(() => router.push('/dietitian'), 1500)
    } catch (e) {
      showToast(e instanceof ApiError ? e.message : 'Không thể từ chối', 'error')
    } finally {
      setSaving(false)
    }
  }

  const hardViolations = plan?.violations.filter(v => v.severity === 'hard') ?? []
  const softViolations = plan?.violations.filter(v => v.severity === 'soft') ?? []
  const nutrition = plan?.computed_nutrition

  // Group items by slot
  const bySlot = plan?.items.reduce<Record<string, MealPlanItem[]>>((acc, item) => {
    ;(acc[item.slot] ??= []).push(item)
    return acc
  }, {}) ?? {}

  const targetKcal = plan?.targets?.kcal?.max_value ?? undefined

  if (loading) return (
    <div style={{ display: 'grid', placeItems: 'center', height: '60vh' }}>
      <span className="spinner" style={{ width: 36, height: 36, color: 'var(--c-green)' }} />
    </div>
  )
  if (error) return (
    <div className="page-body">
      <div className="safety-strip safety-strip-error">{error}</div>
      <Link href="/dietitian" className="btn btn-secondary" style={{ marginTop: 16 }}>← Quay lại</Link>
    </div>
  )
  if (!plan) return null

  return (
    <>
      <div className="topbar">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Link href="/dietitian" style={{ color: 'var(--c-muted)', fontSize: 13 }}>← Hàng chờ</Link>
          <span style={{ color: 'var(--c-border2)' }}>/</span>
          <Link href={`/dietitian/patients/${plan.patient_id}`} style={{ color: 'var(--c-green2)', fontSize: 13 }}>Hồ sơ bệnh nhân</Link>
          <span style={{ color: 'var(--c-border2)' }}>/</span>
          <span style={{ fontFamily: 'var(--f-mono)', fontSize: 13, color: 'var(--c-muted)' }}>#{plan.id.slice(0, 8)}</span>
        </div>
        <div className="topbar-actions">
          {plan.status === 'pending_review' && (
            <>
              <button
                className="btn btn-secondary"
                onClick={() => setShowRejectDialog(true)}
                disabled={saving}
              >
                ✕ Từ chối
              </button>
              <button
                className="btn btn-primary"
                onClick={() => setShowApproveDialog(true)}
                disabled={saving || hardViolations.length > 0}
                title={hardViolations.length > 0 ? 'Không thể duyệt khi còn vi phạm cứng' : ''}
              >
                ✓ Duyệt thực đơn
              </button>
            </>
          )}
          {plan.status !== 'pending_review' && (
            <span className={`badge badge-${plan.status}`} style={{ fontSize: 13, padding: '6px 12px' }}>
              {plan.status === 'approved' ? '✓ Đã duyệt' : plan.status === 'rejected' ? '✕ Đã từ chối' : plan.status}
            </span>
          )}
        </div>
      </div>

      <div className="page-body" style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 24, alignItems: 'start' }}>
        {/* Left — meal plan */}
        <div style={{ display: 'grid', gap: 20 }}>
          <section className="card" style={{ padding: '16px 18px' }} aria-label="Quy trình duyệt thực đơn">
            <div className="review-progress-grid">
              {[
                ['01', 'Đã sinh', 'Món và định lượng'],
                ['02', 'Đã kiểm định', hardViolations.length ? 'Cần xử lý' : 'Đạt kiểm tra cứng'],
                ['03', 'Chuyên gia duyệt', plan.status === 'pending_review' ? 'Đang chờ' : plan.status],
                ['04', 'Bệnh nhân nhận', plan.status === 'approved' ? 'Đã sẵn sàng' : 'Sau khi duyệt'],
              ].map(([step, label, detail]) => (
                <div key={step} style={{ padding: '10px 12px', borderRadius: 11, background: 'var(--c-surface)', border: '1px solid var(--c-border)' }}>
                  <div className="page-kicker" style={{ marginBottom: 3 }}>{step}</div>
                  <div style={{ fontSize: 12, fontWeight: 700 }}>{label}</div>
                  <div style={{ fontSize: 10, color: 'var(--c-muted)', marginTop: 3 }}>{detail}</div>
                </div>
              ))}
            </div>
          </section>
          {/* Safety strip */}
          {hardViolations.length > 0 && (
            <div className="safety-strip safety-strip-error">
              <span style={{ fontWeight: 700, marginRight: 4 }}>⚠ {hardViolations.length} vi phạm cứng</span>
              — Không thể duyệt cho đến khi xử lý xong.
            </div>
          )}
          {hardViolations.length === 0 && (
            <div className="safety-strip safety-strip-ok">
              <span>✓</span>
              <span>
                <strong>Không có vi phạm cứng</strong>
                {softViolations.length > 0 && ` · ${softViolations.length} cảnh báo mềm cần lưu ý`}
              </span>
            </div>
          )}

          {/* Meal slots */}
          {(['breakfast', 'lunch', 'dinner', 'snack'] as const).map(slot => {
            const items = bySlot[slot]
            if (!items?.length) return null
            return (
              <div key={slot} className="card">
                <div className="card-header">
                  <div>
                    <div className="slot-label">{SLOT_LABELS[slot]}</div>
                    <div className="slot-time">{SLOT_TIMES[slot]}</div>
                  </div>
                  <div style={{ textAlign: 'right', fontSize: 12, color: 'var(--c-muted)' }}>
                    {items.length} món
                  </div>
                </div>
                <div className="card-body" style={{ padding: '12px 24px' }}>
                  {items.map(item => (
                    <div key={item.id} className="dish-row">
                      <div className="dish-summary">
                        <div className="dish-name">{item.name_vi}</div>
                        <div className="dish-meta">
                          <span>Món ăn trong thực đơn</span>
                          <SourcePopover item={item} />
                        </div>
                        {item.ingredients.length > 0 && (
                          <details className="ingredient-details">
                            <summary>Dữ liệu tính khẩu phần · {item.ingredients.length} thành phần</summary>
                            <div className="ingredient-list">
                              {item.ingredients.map(ingredient => (
                                <div key={ingredient.food_id} className="ingredient-line">
                                  <span>{ingredient.name_vi}</span>
                                  <span>{ingredient.grams} g</span>
                                </div>
                              ))}
                            </div>
                          </details>
                        )}
                      </div>
                      {/* Gram editor */}
                      <div className="dish-portion">
                        <span style={{ display: 'block', fontFamily: 'var(--f-sans)', fontSize: 10, color: 'var(--c-muted)', marginBottom: 5 }}>Khẩu phần</span>
                        {plan.status === 'pending_review' ? (
                          <input type="number" className="form-input" aria-label={`Khẩu phần ${item.name_vi}`} style={{ width: 84, minHeight: 34, padding: '0 8px', fontSize: 13 }} value={gramEdits[item.id] ?? item.grams} min={1} max={2000} step={5} onChange={e => setGramEdits(prev => ({ ...prev, [item.id]: Number(e.target.value) }))} />
                        ) : <span>{item.grams} g</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}

          {/* Violations */}
          {plan.violations.length > 0 && (
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Vi phạm & Cảnh báo</h2>
              </div>
              <div className="card-body" style={{ display: 'grid', gap: 10 }}>
                {plan.violations.map((v, i) => (
                  <div key={i} style={{
                    padding: '12px 16px',
                    borderRadius: 'var(--r-md)',
                    background: v.severity === 'hard' ? '#fde8e8' : '#fef5e4',
                    border: `1px solid ${v.severity === 'hard' ? '#f5c6c6' : '#f5dfa0'}`,
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <span className={`badge badge-${v.severity}`}>{v.severity === 'hard' ? 'Cứng' : 'Mềm'}</span>
                      <span style={{ fontWeight: 600, fontSize: 13 }}>{v.message_vi}</span>
                    </div>
                    {v.suggestion && (
                      <div style={{ fontSize: 12, color: 'var(--c-muted)', marginTop: 4 }}>
                        💡 {v.suggestion}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right — sidebar */}
        <div style={{ display: 'grid', gap: 20, position: 'sticky', top: 80 }}>
          {/* Nutrition summary */}
          {nutrition && (
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Dinh dưỡng tổng</h2>
                <span style={{ fontSize: 11, color: 'var(--c-muted)' }}>Tính bởi server</span>
              </div>
              <div className="card-body">
                <div style={{ textAlign: 'center', marginBottom: 20 }}>
                  <div style={{ fontFamily: 'var(--f-serif)', fontSize: 40 }}>
                    {nutrition.kcal.toFixed(0)}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--c-muted)' }}>
                    kcal / ngày
                    {targetKcal && (
                      <span style={{ marginLeft: 6 }}>
                        (mục tiêu: {targetKcal.toFixed(0)})
                      </span>
                    )}
                  </div>
                </div>
                <div className="nutrition-bar-wrap">
                  <NutritionBar label="Năng lượng" value={nutrition.kcal} max={targetKcal ?? undefined} unit="kcal" colorClass="bar-kcal" />
                  <NutritionBar label="Carbohydrate" value={nutrition.carb_g} unit="g" colorClass="bar-carb" />
                  <NutritionBar label="Protein" value={nutrition.protein_g} unit="g" colorClass="bar-protein" />
                  <NutritionBar label="Chất béo" value={nutrition.fat_g} unit="g" colorClass="bar-fat" />
                  <NutritionBar label="Chất xơ" value={nutrition.fiber_g} unit="g" colorClass="bar-fiber" />
                  <NutritionBar label="Natri" value={nutrition.na_mg} max={2000} unit="mg" colorClass="bar-na" />
                </div>
                {nutrition.has_estimated && (
                  <div className="badge badge-estimated" style={{ marginTop: 12, display: 'block', textAlign: 'center' }}>
                    ⚠ Có món dùng dữ liệu ước tính
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Plan info */}
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Thông tin</h2>
            </div>
            <div className="card-body" style={{ fontSize: 13, display: 'grid', gap: 10 }}>
              {[
                ['Mã thực đơn', `#${plan.id.slice(0, 8)}`],
                ['Ngày', plan.plan_date],
                ['Số lần thử', String(plan.retry_count)],
                ['Trạng thái', plan.status],
                ['Tạo lúc', new Date(plan.created_at).toLocaleString('vi-VN')],
              ].map(([k, v]) => (
                <div key={k} style={{ display: 'grid', gridTemplateColumns: '110px 1fr', gap: 8 }}>
                  <span style={{ color: 'var(--c-muted)' }}>{k}</span>
                  <span style={{ fontWeight: 500 }}>{v}</span>
                </div>
              ))}
              {plan.reviewer_notes && (
                <div style={{ marginTop: 4, padding: '10px 12px', background: 'var(--c-surface)', borderRadius: 'var(--r-md)', fontSize: 12 }}>
                  <div style={{ fontWeight: 600, marginBottom: 4 }}>Ghi chú chuyên gia:</div>
                  {plan.reviewer_notes}
                </div>
              )}
            </div>
          </div>

          <p className="disclaimer">
            ⚕️ Mọi con số dinh dưỡng được tính bởi server từ cơ sở dữ liệu thực phẩm (không qua LLM). Sửa gram sẽ được tính lại tự động khi duyệt.
          </p>
        </div>
      </div>

      {/* Approve dialog */}
      {showApproveDialog && (
        <div className="dialog-backdrop" onMouseDown={() => setShowApproveDialog(false)}>
          <div className="dialog-card" onMouseDown={e => e.stopPropagation()}>
            <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: '.12em', textTransform: 'uppercase', color: 'var(--c-green2)', marginBottom: 8 }}>
              XÁC NHẬN LÂM SÀNG
            </p>
            <h2 className="dialog-title">Duyệt thực đơn này?</h2>
            <p style={{ color: 'var(--c-muted)', fontSize: 14, marginTop: 8, marginBottom: 20 }}>
              Sau khi duyệt, thực đơn sẽ hiển thị cho bệnh nhân. Các chỉnh sửa gram sẽ được tính lại dinh dưỡng trên server.
            </p>
            <div className="form-group" style={{ marginBottom: 20 }}>
              <label className="form-label" htmlFor="approve-notes">Ghi chú chuyên gia <span style={{ fontWeight: 400, color: 'var(--c-muted)' }}>(không bắt buộc)</span></label>
              <textarea
                id="approve-notes"
                className="form-textarea"
                placeholder="Ví dụ: Theo dõi đường huyết sau ăn trong tuần đầu..."
                value={notes}
                onChange={e => setNotes(e.target.value)}
                autoFocus
              />
            </div>
            <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
              <button className="btn btn-secondary" onClick={() => setShowApproveDialog(false)}>Hủy</button>
              <button className="btn btn-primary" onClick={handleApprove} disabled={saving}>
                {saving ? <><span className="spinner" style={{ width: 14, height: 14 }} /> Đang duyệt...</> : '✓ Xác nhận duyệt'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Reject dialog */}
      {showRejectDialog && (
        <div className="dialog-backdrop" onMouseDown={() => setShowRejectDialog(false)}>
          <div className="dialog-card" onMouseDown={e => e.stopPropagation()}>
            <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: '.12em', textTransform: 'uppercase', color: 'var(--c-red)', marginBottom: 8 }}>
              TỪ CHỐI THỰC ĐƠN
            </p>
            <h2 className="dialog-title">Từ chối thực đơn này?</h2>
            <p style={{ color: 'var(--c-muted)', fontSize: 14, marginTop: 8, marginBottom: 20 }}>
              Vui lòng cung cấp lý do rõ ràng để agent có thể sinh lại thực đơn phù hợp hơn.
            </p>
            <div className="form-group" style={{ marginBottom: 20 }}>
              <label className="form-label" htmlFor="reject-reason">Lý do từ chối <span style={{ color: 'var(--c-red)' }}>*</span></label>
              <textarea
                id="reject-reason"
                className="form-textarea"
                placeholder="Ví dụ: Thực đơn quá nhiều carbohydrate vào bữa tối, cần phân bổ đều hơn..."
                value={rejectReason}
                onChange={e => setRejectReason(e.target.value)}
                autoFocus
                style={{ minHeight: 100 }}
              />
              <span style={{ fontSize: 11, color: rejectReason.length < 10 ? 'var(--c-red)' : 'var(--c-muted)' }}>
                {rejectReason.length}/10 ký tự tối thiểu
              </span>
            </div>
            <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
              <button className="btn btn-secondary" onClick={() => setShowRejectDialog(false)}>Hủy</button>
              <button className="btn btn-danger" onClick={handleReject} disabled={saving || rejectReason.length < 10}>
                {saving ? <><span className="spinner" style={{ width: 14, height: 14 }} /> Đang xử lý...</> : '✕ Xác nhận từ chối'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Toast */}
      {toast && (
        <div className="toast-wrap">
          <div className={`toast toast-${toastType}`}>{toast}</div>
        </div>
      )}
    </>
  )
}
