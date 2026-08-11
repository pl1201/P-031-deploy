'use client'
import { useEffect, useState } from 'react'
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
  const [patients, setPatients] = useState<PatientProfile[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')

  useEffect(() => {
    const token = getToken()
    if (!token) return
    createApiClient(token).listPatients()
      .then(r => setPatients(r.items))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

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

      </div>
    </>
  )
}
