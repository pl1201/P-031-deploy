'use client'
import { useEffect, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import Link from 'next/link'
import { createApiClient } from '@/lib/api'
import { getSession, getToken, clearSession } from '@/lib/auth'

const NAV: Array<{ href: string; label: string; icon: string; exact?: boolean; badge?: boolean }> = [
  { href: '/dietitian', label: 'Trung tâm duyệt', icon: '◉', exact: true, badge: true },
  { href: '/dietitian/patients', label: 'Hồ sơ bệnh nhân', icon: '◇' },
  { href: '/dietitian/reviews', label: 'Nhật ký phê duyệt', icon: '✓' },
  { href: '/dietitian/eval', label: 'Chất lượng hệ thống', icon: '▥' },
]

export default function DietitianLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const [pendingCount, setPendingCount] = useState<number | null>(null)
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    const session = getSession()
    if (!session || (session.role !== 'dietitian' && session.role !== 'admin')) {
      router.replace('/login')
      return
    }
    const token = getToken()
    if (token) {
      void createApiClient(token).listPendingReviews().then(items => setPendingCount(items.length)).catch(() => undefined)
    }
  }, [router])

  const handleLogout = () => {
    clearSession()
    router.push('/login')
  }

  const isActive = (href: string, exact?: boolean) =>
    exact ? pathname === href : pathname.startsWith(href)

  return (
    <div className="app-shell">
      {/* Sidebar */}
      <aside className={`sidebar${menuOpen ? ' open' : ''}`}>
        <div className="sidebar-brand">
          <div className="brand-icon">V</div>
          <div>
            <div className="brand-name">VNUTRICARE</div>
            <div className="brand-sub">Clinical Nutrition Intelligence</div>
          </div>
        </div>

        <nav>
          <div className="nav-label">Clinical workspace</div>
          {NAV.map(item => (
            <Link
              key={item.href}
              href={item.href}
              className={`nav-item${isActive(item.href, item.exact) ? ' active' : ''}`}
              onClick={() => setMenuOpen(false)}
            >
              <span style={{ fontSize: 17, width: 22, textAlign: 'center', opacity: isActive(item.href, item.exact) ? 1 : .6 }}>
                {item.icon}
              </span>
              {item.label}
              {item.badge && pendingCount !== null && pendingCount > 0 && (
                <span className="nav-badge">{pendingCount}</span>
              )}
            </Link>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="user-avatar">BC</div>
          <div>
            <div className="user-name">BS. Chuyên gia</div>
            <div className="user-role">Chuyên gia dinh dưỡng</div>
          </div>
          <button
            onClick={handleLogout}
            style={{ color: 'rgba(255,255,255,.4)', fontSize: 13, padding: '6px 8px', borderRadius: 'var(--r-sm)' }}
            title="Đăng xuất"
          >
            ⏏
          </button>
        </div>

        <div style={{ marginTop: 16, padding: '12px', display: 'flex', alignItems: 'center', gap: 8, background: 'rgba(0,0,0,.1)', borderRadius: 'var(--r-md)' }}>
          <div className="status-dot" />
          <div>
            <div style={{ fontSize: 11, fontWeight: 600 }}>Clinical engine online</div>
            <div style={{ fontSize: 9, color: 'rgba(255,255,255,.5)', marginTop: 2 }}>API · Nutrition · Audit</div>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="main-content">
        <button className="mobile-menu-btn" aria-label="Mở menu" onClick={() => setMenuOpen(true)}>☰</button>
        {children}
      </main>

      {/* Mobile overlay */}
      {menuOpen && (
        <div
          style={{ position: 'fixed', inset: 0, zIndex: 29, background: 'rgba(0,0,0,.4)' }}
          onClick={() => setMenuOpen(false)}
        />
      )}
    </div>
  )
}
