'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { createApiClient, type PatientProfile } from '@/lib/api'
import { getToken } from '@/lib/auth'

const CONDITION_LABELS: Record<string, string> = {
  T2DM: 'ĐTĐ type 2',
  HTN: 'Tăng huyết áp',
  CKD: 'Bệnh thận mạn',
  GOUT: 'Gout',
}

const ACTIVITY_LABELS: Record<string, string> = {
  light: 'Nhẹ',
  moderate: 'Trung bình',
  heavy: 'Nặng',
  very_heavy: 'Rất nặng',
}

export default function PatientsPage() {
  const router = useRouter()
  const [patients, setPatients] = useState<PatientProfile[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState<string | null>(null)
  const [toast, setToast] = useState('')
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')

  const showToast = (msg: string) => {
    setToast(msg)
    setTimeout(() => setToast(''), 3000)
  }

  useEffect(() => {
    const token = getToken()
    if (!token) return
    createApiClient(token).listPatients()
      .then(r => setPatients(r.items))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const handleGeneratePlan = async (patient: PatientProfile) => {
    const token = getToken()
    if (!token) return
    setGenerating(patient.id)
    try {
      const result = await createApiClient(token).createMealPlan(patient.id)
      showToast(`Đang sinh thực đơn cho ${patient.id.slice(0, 8)}... (plan: ${result.plan_id.slice(0, 8)})`)
      // Poll cho đến khi xong
      let attempts = 0
      let failures = 0
      const poll = setInterval(async () => {
        attempts++
        try {
          const plan = await createApiClient(token).getMealPlan(result.plan_id)
          if (plan.status !== 'drafting') {
            clearInterval(poll)
            setGenerating(null)
            showToast(`Thực đơn sẵn sàng — trạng thái: ${plan.status}`)
            if (plan.status === 'pending_review') {
              router.push(`/dietitian/reviews/${plan.id}`)
            }
          }
        } catch { failures++; if (failures >= 3) { clearInterval(poll); setGenerating(null); showToast('Không thể kiểm tra trạng thái thực đơn.') } }
        if (attempts >= 30) { clearInterval(poll); setGenerating(null); showToast('Sinh thực đơn quá thời gian chờ.') }
      }, 2000)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Lỗi không xác định'
      showToast(`Lỗi: ${msg}`)
      setGenerating(null)
    }
  }

  const bmi = (p: PatientProfile) => (p.weight_kg / (p.height_cm / 100) ** 2).toFixed(1)

  return (
    <>
      <div className="topbar">
        <div>
          <p className="page-kicker">Patient intelligence</p>
          <h1 className="page-title">Hồ sơ bệnh nhân</h1>
        </div>
        <div className="topbar-actions">
          <span className="synthetic-label">DỮ LIỆU MÔ PHỎNG</span>
        </div>
      </div>

      <div className="page-body">
        <div className="page-heading-row" style={{ marginBottom: 18 }}>
          <div>
            <h2 style={{ fontFamily: 'var(--f-serif)', fontSize: 26 }}>Danh sách đang theo dõi</h2>
            <p className="page-subtitle">Mở hồ sơ để xem toàn bộ lịch sử thực đơn, chỉ số và quyết định chuyên gia.</p>
          </div>
          <span className="badge badge-approved">{patients.length} hồ sơ</span>
        </div>
        <div className="toolbar" style={{ marginBottom: 18 }}>
          <input className="search-box" aria-label="Tìm hồ sơ hoặc bệnh lý" value={query} onChange={e => setQuery(e.target.value)} placeholder="Tìm mã hồ sơ hoặc bệnh lý…" />
        </div>
        {loading ? (
          <div style={{ display: 'grid', placeItems: 'center', height: '50vh' }}>
            <span className="spinner" style={{ width: 32, height: 32, color: 'var(--c-green)' }} />
          </div>
        ) : error ? (
          <div className="safety-strip safety-strip-error">{error}</div>
        ) : (
          <div className="patient-list">
            {patients.filter(p => `${p.id} ${p.conditions.map(c => c.code).join(' ')}`.toLowerCase().includes(query.toLowerCase())).map(p => (
              <div key={p.id} className="card patient-card">
                <div className="patient-card-grid" style={{ display: 'grid', gridTemplateColumns: '56px 1fr auto', alignItems: 'center', gap: 20, padding: '20px 24px' }}>
                  {/* Avatar */}
                  <div className="patient-avatar-blue">
                    {p.sex === 'male' ? 'N' : 'Nữ'}
                  </div>

                  {/* Info */}
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                      <span style={{ fontFamily: 'var(--f-mono)', fontSize: 12, color: 'var(--c-muted)' }}>
                        #{p.id.slice(0, 8)}
                      </span>
                      {p.conditions.map(c => (
                        <span key={c.code} className="badge badge-pending">
                          {CONDITION_LABELS[c.code] ?? c.code}
                          {c.stage && ` ${c.stage}`}
                        </span>
                      ))}
                      {p.allergies.length > 0 && (
                        <span className="badge badge-hard" title={p.allergies.join(', ')}>
                          ⚠ Dị ứng
                        </span>
                      )}
                    </div>
                    <div style={{ display: 'flex', gap: 20, fontSize: 13 }}>
                      <span>{p.sex === 'male' ? 'Nam' : 'Nữ'} · {p.age} tuổi</span>
                      <span>{p.height_cm} cm · {p.weight_kg} kg</span>
                      <span>BMI {bmi(p)}</span>
                      <span>Hoạt động: {ACTIVITY_LABELS[p.activity_level] ?? p.activity_level}</span>
                      {p.region && <span>Vùng: {p.region === 'north' ? 'Bắc' : p.region === 'central' ? 'Trung' : 'Nam'}</span>}
                    </div>
                    {p.medications.length > 0 && (
                      <div style={{ marginTop: 6, fontSize: 12, color: 'var(--c-muted)' }}>
                        💊 {p.medications.join(', ')}
                      </div>
                    )}
                  </div>

                  {/* Action */}
                  <div className="patient-card-actions">
                    <Link href={`/dietitian/patients/${p.id}`} className="btn btn-secondary">Xem hồ sơ</Link>
                    <button
                      className="btn btn-primary"
                      onClick={() => handleGeneratePlan(p)}
                      disabled={generating !== null}
                    >
                      {generating === p.id
                        ? <><span className="spinner" style={{ width: 14, height: 14 }} /> Đang sinh...</>
                        : '+ Sinh thực đơn'
                      }
                    </button>
                  </div>
                </div>
              </div>
            ))}

            {patients.length === 0 && (
              <div className="empty-state">
                <div className="empty-icon">◈</div>
                <div className="empty-title">Chưa có hồ sơ bệnh nhân</div>
                <div className="empty-desc">Chạy <code>make seed-demo-users</code> để tạo dữ liệu demo.</div>
              </div>
            )}
          </div>
        )}

        {toast && (
          <div className="toast-wrap">
            <div className="toast toast-success">{toast}</div>
          </div>
        )}
      </div>
    </>
  )
}
