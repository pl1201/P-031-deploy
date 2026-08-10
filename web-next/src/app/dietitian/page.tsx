'use client'

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { createApiClient, type MealPlan, type PatientProfile } from '@/lib/api'
import { getToken } from '@/lib/auth'

type QueueFilter = 'all' | 'hard' | 'warning' | 'ready'

const STATUS_LABEL: Record<string, string> = {
  pending_review: 'Chờ duyệt', approved: 'Đã duyệt', rejected: 'Từ chối', drafting: 'Đang sinh', failed: 'Thất bại',
}

export default function DietitianDashboard() {
  const [plans, setPlans] = useState<MealPlan[]>([])
  const [patients, setPatients] = useState<Record<string, PatientProfile>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState<QueueFilter>('all')

  const fetchData = async () => {
    const token = getToken()
    if (!token) return
    const api = createApiClient(token)
    try {
      const [pending, patientResult] = await Promise.all([api.listPendingReviews(), api.listPatients(1, 100)])
      setPlans(pending)
      setPatients(Object.fromEntries(patientResult.items.map(patient => [patient.id, patient])))
    } catch (errorValue) {
      setError(errorValue instanceof Error ? errorValue.message : 'Không thể tải dữ liệu hàng chờ.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const token = getToken()
    if (!token) return
    const api = createApiClient(token)
    Promise.all([api.listPendingReviews(), api.listPatients(1, 100)])
      .then(([pending, patientResult]) => {
        setPlans(pending)
        setPatients(Object.fromEntries(patientResult.items.map(patient => [patient.id, patient])))
      })
      .catch(errorValue => setError(errorValue instanceof Error ? errorValue.message : 'Không thể tải dữ liệu hàng chờ.'))
      .finally(() => setLoading(false))
  }, [])

  const refreshData = () => {
    setLoading(true)
    setError('')
    void fetchData()
  }

  const hardCount = (plan: MealPlan) => plan.violations.filter(item => item.severity === 'hard').length
  const softCount = (plan: MealPlan) => plan.violations.filter(item => item.severity === 'soft').length
  const totals = useMemo(() => ({
    all: plans.length,
    hard: plans.reduce((sum, plan) => sum + hardCount(plan), 0),
    warning: plans.reduce((sum, plan) => sum + softCount(plan), 0),
    ready: plans.filter(plan => hardCount(plan) === 0).length,
  }), [plans])
  const visiblePlans = plans.filter(plan => {
    const patient = patients[plan.patient_id]
    const matchesSearch = `${plan.id} ${plan.patient_id} ${plan.plan_date} ${patient?.conditions.map(item => item.code).join(' ') ?? ''}`.toLowerCase().includes(query.toLowerCase())
    const matchesFilter = filter === 'all' || (filter === 'hard' && hardCount(plan) > 0) || (filter === 'warning' && softCount(plan) > 0) || (filter === 'ready' && hardCount(plan) === 0)
    return matchesSearch && matchesFilter
  })

  return <>
    <header className="topbar">
      <div><p className="page-kicker">Clinical command center</p><h1 className="page-title">Tổng quan dinh dưỡng lâm sàng</h1></div>
      <div className="topbar-actions"><span className="synthetic-label">DỮ LIỆU MÔ PHỎNG</span><Link href="/dietitian/patients" className="btn btn-primary btn-sm">+ Sinh thực đơn</Link></div>
    </header>

    <div className="page-body">
      <section className="workspace-hero">
        <div><span className="hero-kicker">Ưu tiên hôm nay</span><h2>Ra quyết định nhanh.<br /><em>Vẫn giữ đủ bằng chứng.</em></h2><p>Mỗi thực đơn đều được tính lại phía server, kiểm tra an toàn và lưu dấu vết trước khi đến bệnh nhân.</p></div>
        <div className="hero-queue"><strong>{loading ? '—' : plans.length}</strong><span>ca cần chuyên gia xử lý</span><i /></div>
      </section>

      <section className="metric-grid queue-metrics" aria-label="Tóm tắt hàng chờ">
        {([
          ['all', 'Chờ quyết định', totals.all, 'Tổng trong hàng chờ', '#147fd1'],
          ['hard', 'Vi phạm cứng', totals.hard, 'Cần xử lý trước duyệt', '#cb4338'],
          ['warning', 'Cảnh báo mềm', totals.warning, 'Cần chuyên gia lưu ý', '#dc9b18'],
          ['ready', 'Sẵn sàng duyệt', totals.ready, 'Không có vi phạm cứng', '#17a27a'],
        ] as const).map(([key, label, value, note, color]) => <button key={key} className={`metric-card metric-button${filter === key ? ' selected' : ''}`} style={{ '--metric-color': color } as React.CSSProperties} onClick={() => setFilter(key)}>
          <span className="metric-label">{label}</span><strong className="metric-value">{loading ? '—' : value}</strong><span className="metric-note">{note}</span>
        </button>)}
      </section>

      <section className="queue-toolbar">
        <div className="queue-search"><span>⌕</span><input value={query} onChange={event => setQuery(event.target.value)} placeholder="Tìm mã thực đơn, hồ sơ hoặc ngày..." aria-label="Tìm trong hàng chờ" /></div>
        <div className="filter-pills" aria-label="Bộ lọc hàng chờ">
          <button className={filter === 'all' ? 'active' : ''} onClick={() => setFilter('all')}>Tất cả</button>
          <button className={filter === 'hard' ? 'active' : ''} onClick={() => setFilter('hard')}>Rủi ro cao</button>
          <button className={filter === 'ready' ? 'active' : ''} onClick={() => setFilter('ready')}>Sẵn sàng duyệt</button>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={refreshData}>↻ Làm mới</button>
      </section>

      <section className="card queue-panel">
        <div className="card-header"><div><h2 className="card-title">Hàng chờ phê duyệt</h2><p className="panel-subtitle">{visiblePlans.length} kết quả phù hợp</p></div><span className="live-data"><i /> Cập nhật từ API</span></div>
        {loading ? <div className="queue-skeleton">{[1,2,3].map(item => <div key={item}><i /><span /><b /></div>)}</div>
        : error ? <div className="card-body"><div className="safety-strip safety-strip-error">{error}</div></div>
        : visiblePlans.length === 0 ? <div className="empty-state"><div className="empty-icon">✓</div><div className="empty-title">Không có ca phù hợp</div><div className="empty-desc">Thử thay đổi bộ lọc hoặc từ khóa tìm kiếm.</div></div>
        : <div className="queue-list">
          {visiblePlans.map(plan => {
            const patient = patients[plan.patient_id]
            const hard = hardCount(plan); const soft = softCount(plan)
            return <article className="queue-case" key={plan.id}>
              <div className="case-priority" data-level={hard ? 'hard' : soft ? 'warning' : 'ready'} />
              <div className="case-patient"><div className="patient-mini-avatar">{patient?.sex === 'female' ? 'Nữ' : 'N'}</div><div><Link href={`/dietitian/patients/${plan.patient_id}`}>{patient ? `${patient.sex === 'male' ? 'Nam' : 'Nữ'}, ${patient.age} tuổi` : 'Hồ sơ bệnh nhân'}</Link><span>#{plan.patient_id.slice(0,8)} · {patient?.conditions.map(item => item.code).join(' · ') || 'Đang cập nhật'}</span></div></div>
              <div className="case-plan"><span>Mã thực đơn</span><strong>#{plan.id.slice(0,8)}</strong></div>
              <div className="case-plan"><span>Ngày kế hoạch</span><strong>{plan.plan_date}</strong></div>
              <div className="case-findings">{hard > 0 && <span className="badge badge-hard">{hard} cứng</span>}{soft > 0 && <span className="badge badge-soft">{soft} mềm</span>}{hard === 0 && soft === 0 && <span className="badge badge-ok">✓ An toàn</span>}</div>
              <span className="badge badge-pending">{STATUS_LABEL[plan.status] ?? plan.status}</span>
              <Link href={`/dietitian/reviews/${plan.id}`} className="btn btn-primary btn-sm">Xem và duyệt →</Link>
            </article>
          })}
        </div>}
      </section>
    </div>
  </>
}
