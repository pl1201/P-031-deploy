'use client'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import { createApiClient, type MealPlan } from '@/lib/api'
import { getToken } from '@/lib/auth'

function statusLabel(s: string) {
  const map: Record<string, string> = {
    pending_review: 'Chờ duyệt',
    approved: 'Đã duyệt',
    rejected: 'Từ chối',
    drafting: 'Đang sinh',
    failed: 'Thất bại',
  }
  return map[s] ?? s
}

function statusClass(s: string) {
  const map: Record<string, string> = {
    pending_review: 'badge-pending',
    approved: 'badge-approved',
    rejected: 'badge-rejected',
    drafting: 'badge-draft',
    failed: 'badge-failed',
  }
  return `badge ${map[s] ?? 'badge-draft'}`
}

export default function DietitianDashboard() {
  const [plans, setPlans] = useState<MealPlan[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const token = getToken()
    if (!token) return
    createApiClient(token)
      .listPendingReviews()
      .then(setPlans)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const hardCount = (plan: MealPlan) => plan.violations.filter(v => v.severity === 'hard').length
  const softCount = (plan: MealPlan) => plan.violations.filter(v => v.severity === 'soft').length

  return (
    <>
      <div className="topbar">
        <div>
          <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: '.1em', textTransform: 'uppercase', color: 'var(--c-green2)', marginBottom: 4 }}>
            TỔNG QUAN
          </p>
          <h1 className="page-title">Hàng chờ duyệt</h1>
        </div>
        <div className="topbar-actions">
          <span className="synthetic-label">DỮ LIỆU MÔ PHỎNG</span>
          <Link href="/dietitian/patients" className="btn btn-primary btn-sm">
            + Sinh thực đơn mới
          </Link>
        </div>
      </div>

      <div className="page-body">
        {/* Stats row */}
        <div className="stats-grid" style={{ marginBottom: 28 }}>
          <div className="stat-cell">
            <div className="stat-label">Chờ duyệt</div>
            <div className="stat-value" style={{ color: loading ? 'var(--c-muted)' : 'var(--c-orange)' }}>
              {loading ? '—' : plans.length}
            </div>
          </div>
          <div className="stat-cell">
            <div className="stat-label">Vi phạm cứng</div>
            <div className="stat-value" style={{ color: 'var(--c-red)' }}>
              {loading ? '—' : plans.reduce((acc, p) => acc + hardCount(p), 0)}
            </div>
          </div>
          <div className="stat-cell">
            <div className="stat-label">Cảnh báo mềm</div>
            <div className="stat-value" style={{ color: 'var(--c-yellow)' }}>
              {loading ? '—' : plans.reduce((acc, p) => acc + softCount(p), 0)}
            </div>
          </div>
          <div className="stat-cell">
            <div className="stat-label">Cần xem xét</div>
            <div className="stat-value" style={{ color: 'var(--c-purple)' }}>
              {loading ? '—' : plans.filter(p => hardCount(p) > 0).length}
            </div>
          </div>
        </div>

        {/* Table */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Thực đơn chờ duyệt</h2>
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => {
                setLoading(true)
                setError('')
                const token = getToken()
                if (!token) return
                createApiClient(token).listPendingReviews().then(setPlans).catch(e => setError(e.message)).finally(() => setLoading(false))
              }}
            >
              ↻ Làm mới
            </button>
          </div>

          {loading ? (
            <div style={{ padding: 60, display: 'grid', placeItems: 'center' }}>
              <span className="spinner" style={{ width: 28, height: 28, color: 'var(--c-green)' }} />
            </div>
          ) : error ? (
            <div className="card-body">
              <div className="safety-strip safety-strip-error">{error}</div>
            </div>
          ) : plans.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">✓</div>
              <div className="empty-title">Không có thực đơn chờ duyệt</div>
              <div className="empty-desc">Tất cả thực đơn đã được xử lý.</div>
            </div>
          ) : (
            <div className="table-wrap" style={{ borderRadius: 0, border: 'none', borderTop: '1px solid var(--c-border)' }}>
              <table>
                <thead>
                  <tr>
                    <th>Mã thực đơn</th>
                    <th>Bệnh nhân</th>
                    <th>Ngày</th>
                    <th>Vi phạm</th>
                    <th>Lần thử</th>
                    <th>Trạng thái</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {plans.map(plan => (
                    <tr key={plan.id}>
                      <td>
                        <span className="font-mono text-sm" style={{ color: 'var(--c-muted)' }}>
                          #{plan.id.slice(0, 8)}
                        </span>
                      </td>
                      <td>
                        <span style={{ fontWeight: 500 }}>{plan.patient_id.slice(0, 12)}…</span>
                      </td>
                      <td style={{ color: 'var(--c-ink2)' }}>{plan.plan_date}</td>
                      <td>
                        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                          {hardCount(plan) > 0 && (
                            <span className="badge badge-hard">{hardCount(plan)} cứng</span>
                          )}
                          {softCount(plan) > 0 && (
                            <span className="badge badge-soft">{softCount(plan)} mềm</span>
                          )}
                          {hardCount(plan) === 0 && softCount(plan) === 0 && (
                            <span className="badge badge-ok">✓ Sạch</span>
                          )}
                        </div>
                      </td>
                      <td>
                        <span className="font-mono text-sm">{plan.retry_count}</span>
                      </td>
                      <td>
                        <span className={statusClass(plan.status)}>{statusLabel(plan.status)}</span>
                      </td>
                      <td>
                        <Link
                          href={`/dietitian/reviews/${plan.id}`}
                          className="btn btn-secondary btn-sm"
                        >
                          Xem & duyệt →
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <p className="disclaimer" style={{ marginTop: 20 }}>
          ⚕️ Chỉ thực đơn được chuyên gia duyệt mới hiển thị cho bệnh nhân. Kiểm tra kỹ vi phạm cứng (màu đỏ) trước khi duyệt.
        </p>
      </div>
    </>
  )
}
