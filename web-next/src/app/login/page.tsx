'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { createApiClient, ApiError } from '@/lib/api'
import { saveSession, redirectByRole } from '@/lib/auth'
import styles from './login.module.css'

const DEMO_ACCOUNTS = [
  {
    role: 'Chuyên gia dinh dưỡng',
    description: 'Lập và duyệt thực đơn',
    email: 'dietitian1@nutricare.demo',
    initials: 'CG',
  },
  {
    role: 'Bệnh nhân',
    description: 'Theo dõi kế hoạch cá nhân',
    email: 'patient1@nutricare.demo',
    initials: 'BN',
  },
] as const

function MailIcon() {
  return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6.5h16v11H4zM4 7l8 6 8-6" /></svg>
}

function LockIcon() {
  return <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="10" width="14" height="10" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></svg>
}

function ClinicalPreview() {
  return (
    <div className={styles.preview} aria-hidden="true">
      <div className={styles.previewGlow} />
      <div className={styles.previewTopbar}>
        <div className={styles.previewBrand}><span>V</span> VNUTRICARE</div>
        <div className={styles.previewStatus}><i /> Clinical engine online</div>
      </div>
      <div className={styles.previewBody}>
        <div className={styles.previewHeading}>
          <span>Hồ sơ đang theo dõi</span>
          <strong>Nguyễn Minh Anh</strong>
          <small>ĐTĐ type 2 · Kế hoạch 08/08</small>
        </div>
        <div className={styles.nutritionDial}>
          <div><strong>92</strong><span>% mục tiêu</span></div>
        </div>
        <div className={styles.macroGrid}>
          <div><i className={styles.carb} /><span>Carb</span><strong>238 g</strong></div>
          <div><i className={styles.protein} /><span>Protein</span><strong>112 g</strong></div>
          <div><i className={styles.fiber} /><span>Chất xơ</span><strong>31 g</strong></div>
        </div>
        <div className={styles.approvalStrip}>
          <span>✓</span>
          <div><strong>Sẵn sàng chuyên gia duyệt</strong><small>Không phát hiện vi phạm cứng</small></div>
        </div>
      </div>
    </div>
  )
}

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [remember, setRemember] = useState(true)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const selectDemo = (account: (typeof DEMO_ACCOUNTS)[number]) => {
    setEmail(account.email)
    setPassword('Demo1234')
    setError('')
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      const session = await createApiClient().login(email, password)
      saveSession(session)
      router.push(redirectByRole(session.role))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể đăng nhập. Vui lòng kiểm tra kết nối và thử lại.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className={styles.page}>
      <div className={styles.ambientOne} />
      <div className={styles.ambientTwo} />

      <header className={styles.header}>
        <div className={styles.logoMark}>V</div>
        <div className={styles.logoText}>
          <strong>VNUTRICARE</strong>
          <span>Clinical Nutrition Intelligence</span>
        </div>
        <div className={styles.systemBadge}><i /> Hệ thống vận hành bình thường</div>
      </header>

      <section className={styles.shell}>
        <div className={styles.story}>
          <div className={styles.eyebrow}><span>✦</span> AI hỗ trợ quyết định lâm sàng</div>
          <h1>Dinh dưỡng cá thể hóa.<br /><em>Quyết định có căn cứ.</em></h1>
          <p className={styles.lead}>
            Biến hồ sơ lâm sàng thành kế hoạch dinh dưỡng có thể kiểm chứng — từ tính toán, rà soát đến phê duyệt chuyên gia.
          </p>
          <ClinicalPreview />
          <div className={styles.trustRow}>
            <span><i>01</i>Dữ liệu có nguồn</span>
            <span><i>02</i>Tính toán phía server</span>
            <span><i>03</i>Chuyên gia phê duyệt</span>
          </div>
        </div>

        <div className={styles.authColumn}>
          <div className={styles.authCard}>
            <div className={styles.authIntro}>
              <span className={styles.authKicker}>Đăng nhập hệ thống</span>
              <h2>Chào mừng trở lại</h2>
              <p>Tiếp tục không gian dinh dưỡng của bạn.</p>
            </div>

            <form onSubmit={handleSubmit} className={styles.form}>
              <label>
                <span>Email</span>
                <div className={styles.field}>
                  <MailIcon />
                  <input type="email" value={email} onChange={event => setEmail(event.target.value)} placeholder="name@nutricare.vn" autoComplete="username" required autoFocus />
                </div>
              </label>

              <label>
                <span>Mật khẩu</span>
                <div className={styles.field}>
                  <LockIcon />
                  <input type={showPassword ? 'text' : 'password'} value={password} onChange={event => setPassword(event.target.value)} placeholder="Nhập mật khẩu" autoComplete="current-password" required />
                  <button type="button" className={styles.passwordToggle} onClick={() => setShowPassword(value => !value)} aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}>
                    {showPassword ? 'Ẩn' : 'Hiện'}
                  </button>
                </div>
              </label>

              <div className={styles.formOptions}>
                <label className={styles.remember}>
                  <input type="checkbox" checked={remember} onChange={event => setRemember(event.target.checked)} />
                  <span>Ghi nhớ đăng nhập</span>
                </label>
                <button type="button" className={styles.textButton} onClick={() => setError('Vui lòng liên hệ quản trị viên để được cấp lại mật khẩu.')}>Quên mật khẩu?</button>
              </div>

              {error && <div className={styles.error} role="alert"><span>!</span>{error}</div>}

              <button type="submit" className={styles.submit} disabled={loading}>
                {loading ? <><span className={styles.spinner} /> Đang kết nối...</> : <>Đăng nhập <span>→</span></>}
              </button>
            </form>

            <div className={styles.divider}><span>Truy cập nhanh bản demo</span></div>
            <div className={styles.demoGrid}>
              {DEMO_ACCOUNTS.map(account => (
                <button type="button" key={account.email} onClick={() => selectDemo(account)} className={`${styles.demoAccount} ${email === account.email ? styles.demoActive : ''}`}>
                  <span className={styles.demoAvatar}>{account.initials}</span>
                  <span className={styles.demoCopy}><strong>{account.role}</strong><small>{account.description}</small></span>
                  <span className={styles.demoArrow}>↗</span>
                </button>
              ))}
            </div>

            <p className={styles.demoNote}><span>ⓘ</span> Bản demo sử dụng dữ liệu mô phỏng và không thay thế tư vấn y khoa.</p>
          </div>
        </div>
      </section>

      <footer className={styles.footer}>
        <span>© 2026 VNUTRICARE · Clinical Nutrition AI</span>
        <span>Dữ liệu mô phỏng · Quy trình có chuyên gia giám sát</span>
      </footer>
    </main>
  )
}
