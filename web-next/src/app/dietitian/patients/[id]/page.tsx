'use client'

import { useCallback, useEffect, useState } from 'react'
import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { createApiClient, type MealPlan, type PatientProfile } from '@/lib/api'
import { getToken } from '@/lib/auth'

const STATUS: Record<string, string> = {
  drafting: 'Đang sinh', pending_review: 'Chờ duyệt', approved: 'Đã duyệt',
  rejected: 'Đã từ chối', failed: 'Thất bại',
}

const CONDITION: Record<string, string> = {
  T2DM: 'Đái tháo đường type 2', HTN: 'Tăng huyết áp', CKD: 'Bệnh thận mạn', GOUT: 'Gout',
}

export default function PatientDetailPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const [patient, setPatient] = useState<PatientProfile | null>(null)
  const [plans, setPlans] = useState<MealPlan[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    const token = getToken()
    if (!token || !id) return
    setLoading(true)
    try {
      const api = createApiClient(token)
      const [profile, history] = await Promise.all([api.getPatient(id), api.listMealPlans(id)])
      setPatient(profile)
      setPlans(history.items)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Không tải được hồ sơ')
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => { load() }, [load])

  const generate = async () => {
    const token = getToken()
    if (!token || !patient) return
    setGenerating(true)
    try {
      const api = createApiClient(token)
      const result = await api.createMealPlan(patient.id)
      for (let attempt = 0; attempt < 30; attempt++) {
        await new Promise(resolve => setTimeout(resolve, 2000))
        const plan = await api.getMealPlan(result.plan_id)
        if (plan.status !== 'drafting') {
          router.push(`/dietitian/reviews/${result.plan_id}`)
          return
        }
      }
      setError('Thực đơn vẫn đang được xử lý. Bạn có thể kiểm tra lại trong lịch sử sau ít phút.')
      await load()
      setGenerating(false)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Không thể sinh thực đơn')
      setGenerating(false)
    }
  }

  if (loading) return <div style={{ display: 'grid', placeItems: 'center', height: '60vh' }}><span className="spinner" style={{ width: 34, height: 34 }} /></div>
  if (error && !patient) return <div className="page-body"><div className="safety-strip safety-strip-error">{error}</div></div>
  if (!patient) return null

  const bmi = (patient.weight_kg / (patient.height_cm / 100) ** 2).toFixed(1)

  return <>
    <div className="topbar">
      <div>
        <Link href="/dietitian/patients" style={{ color: 'var(--c-muted)', fontSize: 12 }}>← Hồ sơ bệnh nhân</Link>
        <h1 className="page-title" style={{ marginTop: 4 }}>Hồ sơ #{patient.id.slice(0, 8)}</h1>
      </div>
      <button className="btn btn-primary" onClick={generate} disabled={generating}>
        {generating ? 'Đang sinh…' : '+ Sinh thực đơn mới'}
      </button>
    </div>

    <div className="page-body" style={{ display: 'grid', gap: 24 }}>
      {error && <div className="safety-strip safety-strip-error">{error}</div>}
      <div className="card">
        <div className="card-header">
          <div><div className="slot-label">THÔNG TIN LÂM SÀNG</div><h2 className="card-title" style={{ marginTop: 4 }}>{patient.sex === 'male' ? 'Nam' : 'Nữ'}, {patient.age} tuổi</h2></div>
          <span className="synthetic-label">DỮ LIỆU MÔ PHỎNG</span>
        </div>
        <div className="card-body" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: 20 }}>
          <div><div className="stat-label">Thể trạng</div><strong>{patient.height_cm} cm · {patient.weight_kg} kg · BMI {bmi}</strong></div>
          <div><div className="stat-label">Bệnh lý</div><strong>{patient.conditions.map(c => CONDITION[c.code] ?? c.code).join(', ') || 'Chưa ghi nhận'}</strong></div>
          <div><div className="stat-label">Dị ứng</div><strong>{patient.allergies.join(', ') || 'Không'}</strong></div>
          <div><div className="stat-label">Thuốc đang dùng</div><strong>{patient.medications.join(', ') || 'Chưa ghi nhận'}</strong></div>
          <div><div className="stat-label">Vận động</div><strong>{patient.activity_level}</strong></div>
          <div><div className="stat-label">Khu vực</div><strong>{patient.region || 'Chưa chọn'}</strong></div>
        </div>
      </div>

      <div className="card">
        <div className="card-header"><h2 className="card-title">Lịch sử thực đơn</h2><span style={{ fontSize: 12, color: 'var(--c-muted)' }}>{plans.length} bản ghi</span></div>
        {plans.length === 0 ? <div className="empty-state"><div className="empty-title">Chưa có thực đơn</div><div className="empty-desc">Sinh thực đơn đầu tiên cho hồ sơ này.</div></div> :
          <div className="table-wrap" style={{ border: 0, borderTop: '1px solid var(--c-border)', borderRadius: 0 }}><table><thead><tr><th>Ngày áp dụng</th><th>Tạo lúc</th><th>Trạng thái</th><th>Ghi chú chuyên gia</th><th></th></tr></thead><tbody>
            {plans.map(plan => <tr key={plan.id}>
              <td><strong>{new Date(`${plan.plan_date}T00:00:00`).toLocaleDateString('vi-VN')}</strong></td>
              <td>{new Date(plan.created_at).toLocaleString('vi-VN')}</td>
              <td><span className={`badge badge-${plan.status}`}>{STATUS[plan.status] ?? plan.status}</span></td>
              <td style={{ color: 'var(--c-muted)' }}>{plan.reviewer_notes || '—'}</td>
              <td><Link href={`/dietitian/reviews/${plan.id}`} className="btn btn-secondary btn-sm">Xem thực đơn →</Link></td>
            </tr>)}
          </tbody></table></div>}
      </div>
    </div>
  </>
}
