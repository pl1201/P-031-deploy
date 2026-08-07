'use client'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { getSession, clearSession } from '@/lib/auth'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

const NAV = [
  { href: '/patient', label: 'Thực đơn của tôi', icon: '◉', exact: true },
]

export default function PatientLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    const session = getSession()
    if (!session || session.role !== 'patient') {
      router.replace('/login')
    }
  }, [router])

  const handleLogout = () => {
    clearSession()
    router.push('/login')
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-icon">V</div>
          <div>
            <div className="brand-name">VNUTRICARE</div>
            <div className="brand-sub">Bệnh nhân</div>
          </div>
        </div>
        <nav>
          {NAV.map(item => (
            <Link
              key={item.href}
              href={item.href}
              className={`nav-item${pathname === item.href ? ' active' : ''}`}
            >
              <span style={{ fontSize: 17, width: 22, textAlign: 'center' }}>{item.icon}</span>
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="user-avatar">BN</div>
          <div>
            <div className="user-name">Bệnh nhân</div>
            <div className="user-role">Bệnh nhân ĐTĐ2</div>
          </div>
          <button onClick={handleLogout} style={{ color: 'rgba(255,255,255,.4)', fontSize: 13 }} title="Đăng xuất">⏏</button>
        </div>
        <div style={{ marginTop: 16, padding: 12, background: 'rgba(0,0,0,.1)', borderRadius: 'var(--r-md)' }}>
          <p className="disclaimer" style={{ fontSize: 10, background: 'transparent', border: 'none', color: 'rgba(255,255,255,.45)' }}>
            Dữ liệu 100% mô phỏng. Không thay thế bác sĩ.
          </p>
        </div>
      </aside>
      <main className="main-content">{children}</main>
    </div>
  )
}
