'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { createApiClient, type MealPlan, type PatientProfile } from '@/lib/api'
import { getToken } from '@/lib/auth'

const STATUS_LABELS: Record<string, string> = {
  approved: 'Đã duyệt',
  rejected: 'Đã từ chối',
}

export default function ApprovalLogPage() {
  const [plans, setPlans] = useState<MealPlan[]>([])
  const [patients, setPatients] = useState<Record<string, PatientProfile>>({})
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState<'all' | 'approved' | 'rejected'>('all')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const token = getToken()
    if (!token) return
    const api = createApiClient(token)
    Promise.all([api.listMealPlans(undefined, undefined, 1), api.listPatients(1, 100)])
      .then(([history, patientResult]) => {
        setPlans(history.items.filter(plan => plan.status === 'approved' || plan.status === 'rejected'))
        setPatients(Object.fromEntries(patientResult.items.map(patient => [patient.id, patient])))
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const visible = plans.filter(plan => {
    const matchesFilter = filter === 'all' || plan.status === filter
    const matchesQuery = `${plan.id} ${plan.patient_id} ${plan.plan_date}`.toLowerCase().includes(query.toLowerCase())
    return matchesFilter && matchesQuery
  })

  return (
    <>
      <div className="topbar">
        <div><p className="page-kicker">Clinical audit trail</p><h1 className="page-title">Nhật ký phê duyệt</h1></div>
        <span className="synthetic-label">DỮ LIỆU MÔ PHỎNG</span>
      </div>
      <div className="page-body">
        <div className="page-heading-row" style={{ marginBottom: 18 }}>
          <div><h2 style={{ fontSize: 22 }}>Lịch sử quyết định chuyên gia</h2><p className="page-subtitle">Theo dõi thực đơn đã duyệt hoặc từ chối và mở lại đầy đủ bằng chứng của từng quyết định.</p></div>
          <span className="badge badge-draft">{plans.length} quyết định</span>
        </div>
        <div className="toolbar" style={{ marginBottom: 16 }}>
          <input className="search-box" value={query} onChange={e => setQuery(e.target.value)} placeholder="Tìm mã thực đơn, hồ sơ hoặc ngày…" aria-label="Tìm nhật ký" />
          <div className="clinical-tabs">
            {([['all', 'Tất cả'], ['approved', 'Đã duyệt'], ['rejected', 'Từ chối']] as const).map(([value, label]) => <button key={value} className={`clinical-tab${filter === value ? ' active' : ''}`} onClick={() => setFilter(value)}>{label}</button>)}
          </div>
        </div>
        <section className="card">
          {loading ? <div className="empty-state"><span className="spinner" /></div> : error ? <div className="card-body"><div className="safety-strip safety-strip-error">{error}</div></div> : visible.length === 0 ? <div className="empty-state"><div className="empty-title">Chưa có quyết định phù hợp</div><div className="empty-desc">Các lần duyệt và từ chối sẽ xuất hiện tại đây.</div></div> : (
            <div className="audit-list">
              {visible.map(plan => {
                const patient = patients[plan.patient_id]
                return <Link className="audit-row" href={`/dietitian/reviews/${plan.id}`} key={plan.id}>
                  <span className={`badge badge-${plan.status}`}>{STATUS_LABELS[plan.status]}</span>
                  <span className="patient-identity"><strong>{patient ? `${patient.sex === 'male' ? 'Nam' : 'Nữ'}, ${patient.age} tuổi` : 'Hồ sơ bệnh nhân'}</strong><span>#{plan.patient_id.slice(0, 8)}</span></span>
                  <span><strong>{plan.plan_date}</strong><small className="text-muted" style={{ display: 'block', marginTop: 3 }}>{plan.items.length} món · lần {plan.retry_count}</small></span>
                  <span className="font-mono text-sm">#{plan.id.slice(0, 8)}</span>
                  <span className="btn btn-secondary btn-sm">Xem chi tiết →</span>
                </Link>
              })}
            </div>
          )}
        </section>
      </div>
    </>
  )
}
