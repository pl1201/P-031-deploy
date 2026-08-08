'use client'

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { createApiClient, type MealPlan, type PatientProfile } from '@/lib/api'
import { getToken } from '@/lib/auth'

export default function ApprovalLogPage() {
  const [plans, setPlans] = useState<MealPlan[]>([])
  const [patients, setPatients] = useState<PatientProfile[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const token = getToken()
    if (!token) return
    const api = createApiClient(token)
    Promise.all([api.listMealPlans(undefined, 'approved'), api.listPatients(1, 100)])
      .then(([history, profiles]) => { setPlans(history.items); setPatients(profiles.items) })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const patientById = useMemo(() => new Map(patients.map(p => [p.id, p])), [patients])

  return <>
    <div className="topbar"><div><div className="slot-label">KIỂM SOÁT LÂM SÀNG</div><h1 className="page-title">Nhật ký phê duyệt</h1></div><span className="badge badge-approved">{plans.length} đã duyệt</span></div>
    <div className="page-body">
      <div className="safety-strip safety-strip-ok" style={{ marginBottom: 20 }}>✓ Chỉ hiển thị các thực đơn đã qua cổng chuyên gia và đang khả dụng cho bệnh nhân.</div>
      <div className="card">
        {loading ? <div style={{ padding: 60, display: 'grid', placeItems: 'center' }}><span className="spinner" style={{ width: 30, height: 30 }} /></div> : error ?
          <div className="card-body"><div className="safety-strip safety-strip-error">{error}</div></div> : plans.length === 0 ?
          <div className="empty-state"><div className="empty-title">Chưa có thực đơn được duyệt</div><div className="empty-desc">Các lần phê duyệt sẽ xuất hiện tại đây.</div></div> :
          <div className="table-wrap" style={{ border: 0, borderRadius: 0 }}><table><thead><tr><th>Bệnh nhân</th><th>Ngày thực đơn</th><th>Tạo lúc</th><th>Người duyệt</th><th>Ghi chú</th><th></th></tr></thead><tbody>
            {plans.map(plan => {
              const patient = patientById.get(plan.patient_id)
              return <tr key={plan.id}>
                <td><Link href={`/dietitian/patients/${plan.patient_id}`} style={{ fontWeight: 650, color: 'var(--c-green)' }}>#{plan.patient_id.slice(0, 8)}</Link><div style={{ fontSize: 11, color: 'var(--c-muted)', marginTop: 3 }}>{patient ? `${patient.sex === 'male' ? 'Nam' : 'Nữ'}, ${patient.age} tuổi · ${patient.conditions.map(c => c.code).join(', ')}` : 'Hồ sơ không còn trong danh sách'}</div></td>
                <td>{new Date(`${plan.plan_date}T00:00:00`).toLocaleDateString('vi-VN')}</td>
                <td>{new Date(plan.created_at).toLocaleString('vi-VN')}</td>
                <td><span className="font-mono text-sm">{plan.reviewer_id ? `#${plan.reviewer_id.slice(0, 8)}` : '—'}</span></td>
                <td style={{ maxWidth: 280 }}>{plan.reviewer_notes || 'Không có ghi chú'}</td>
                <td><Link href={`/dietitian/reviews/${plan.id}`} className="btn btn-secondary btn-sm">Xem →</Link></td>
              </tr>
            })}
          </tbody></table></div>}
      </div>
    </div>
  </>
}
