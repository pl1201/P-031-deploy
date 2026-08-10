'use client'

import { useEffect, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import Link from 'next/link'
import { createApiClient } from '@/lib/api'
import { getSession, getToken, clearSession } from '@/lib/auth'

type IconName = 'overview' | 'patients' | 'plans' | 'audit' | 'quality' | 'search' | 'logout' | 'menu'

function Icon({ name }: { name: IconName }) {
  const paths: Record<IconName, React.ReactNode> = {
    overview: <><rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/></>,
    patients: <><circle cx="9" cy="8" r="3"/><path d="M3.5 20v-2a5.5 5.5 0 0 1 11 0v2M16 4.5a3 3 0 0 1 0 6M17 14a5 5 0 0 1 3.5 4.8V20"/></>,
    plans: <><path d="M7 3h10v4H7zM5 5H4a2 2 0 0 0-2 2v13h20V7a2 2 0 0 0-2-2h-1M7 12h10M7 16h7"/></>,
    audit: <><path d="M12 3a9 9 0 1 0 9 9M12 7v5l3 2"/><path d="m17 4 4-1-1 4"/></>,
    quality: <><path d="M4 19V9M10 19V5M16 19v-7M22 19H2"/></>,
    search: <><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></>,
    logout: <><path d="M10 5H4v14h6M14 8l4 4-4 4M8 12h10"/></>,
    menu: <><path d="M4 7h16M4 12h16M4 17h16"/></>,
  }
  return <svg className="ui-icon" viewBox="0 0 24 24" aria-hidden="true">{paths[name]}</svg>
}

type NavItem = { href: string; label: string; icon: IconName; exact?: boolean; badge?: boolean }
type NavGroup = { label: string; items: NavItem[] }

const NAV: Array<{ href: string; label: string; icon: string; exact?: boolean; badge?: boolean }> = [
  { href: '/dietitian', label: 'Hàng chờ duyệt', icon: '◎', exact: true, badge: true },
  { href: '/dietitian/patients', label: 'Hồ sơ bệnh nhân', icon: '◈' },
  { href: '/dietitian/food-logs', label: 'Món chờ đối chiếu', icon: '✎' },
  { href: '/dietitian/approvals', label: 'Nhật ký phê duyệt', icon: '✓' },
  { href: '/eval', label: 'Báo cáo Eval', icon: '◫' },
]

export default function DietitianLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const [pendingCount, setPendingCount] = useState<number | null>(null)
  const [menuOpen, setMenuOpen] = useState(false)
  const [quickSearch, setQuickSearch] = useState('')

  useEffect(() => {
    const session = getSession()
    if (!session || (session.role !== 'dietitian' && session.role !== 'admin')) {
      router.replace('/login')
      return
    }
    const token = getToken()
    if (token) void createApiClient(token).listPendingReviews().then(items => setPendingCount(items.length)).catch(() => undefined)
  }, [router])

  const handleLogout = () => { clearSession(); router.push('/login') }
  const isActive = (href: string, exact?: boolean) => exact ? pathname === href : pathname.startsWith(href)
  const handleQuickSearch = (event: React.FormEvent) => {
    event.preventDefault()
    const value = quickSearch.trim()
    router.push(value ? `/dietitian/patients?q=${encodeURIComponent(value)}` : '/dietitian/patients')
    setMenuOpen(false)
  }

  return (
    <div className="app-shell clinical-shell">
      <aside className={`sidebar clinical-sidebar${menuOpen ? ' open' : ''}`}>
        <div className="sidebar-brand">
          <div className="brand-icon">V</div>
          <div><div className="brand-name">VNUTRICARE</div><div className="brand-sub">Clinical Nutrition Intelligence</div></div>
          <button className="sidebar-close" onClick={() => setMenuOpen(false)} aria-label="Đóng menu">×</button>
        </div>

        <form className="sidebar-search" onSubmit={handleQuickSearch}>
          <Icon name="search" />
          <input value={quickSearch} onChange={event => setQuickSearch(event.target.value)} placeholder="Tìm hồ sơ nhanh..." aria-label="Tìm hồ sơ nhanh" />
          <kbd>⌘K</kbd>
        </form>

        <nav className="sidebar-nav">
          {NAV_GROUPS.map(group => (
            <div className="nav-group" key={group.label}>
              <div className="nav-label">{group.label}</div>
              {group.items.map(item => {
                const active = isActive(item.href, item.exact)
                return (
                  <Link key={item.href} href={item.href} className={`nav-item${active ? ' active' : ''}`} onClick={() => setMenuOpen(false)}>
                    <span className="nav-icon"><Icon name={item.icon} /></span>
                    <span>{item.label}</span>
                    {item.badge && pendingCount !== null && pendingCount > 0 && <span className="nav-badge">{pendingCount}</span>}
                  </Link>
                )
              })}
            </div>
          ))}
        </nav>

        <div className="sidebar-health">
          <div className="health-orbit"><i /></div>
          <div><strong>Clinical engine online</strong><span>API · Nutrition · Audit</span></div>
          <span className="health-value">99.9%</span>
        </div>

        <div className="sidebar-footer">
          <div className="user-avatar">BC</div>
          <div className="user-copy"><div className="user-name">BS. Chuyên gia</div><div className="user-role">Chuyên gia dinh dưỡng</div></div>
          <button className="logout-button" onClick={handleLogout} title="Đăng xuất" aria-label="Đăng xuất"><Icon name="logout" /></button>
        </div>
      </aside>

      <main className="main-content">
        <button className="mobile-menu-btn" aria-label="Mở menu" onClick={() => setMenuOpen(true)}><Icon name="menu" /></button>
        {children}
      </main>
      {menuOpen && <button className="mobile-overlay" aria-label="Đóng menu" onClick={() => setMenuOpen(false)} />}
    </div>
  )
}
