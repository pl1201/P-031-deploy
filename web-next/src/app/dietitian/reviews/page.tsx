'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { createApiClient, type MealPlan, type PatientProfile } from '@/lib/api'
import { getToken } from '@/lib/auth'
import { notifyReviewQueueChanged } from '@/lib/review-queue'

const STATUS_LABELS: Record<string, string> = {
  approved: 'Đã duyệt', rejected: 'Đã từ chối', pending_review: 'Chờ duyệt', manual_review_required: 'Bị chặn',
}
const STATUS_BADGE: Record<string, string> = {
  approved: 'approved', rejected: 'rejected', pending_review: 'pending', manual_review_required: 'rejected',
}
type Tab = 'pending' | 'all' | 'approved' | 'rejected'
type BulkAction = 'approve' | 'reject'

export default function ApprovalLogPage() {
  const [pending, setPending] = useState<MealPlan[]>([])
  const [plans, setPlans] = useState<MealPlan[]>([])
  const [patients, setPatients] = useState<Record<string, PatientProfile>>({})
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState<Tab>('pending')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [bulkAction, setBulkAction] = useState<BulkAction | null>(null)
  const [bulkNote, setBulkNote] = useState('')
  const [bulkBusy, setBulkBusy] = useState(false)
  const [bulkMessage, setBulkMessage] = useState('')

  useEffect(() => {
    const token = getToken()
    if (!token) return
    const api = createApiClient(token)
    Promise.all([api.listPendingReviews(), api.listMealPlans(undefined, undefined, 1), api.listPatients(1, 100)])
      .then(([queue, history, patientResult]) => {
        setPending(queue)
        notifyReviewQueueChanged(queue.length)
        setPlans(history.items.filter(plan => plan.status === 'approved' || plan.status === 'rejected'))
        setPatients(Object.fromEntries(patientResult.items.map(patient => [patient.id, patient])))
      })
      .catch(value => setError(value instanceof Error ? value.message : 'Không thể tải hàng chờ.'))
      .finally(() => setLoading(false))
  }, [])

  const source = filter === 'pending' ? pending : plans
  const visible = source.filter(plan => {
    const matchesFilter = filter === 'pending' || filter === 'all' || plan.status === filter
    const matchesQuery = `${plan.id} ${plan.patient_id} ${plan.plan_date}`.toLowerCase().includes(query.toLowerCase())
    return matchesFilter && matchesQuery
  })
  const visiblePendingIds = filter === 'pending' ? visible.map(plan => plan.id) : []
  const allVisibleSelected = visiblePendingIds.length > 0 && visiblePendingIds.every(id => selected.has(id))

  const toggleAllVisible = () => setSelected(current => {
    const next = new Set(current)
    if (allVisibleSelected) visiblePendingIds.forEach(id => next.delete(id))
    else visiblePendingIds.forEach(id => next.add(id))
    return next
  })

  const togglePlan = (id: string) => setSelected(current => {
    const next = new Set(current)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    return next
  })

  const runBulkAction = async () => {
    const token = getToken()
    if (!token || !bulkAction || selected.size === 0 || bulkNote.trim().length < 10) return
    setBulkBusy(true)
    setBulkMessage('')
    const api = createApiClient(token)
    const chosen = pending.filter(plan => selected.has(plan.id))
    const succeeded = new Set<string>()
    const failed: string[] = []

    // Xử lý tuần tự để mỗi plan đi qua đầy đủ cổng an toàn và audit của backend.
    for (const plan of chosen) {
      try {
        if (bulkAction === 'approve') await api.approveMealPlan(plan.id, undefined, bulkNote.trim())
        else await api.rejectMealPlan(plan.id, bulkNote.trim())
        succeeded.add(plan.id)
      } catch (value) {
        failed.push(`#${plan.id.slice(0, 8)}: ${value instanceof Error ? value.message : 'Không thể xử lý'}`)
      }
    }

    const remaining = pending.filter(plan => !succeeded.has(plan.id))
    const verb = bulkAction === 'approve' ? 'duyệt' : 'từ chối'
    setPending(remaining)
    setSelected(new Set())
    notifyReviewQueueChanged(remaining.length)
    setBulkBusy(false)
    setBulkAction(null)
    setBulkNote('')
    setBulkMessage(`Đã ${verb} ${succeeded.size}/${chosen.length} thực đơn.${failed.length ? ` Không xử lý được: ${failed.join(' · ')}` : ''}`)
  }

  return <>
    <div className="topbar">
      <div><p className="page-kicker">Clinical audit trail</p><h1 className="page-title">Hàng chờ &amp; nhật ký phê duyệt</h1></div>
      <span className="synthetic-label">DỮ LIỆU MÔ PHỎNG</span>
    </div>
    <div className="page-body">
      <div className="page-heading-row" style={{ marginBottom: 18 }}>
        <div><h2 style={{ fontSize: 22 }}>{filter === 'pending' ? 'Thực đơn đang chờ chuyên gia' : 'Lịch sử quyết định chuyên gia'}</h2><p className="page-subtitle">{filter === 'pending' ? 'Bản nháp đã sinh và kiểm tra xong, chờ chuyên gia quyết định.' : 'Theo dõi thực đơn đã duyệt hoặc từ chối và toàn bộ bằng chứng của từng quyết định.'}</p></div>
        <span className="badge badge-draft">{filter === 'pending' ? `${pending.length} chờ duyệt` : `${plans.length} quyết định`}</span>
      </div>
      <div className="toolbar" style={{ marginBottom: 16 }}>
        <input className="search-box" value={query} onChange={event => setQuery(event.target.value)} placeholder="Tìm mã thực đơn, hồ sơ hoặc ngày…" aria-label="Tìm nhật ký" />
        <div className="clinical-tabs">{([['pending', `Chờ duyệt (${pending.length})`], ['all', 'Tất cả quyết định'], ['approved', 'Đã duyệt'], ['rejected', 'Từ chối']] as const).map(([value, label]) => <button type="button" key={value} className={`clinical-tab${filter === value ? ' active' : ''}`} onClick={() => setFilter(value)}>{label}</button>)}</div>
      </div>
      {filter === 'pending' && !loading && !error && pending.length > 0 && <div className="bulk-review-bar">
        <label className="bulk-review-select"><input type="checkbox" checked={allVisibleSelected} onChange={toggleAllVisible} /> Chọn tất cả đang hiển thị</label>
        <span className="bulk-review-count">Đã chọn {selected.size}</span>
        <button type="button" className="btn btn-secondary btn-sm" disabled={selected.size === 0} onClick={() => setBulkAction('reject')}>Từ chối đã chọn</button>
        <button type="button" className="btn btn-primary btn-sm" disabled={selected.size === 0} onClick={() => setBulkAction('approve')}>Duyệt đã chọn</button>
      </div>}
      {bulkMessage && <div className={`safety-strip ${bulkMessage.includes('Không xử lý được') ? 'safety-strip-warning' : 'safety-strip-success'}`} role="status" style={{ marginBottom: 16 }}>{bulkMessage}</div>}
      <section className="card">
        {loading ? <div className="empty-state"><span className="spinner" /></div> : error ? <div className="card-body"><div className="safety-strip safety-strip-error">{error}</div></div> : visible.length === 0 ? <div className="empty-state"><div className="empty-title">{filter === 'pending' ? 'Không có thực đơn chờ duyệt' : 'Chưa có quyết định phù hợp'}</div><div className="empty-desc">{filter === 'pending' ? 'Các bản nháp đã qua bước sinh và kiểm tra sẽ xuất hiện tại đây.' : 'Các lần duyệt và từ chối sẽ xuất hiện tại đây.'}</div></div> : <div className="audit-list">
          {visible.map(plan => {
            const patient = patients[plan.patient_id]
            const identity = <span className="patient-identity"><strong>{patient ? `${patient.sex === 'male' ? 'Nam' : 'Nữ'}, ${patient.age} tuổi` : 'Hồ sơ bệnh nhân'}</strong><span>#{plan.patient_id.slice(0, 8)}</span></span>
            const date = <span><strong>{plan.plan_date}</strong><small className="text-muted" style={{ display: 'block', marginTop: 3 }}>{plan.items.length} món · sinh lần {plan.retry_count} · bản {plan.menu_version}</small></span>
            const status = <span className={`badge badge-${STATUS_BADGE[plan.status] ?? 'draft'}`}>{STATUS_LABELS[plan.status] ?? plan.status}</span>
            if (filter === 'pending') return <div className="audit-row audit-row-selectable" key={plan.id}>
              <label className="audit-check" aria-label={`Chọn thực đơn ${plan.id}`}><input type="checkbox" checked={selected.has(plan.id)} onChange={() => togglePlan(plan.id)} /></label>
              {status}{identity}{date}<span className="font-mono text-sm">#{plan.id.slice(0, 8)}</span><Link className="btn btn-secondary btn-sm" href={`/dietitian/reviews/${plan.id}`}>Xem xét →</Link>
            </div>
            return <Link className="audit-row" href={`/dietitian/reviews/${plan.id}`} key={plan.id}>{status}{identity}{date}<span className="font-mono text-sm">#{plan.id.slice(0, 8)}</span><span className="btn btn-secondary btn-sm">Xem chi tiết →</span></Link>
          })}
        </div>}
      </section>
    </div>
    {bulkAction && <div className="bulk-review-overlay" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget && !bulkBusy) setBulkAction(null) }}>
      <section className="bulk-review-dialog" role="dialog" aria-modal="true" aria-labelledby="bulk-review-title">
        <div className={`bulk-review-dialog-mark ${bulkAction}`}>{bulkAction === 'approve' ? '✓' : '×'}</div>
        <h2 id="bulk-review-title">{bulkAction === 'approve' ? `Duyệt ${selected.size} thực đơn` : `Từ chối ${selected.size} thực đơn`}</h2>
        <p>{bulkAction === 'approve' ? 'Mỗi thực đơn vẫn được backend kiểm tra độc lập. Bản bị cổng an toàn chặn sẽ không được duyệt.' : 'Lý do sẽ được lưu vào nhật ký kiểm toán của từng thực đơn.'}</p>
        <label>{bulkAction === 'approve' ? 'Ghi chú phê duyệt' : 'Lý do từ chối'}<textarea autoFocus value={bulkNote} onChange={event => setBulkNote(event.target.value)} placeholder="Nhập tối thiểu 10 ký tự…" rows={4} /></label>
        <small className={bulkNote.length > 0 && bulkNote.trim().length < 10 ? 'text-danger' : 'text-muted'}>{bulkNote.trim().length}/10 ký tự tối thiểu</small>
        <div className="bulk-review-dialog-actions"><button type="button" className="btn btn-secondary" disabled={bulkBusy} onClick={() => setBulkAction(null)}>Hủy</button><button type="button" className={`btn ${bulkAction === 'approve' ? 'btn-primary' : 'btn-danger'}`} disabled={bulkBusy || bulkNote.trim().length < 10} onClick={runBulkAction}>{bulkBusy ? 'Đang xử lý…' : bulkAction === 'approve' ? 'Xác nhận duyệt' : 'Xác nhận từ chối'}</button></div>
      </section>
    </div>}
  </>
}
