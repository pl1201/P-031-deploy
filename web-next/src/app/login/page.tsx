'use client'
import type { Metadata } from 'next'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { createApiClient, ApiError } from '@/lib/api'
import { saveSession, redirectByRole } from '@/lib/auth'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const session = await createApiClient().login(email, password)
      saveSession(session)
      router.push(redirectByRole(session.role))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể đăng nhập. Kiểm tra lại thông tin.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--c-bg)',
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
    }}>
      {/* Left — branding */}
      <div style={{
        background: 'var(--c-green)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        padding: '52px 56px',
        color: '#e8f0eb',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div className="brand-icon" style={{ width: 44, height: 44, fontSize: 26 }}>V</div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 18, letterSpacing: '.02em' }}>VNUTRICARE</div>
            <div style={{ fontSize: 11, opacity: .5, letterSpacing: '.1em', textTransform: 'uppercase', marginTop: 2 }}>Clinical Nutrition AI</div>
          </div>
        </div>

        <div>
          <p style={{ fontSize: 11, opacity: .45, letterSpacing: '.1em', textTransform: 'uppercase', marginBottom: 16 }}>
            VMEC-10 · AI20K Cohort 3 · P-031
          </p>
          <h1 style={{
            fontFamily: 'var(--f-serif)',
            fontSize: 'clamp(40px,5vw,60px)',
            fontWeight: 400,
            lineHeight: .95,
            letterSpacing: 0,
            marginBottom: 20,
          }}>
            Tư vấn<br />
            <em style={{ color: 'var(--c-lime)', fontStyle: 'italic' }}>dinh dưỡng</em><br />
            lâm sàng
          </h1>
          <p style={{ fontSize: 14, lineHeight: 1.7, opacity: .7, maxWidth: 380 }}>
            AI Agent hỗ trợ chuyên gia lập và duyệt thực đơn cá thể hoá
            cho bệnh nhân đái tháo đường type 2 — mọi con số có nguồn,
            mọi thực đơn qua chuyên gia duyệt.
          </p>
        </div>

        <div style={{ fontSize: 12, opacity: .35 }}>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 10 }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--c-lime)' }} />
            LLM chỉ chọn món — Python tính số (RULE-1)
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 10 }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--c-lime)' }} />
            Mọi con số dinh dưỡng có nguồn truy vết (RULE-2)
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--c-lime)' }} />
            Chuyên gia duyệt trước khi đến bệnh nhân (RULE-3)
          </div>
        </div>
      </div>

      {/* Right — form */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        padding: '52px 72px',
      }}>
        <div style={{ maxWidth: 400, width: '100%' }}>
          <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: '.12em', textTransform: 'uppercase', color: 'var(--c-green2)', marginBottom: 8 }}>
            ĐĂNG NHẬP HỆ THỐNG
          </p>
          <h2 style={{
            fontFamily: 'var(--f-serif)',
            fontSize: 32, fontWeight: 400,
            letterSpacing: 0,
            marginBottom: 32,
          }}>
            Xin chào,<br />
            <em style={{ color: 'var(--c-green)', fontStyle: 'italic' }}>chuyên gia.</em>
          </h2>

          <form onSubmit={handleSubmit} style={{ display: 'grid', gap: 16 }}>
            <div className="form-group">
              <label className="form-label" htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                className="form-input"
                placeholder="dietitian1@nutricare.demo"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                autoFocus
              />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="password">Mật khẩu</label>
              <input
                id="password"
                type="password"
                className="form-input"
                placeholder="••••••••"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
              />
            </div>

            {error && (
              <div style={{
                padding: '10px 14px',
                borderRadius: 'var(--r-md)',
                background: '#fde8e8',
                border: '1px solid #f5c6c6',
                color: 'var(--c-red)',
                fontSize: 13,
              }}>
                {error}
              </div>
            )}

            <button type="submit" className="btn btn-primary btn-lg" disabled={loading} style={{ marginTop: 4 }}>
              {loading ? <><span className="spinner" style={{ width: 16, height: 16 }} /> Đang đăng nhập...</> : 'Đăng nhập →'}
            </button>
          </form>

          <div style={{ marginTop: 32, padding: 20, background: 'var(--c-surface)', borderRadius: 'var(--r-md)', border: '1px solid var(--c-border)' }}>
            <p style={{ fontSize: 11, fontWeight: 700, color: 'var(--c-muted)', marginBottom: 10, letterSpacing: '.08em', textTransform: 'uppercase' }}>
              Tài khoản demo (mật khẩu: Demo1234)
            </p>
            {[
              ['dietitian1@nutricare.demo', 'Chuyên gia dinh dưỡng'],
              ['patient1@nutricare.demo', 'Bệnh nhân ĐTĐ2'],
            ].map(([em, label]) => (
              <button
                key={em}
                type="button"
                onClick={() => { setEmail(em); setPassword('Demo1234') }}
                style={{
                  display: 'block', width: '100%',
                  padding: '8px 12px', marginBottom: 6,
                  textAlign: 'left',
                  borderRadius: 'var(--r-sm)',
                  border: '1px solid var(--c-border)',
                  background: 'transparent',
                  fontSize: 12,
                  cursor: 'pointer',
                  transition: 'background .15s',
                }}
                onMouseOver={e => (e.currentTarget.style.background = 'rgba(0,0,0,.03)')}
                onMouseOut={e => (e.currentTarget.style.background = 'transparent')}
              >
                <span style={{ fontWeight: 600 }}>{em}</span>
                <span style={{ color: 'var(--c-muted)', marginLeft: 8 }}>{label}</span>
              </button>
            ))}
          </div>

          <p className="disclaimer" style={{ marginTop: 20 }}>
            ⚕️ <strong>Dữ liệu 100% mô phỏng.</strong> Hệ thống này không thay thế bác sĩ hoặc chuyên gia dinh dưỡng. Mọi thực đơn cần được chuyên gia duyệt trước khi đến tay bệnh nhân.
          </p>
        </div>
      </div>

      <style>{`
        @media (max-width: 768px) {
          div[style*="gridTemplateColumns: 1fr 1fr"] {
            grid-template-columns: 1fr !important;
          }
          div[style*="52px 56px"] { display: none !important; }
          div[style*="52px 72px"] { padding: 40px 24px !important; }
        }
      `}</style>
    </div>
  )
}
