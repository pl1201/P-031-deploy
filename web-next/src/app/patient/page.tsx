'use client'
import { useEffect, useState } from 'react'
import { createApiClient, type MealPlan, type MealPlanItem } from '@/lib/api'
import { getToken, getSession } from '@/lib/auth'

const SLOT_LABELS: Record<string, string> = {
  breakfast: 'Bữa sáng',
  lunch: 'Bữa trưa',
  dinner: 'Bữa tối',
  snack: 'Bữa phụ',
}

export default function PatientDashboard() {
  const [plans, setPlans] = useState<MealPlan[]>([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<MealPlan | null>(null)

  useEffect(() => {
    const token = getToken()
    if (!token) return
    createApiClient(token)
      .listMealPlans(undefined, 'approved')
      .then(r => {
        setPlans(r.items)
        if (r.items.length > 0) setSelected(r.items[0])
      })
      .finally(() => setLoading(false))
  }, [])

  const nutrition = selected?.computed_nutrition

  const bySlot = selected?.items.reduce<Record<string, MealPlanItem[]>>((acc, item) => {
    ;(acc[item.slot] ??= []).push(item)
    return acc
  }, {}) ?? {}

  return (
    <>
      <div className="topbar">
        <h1 className="page-title">Thực đơn của tôi</h1>
        <div className="topbar-actions">
          {selected && (
            <span style={{ fontSize: 13, color: 'var(--c-muted)' }}>{selected.plan_date}</span>
          )}
        </div>
      </div>

      <div className="page-body">
        {loading ? (
          <div style={{ display: 'grid', placeItems: 'center', height: '50vh' }}>
            <span className="spinner" style={{ width: 32, height: 32, color: 'var(--c-green)' }} />
          </div>
        ) : plans.length === 0 ? (
          <div className="card" style={{ padding: 60, textAlign: 'center' }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>⌛</div>
            <h2 style={{ fontFamily: 'var(--f-serif)', fontSize: 24, marginBottom: 8 }}>Thực đơn đang chờ duyệt</h2>
            <p style={{ color: 'var(--c-muted)', maxWidth: 360, margin: '0 auto 20px' }}>
              Chuyên gia dinh dưỡng đang xem xét và sẽ phê duyệt thực đơn của bạn sớm nhất.
            </p>
            <p className="disclaimer" style={{ maxWidth: 400, margin: '0 auto' }}>
              ⚕️ Chỉ thực đơn được chuyên gia duyệt mới xuất hiện tại đây. Điều này đảm bảo an toàn cho bạn.
            </p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: 24, alignItems: 'start' }}>
            {/* Main */}
            <div style={{ display: 'grid', gap: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                <span className="badge badge-approved">✓ Đã duyệt bởi chuyên gia</span>
                {selected?.reviewer_notes && (
                  <span style={{ fontSize: 13, color: 'var(--c-muted)' }}>· {selected.reviewer_notes}</span>
                )}
              </div>

              {(['breakfast', 'lunch', 'dinner', 'snack'] as const).map(slot => {
                const items = bySlot[slot]
                if (!items?.length) return null
                return (
                  <div key={slot} className="card">
                    <div className="card-header">
                      <div>
                        <div className="slot-label">{SLOT_LABELS[slot]}</div>
                      </div>
                      <div style={{ fontSize: 12, color: 'var(--c-muted)' }}>{items.length} món</div>
                    </div>
                    <div className="card-body" style={{ padding: '12px 24px' }}>
                      {items.map(item => (
                        <div key={item.id} className="food-row">
                          <div className="dish-summary">
                            <div className="food-name">{item.name_vi}</div>
                            {item.is_estimated && (
                              <span className="badge badge-estimated" style={{ marginTop: 4, display: 'inline-block' }}>
                                Dữ liệu ước tính
                              </span>
                            )}
                            {item.ingredients.length > 0 && (
                              <details className="ingredient-details">
                                <summary>Xem {item.ingredients.length} nguyên liệu</summary>
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
                          <span className="food-grams">{item.grams} g</span>
                          <span className="source-chip" style={{ cursor: 'default' }}>{item.source}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Sidebar */}
            <div style={{ position: 'sticky', top: 80, display: 'grid', gap: 16 }}>
              {nutrition && (
                <div className="card">
                  <div className="card-header">
                    <h2 className="card-title">Dinh dưỡng ngày</h2>
                  </div>
                  <div className="card-body">
                    <div style={{ textAlign: 'center', marginBottom: 20 }}>
                      <div style={{ fontFamily: 'var(--f-serif)', fontSize: 44 }}>
                        {nutrition.kcal.toFixed(0)}
                      </div>
                      <div style={{ color: 'var(--c-muted)', fontSize: 13 }}>kcal hôm nay</div>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                      {[
                        { label: 'Carb', val: `${nutrition.carb_g.toFixed(0)} g`, color: 'var(--c-orange)' },
                        { label: 'Protein', val: `${nutrition.protein_g.toFixed(0)} g`, color: 'var(--c-sky)' },
                        { label: 'Chất béo', val: `${nutrition.fat_g.toFixed(0)} g`, color: 'var(--c-yellow)' },
                        { label: 'Chất xơ', val: `${nutrition.fiber_g.toFixed(0)} g`, color: 'var(--c-green2)' },
                      ].map(n => (
                        <div key={n.label} style={{ textAlign: 'center', padding: '12px 8px', background: 'var(--c-surface)', borderRadius: 'var(--r-md)' }}>
                          <div style={{ fontSize: 18, fontWeight: 700, color: n.color }}>{n.val}</div>
                          <div style={{ fontSize: 11, color: 'var(--c-muted)', marginTop: 2 }}>{n.label}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Lưu ý từ chuyên gia — API đã trả `violations` từ lâu nhưng màn
                  bệnh nhân trước đây bỏ qua hoàn toàn, nên bệnh nhân không hề
                  biết thực đơn của mình có điểm nào cần chú ý. Chỉ hiện cảnh
                  báo mềm (soft): thực đơn đã duyệt thì theo RULE-3 không thể
                  còn vi phạm cứng. */}
              {selected && selected.violations.filter(v => v.severity === 'soft').length > 0 && (
                <div className="card">
                  <div className="card-header"><h2 className="card-title">Điều cần lưu ý</h2></div>
                  <div className="card-body" style={{ display: 'grid', gap: 12 }}>
                    {selected.violations
                      .filter(v => v.severity === 'soft')
                      .map((v, i) => (
                        <div key={i} style={{ fontSize: 13, lineHeight: 1.5 }}>
                          <div style={{ display: 'flex', gap: 6, alignItems: 'flex-start' }}>
                            <span className="badge badge-soft">Lưu ý</span>
                            <span>{v.message_vi}</span>
                          </div>
                          {v.suggestion && (
                            <div style={{ color: 'var(--c-muted)', fontSize: 12.5, marginTop: 4 }}>
                              → {v.suggestion}
                            </div>
                          )}
                          {/* actual/limit là null với cảnh báo định tính (tương tác
                              thuốc–thực phẩm). Hiện "0" ở đây là bịa số — RULE-2. */}
                          {v.actual != null && v.limit != null && (
                            <div style={{ color: 'var(--c-muted)', fontSize: 12, marginTop: 2 }}>
                              {v.actual} / {v.limit} {v.unit}
                            </div>
                          )}
                        </div>
                      ))}
                  </div>
                </div>
              )}

              {plans.length > 1 && (
                <div className="card">
                  <div className="card-header"><h2 className="card-title">Lịch sử</h2></div>
                  <div className="card-body" style={{ padding: '8px 16px' }}>
                    {plans.map(p => (
                      <button
                        key={p.id}
                        onClick={() => setSelected(p)}
                        style={{
                          display: 'block', width: '100%', padding: '10px 0',
                          textAlign: 'left', borderBottom: '1px solid var(--c-border)',
                          fontSize: 13,
                          fontWeight: selected?.id === p.id ? 700 : 400,
                          color: selected?.id === p.id ? 'var(--c-green)' : 'var(--c-ink)',
                        }}
                      >
                        {p.plan_date}
                        <span className="badge badge-approved" style={{ marginLeft: 8 }}>✓</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <p className="disclaimer">
                ⚕️ Đây là thực đơn dành riêng cho bạn, được chuyên gia dinh dưỡng xem xét và phê duyệt. Không thay thế hướng dẫn của bác sĩ. Dữ liệu 100% mô phỏng.
              </p>
            </div>
          </div>
        )}
      </div>
    </>
  )
}
