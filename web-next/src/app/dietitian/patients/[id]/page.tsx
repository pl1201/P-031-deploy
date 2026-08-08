'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { createApiClient, type MealPlan, type PatientProfile } from '@/lib/api'
import { getToken } from '@/lib/auth'

const CONDITION_LABELS: Record<string, string> = {
  T2DM: 'Đái tháo đường type 2',
  HTN: 'Tăng huyết áp',
  CKD: 'Bệnh thận mạn',
  GOUT: 'Gout',
}

const STATUS_LABELS: Record<string, string> = {
  drafting: 'Đang sinh',
  pending_review: 'Chờ duyệt',
  approved: 'Đã duyệt',
  rejected: 'Đã từ chối',
  failed: 'Thất bại',
}

const STATUS_CLASS: Record<string, string> = {
  drafting: 'badge-draft',
  pending_review: 'badge-pending',
  approved: 'badge-approved',
  rejected: 'badge-rejected',
  failed: 'badge-failed',
}

export default function PatientDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [patient, setPatient] = useState<PatientProfile | null>(null)
  const [plans, setPlans] = useState<MealPlan[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState<'overview' | 'plans'>('plans')

  useEffect(() => {
    const token = getToken()
    if (!token || !id) return
    let cancelled = false
    const api = createApiClient(token)
    void Promise.all([api.getPatient(id), api.listMealPlans(id)])
      .then(([profile, history]) => {
        if (cancelled) return
        setPatient(profile)
        setPlans(history.items)
      })
      .catch(e => { if (!cancelled) setError(e.message) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [id])

  if (loading) return <div style={{ display: 'grid', placeItems: 'center', height: '60vh' }}><span className="spinner" style={{ width: 34, height: 34, color: 'var(--c-green2)' }} /></div>
  if (error || !patient) return <div className="page-body"><div className="safety-strip safety-strip-error">{error || 'Không tìm thấy hồ sơ'}</div></div>

  const bmi = patient.weight_kg / (patient.height_cm / 100) ** 2
  const latestPlan = plans[0]
  const approvedCount = plans.filter(plan => plan.status === 'approved').length
  const pendingCount = plans.filter(plan => plan.status === 'pending_review').length

  return (
    <>
      <div className="topbar">
        <div>
          <p className="page-kicker">Patient record · #{patient.id.slice(0, 8)}</p>
          <h1 className="page-title">Hồ sơ dinh dưỡng cá nhân</h1>
        </div>
        <div className="topbar-actions">
          <Link href="/dietitian/patients" className="btn btn-secondary">← Danh sách</Link>
          <Link href="/dietitian/patients" className="btn btn-primary">+ Sinh thực đơn mới</Link>
        </div>
      </div>

      <div className="page-body">
        <section className="command-banner" style={{ minHeight: 176 }}>
          <div style={{ position: 'relative', zIndex: 1 }}>
            <div style={{ display: 'flex', gap: 7, flexWrap: 'wrap', marginBottom: 12 }}>
              {patient.conditions.map(condition => <span key={condition.code} className="badge" style={{ color: '#0b4b8a', background: '#dff1ff', border: '1px solid rgba(255,255,255,.45)' }}>{CONDITION_LABELS[condition.code] ?? condition.code}{condition.stage ? ` · ${condition.stage}` : ''}</span>)}
            </div>
            <h2>{patient.sex === 'male' ? 'Nam' : 'Nữ'}, {patient.age} tuổi · BMI {bmi.toFixed(1)}</h2>
            <p>{patient.height_cm} cm · {patient.weight_kg} kg · Mức hoạt động {patient.activity_level} · Khu vực {patient.region ?? 'chưa cập nhật'}</p>
          </div>
          <div className="banner-meta">
            <strong>{plans.length}</strong>
            <span>thực đơn trong lịch sử</span>
          </div>
        </section>

        <div className="metric-grid">
          <div className="metric-card"><div className="metric-label">Thực đơn gần nhất</div><div className="metric-value" style={{ fontSize: 22 }}>{latestPlan?.plan_date ?? '—'}</div><div className="metric-note">{latestPlan ? STATUS_LABELS[latestPlan.status] : 'Chưa có dữ liệu'}</div></div>
          <div className="metric-card" style={{ '--metric-color': '#239ac7' } as React.CSSProperties}><div className="metric-label">Đã được duyệt</div><div className="metric-value">{approvedCount}</div><div className="metric-note">Có thể hiển thị cho bệnh nhân</div></div>
          <div className="metric-card" style={{ '--metric-color': '#e8b84b' } as React.CSSProperties}><div className="metric-label">Đang chờ duyệt</div><div className="metric-value">{pendingCount}</div><div className="metric-note">Cần chuyên gia quyết định</div></div>
          <div className="metric-card" style={{ '--metric-color': '#596fc7' } as React.CSSProperties}><div className="metric-label">Dị ứng đã ghi nhận</div><div className="metric-value">{patient.allergies.length}</div><div className="metric-note">{patient.allergies.join(', ') || 'Không ghi nhận'}</div></div>
        </div>

        <div className="clinical-tabs" style={{ marginBottom: 18 }}>
          <button className={`clinical-tab${activeTab === 'plans' ? ' active' : ''}`} onClick={() => setActiveTab('plans')}>Lịch sử thực đơn</button>
          <button className={`clinical-tab${activeTab === 'overview' ? ' active' : ''}`} onClick={() => setActiveTab('overview')}>Thông tin lâm sàng</button>
        </div>

        {activeTab === 'plans' ? (
          <section className="card">
            <div className="card-header"><div><h2 className="card-title">Lịch sử thực đơn</h2><p className="page-subtitle">Bao gồm bản đang sinh, chờ duyệt, đã duyệt và bị từ chối.</p></div><span className="badge badge-draft">{plans.length} bản</span></div>
            <div className="card-body">
              {plans.length === 0 ? <div className="empty-state"><div className="empty-icon">◇</div><div className="empty-title">Chưa có thực đơn</div><div className="empty-desc">Sinh thực đơn đầu tiên từ hồ sơ này.</div></div> : (
                <div className="plan-history-grid">
                  {plans.map(plan => {
                    const hard = plan.violations.filter(item => item.severity === 'hard').length
                    return <Link key={plan.id} href={`/dietitian/reviews/${plan.id}`} className="plan-history-card">
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}><span className={`badge ${STATUS_CLASS[plan.status] ?? 'badge-draft'}`}>{STATUS_LABELS[plan.status] ?? plan.status}</span><span className="font-mono text-sm text-muted">#{plan.id.slice(0, 8)}</span></div>
                      <div style={{ fontFamily: 'var(--f-serif)', fontSize: 22, marginTop: 14 }}>{plan.plan_date}</div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 12, fontSize: 11, color: 'var(--c-muted)' }}><span>{plan.items.length} món · lần thử {plan.retry_count}</span><span style={{ color: hard ? 'var(--c-red)' : 'var(--c-green2)' }}>{hard ? `${hard} vi phạm cứng` : 'Sẵn sàng xem'}</span></div>
                    </Link>
                  })}
                </div>
              )}
            </div>
          </section>
        ) : (
          <section className="card">
            <div className="card-header"><h2 className="card-title">Thông tin phục vụ lập thực đơn</h2></div>
            <div className="card-body">
              <div className="info-grid">
                <div className="info-tile"><span>Tuổi / giới tính</span><strong>{patient.age} · {patient.sex === 'male' ? 'Nam' : 'Nữ'}</strong></div>
                <div className="info-tile"><span>Chiều cao / cân nặng</span><strong>{patient.height_cm} cm · {patient.weight_kg} kg</strong></div>
                <div className="info-tile"><span>Mức hoạt động</span><strong>{patient.activity_level}</strong></div>
                <div className="info-tile"><span>Dị ứng</span><strong>{patient.allergies.join(', ') || 'Không ghi nhận'}</strong></div>
                <div className="info-tile"><span>Thuốc đang dùng</span><strong>{patient.medications.join(', ') || 'Không ghi nhận'}</strong></div>
                <div className="info-tile"><span>Khu vực</span><strong>{patient.region ?? 'Chưa cập nhật'}</strong></div>
              </div>
              {Object.keys(patient.lab_values).length > 0 && <div style={{ marginTop: 22 }}><div className="section-heading"><h2>Chỉ số xét nghiệm</h2></div><div className="info-grid">{Object.entries(patient.lab_values).map(([key, value]) => <div className="info-tile" key={key}><span>{key}</span><strong>{value}</strong></div>)}</div></div>}
            </div>
          </section>
        )}
      </div>
    </>
  )
}
