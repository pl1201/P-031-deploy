'use client'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { getSession, clearSession } from '@/lib/auth'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { LeafMark } from '@/components/brand-artwork'

const NAV = [
  { href: '/patient', label: 'Tổng quan', icon: '▦', exact: true },
  { href: '/patient', label: 'Thực đơn', icon: '⌑', exact: false },
  { href: '/patient/diary', label: 'Nhật ký ăn uống', icon: '▣', exact: true },
  { href: '/patient', label: 'Tiến độ', icon: '↗', exact: false },
  { href: '/patient', label: 'Tin nhắn', icon: '◌', exact: false },
  { href: '/patient', label: 'Tài khoản', icon: '♙', exact: false },
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
          <LeafMark />
          <div className="brand-name">VNUTRICARE</div>
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
            <div className="user-name">Tài khoản người bệnh</div>
            <div className="user-role">Người bệnh</div>
          </div>
          <button onClick={handleLogout} style={{ color: 'rgba(255,255,255,.4)', fontSize: 13 }} title="Đăng xuất">⏏</button>
        </div>
      </aside>
      <main className="main-content">{children}</main>
    </div>
  )
}
