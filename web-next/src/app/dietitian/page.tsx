'use client'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import { createApiClient, type MealPlan, type PatientProfile } from '@/lib/api'
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
  const [query, setQuery] = useState('')
  const [patients, setPatients] = useState<Record<string, PatientProfile>>({})

  useEffect(() => {
    const token = getToken()
    if (!token) return
    const api = createApiClient(token)
    Promise.all([api.listPendingReviews(), api.listPatients(1, 100)])
      .then(([pending, patientResult]) => {
        setPlans(pending)
        setPatients(Object.fromEntries(patientResult.items.map(patient => [patient.id, patient])))
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const hardCount = (plan: MealPlan) => plan.violations.filter(v => v.severity === 'hard').length
  const softCount = (plan: MealPlan) => plan.violations.filter(v => v.severity === 'soft').length
  const visiblePlans = plans.filter(plan => `${plan.id} ${plan.patient_id} ${plan.plan_date}`.toLowerCase().includes(query.toLowerCase()))
  const createdTime = (createdAt: string) => new Date(createdAt).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })

  return (
    <>
      <div className="topbar">
        <div>
          <p className="page-kicker">Clinical command center</p>
          <h1 className="page-title">Trung tâm duyệt thực đơn</h1>
        </div>
        <div className="topbar-actions">
          <span className="synthetic-label">DỮ LIỆU MÔ PHỎNG</span>
          <Link href="/dietitian/patients" className="btn btn-primary btn-sm">
            + Sinh thực đơn mới
          </Link>
        </div>
      </div>

      <div className="page-body">
        <section className="clinical-summary" aria-label="Tóm tắt hàng chờ">
          <div className="clinical-summary-title">Ưu tiên xử lý hôm nay</div>
          <div className="clinical-summary-item"><strong>{loading ? '—' : plans.length}</strong> chờ quyết định</div>
          <div className="clinical-summary-item"><strong>{loading ? '—' : plans.reduce((acc, p) => acc + hardCount(p), 0)}</strong> vi phạm cứng</div>
          <div className="clinical-summary-item"><strong>{loading ? '—' : plans.reduce((acc, p) => acc + softCount(p), 0)}</strong> cảnh báo</div>
          <div className="clinical-summary-item"><strong>{loading ? '—' : plans.filter(p => hardCount(p) === 0).length}</strong> sẵn sàng duyệt</div>
        </section>

        <div className="toolbar" style={{ marginBottom: 14 }}>
          <input className="search-box" aria-label="Tìm thực đơn" value={query} onChange={e => setQuery(e.target.value)} placeholder="Tìm mã thực đơn, bệnh nhân hoặc ngày…" />
          <span className="status-rail"><i /> Cập nhật theo dữ liệu API</span>
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
              <table className="queue-table">
                <thead>
                  <tr>
                    <th>Mã thực đơn</th>
                    <th>Bệnh nhân</th>
                    <th>Hồ sơ lâm sàng</th>
                    <th>Ngày / chờ</th>
                    <th>Vi phạm</th>
                    <th>Lần thử</th>
                    <th>Trạng thái</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {visiblePlans.map(plan => (
                    <tr key={plan.id}>
                      <td>
                        <span className="font-mono text-sm" style={{ color: 'var(--c-muted)' }}>
                          #{plan.id.slice(0, 8)}
                        </span>
                      </td>
                      <td>
                        <Link href={`/dietitian/patients/${plan.patient_id}`} className="patient-identity">
                          <strong>{patients[plan.patient_id] ? `${patients[plan.patient_id].sex === 'male' ? 'Nam' : 'Nữ'}, ${patients[plan.patient_id].age} tuổi` : 'Hồ sơ bệnh nhân'}</strong>
                          <span>#{plan.patient_id.slice(0, 8)}</span>
                        </Link>
                      </td>
                      <td><div>{plan.plan_date}</div><div className="text-muted" style={{ fontSize: 10, marginTop: 3 }}>Tạo lúc {createdTime(plan.created_at)}</div></td>
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
