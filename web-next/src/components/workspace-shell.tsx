'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useEffect, useMemo, useState } from 'react'
import { Icon, LeafMark } from '@/components/brand-artwork'
import { createApiClient, type Role } from '@/lib/api'
import { clearSession, getSession, getToken } from '@/lib/auth'
import { REVIEW_QUEUE_CHANGED_EVENT, type ReviewQueueChangedDetail } from '@/lib/review-queue'
import styles from './workspace-shell.module.css'

type WorkspaceRole = 'patient' | 'dietitian'

type NavItem = {
  href: string
  label: string
  icon: string
  exact?: boolean
  badge?: 'pending'
  adminOnly?: boolean
}

const PATIENT_NAV: NavItem[] = [
  { href: '/patient', label: 'Hôm nay', icon: 'home', exact: true },
  { href: '/patient/diary', label: 'Món đã ăn', icon: 'diary' },
  { href: '/patient/weekly', label: 'Tuần của tôi', icon: 'trend' },
  { href: '/patient/profile', label: 'Hồ sơ', icon: 'user' },
]

const DIETITIAN_NAV: NavItem[] = [
  { href: '/dietitian', label: 'Tổng quan hôm nay', icon: 'home', exact: true },
  { href: '/dietitian/patients', label: 'Bệnh nhân', icon: 'user' },
  { href: '/dietitian/reviews', label: 'Duyệt thực đơn', icon: 'clipboard', badge: 'pending' },
  { href: '/dietitian/meal-plans/new', label: 'Tạo thực đơn', icon: 'sparkles' },
  { href: '/dietitian/food-logs', label: 'Đối chiếu nhật ký', icon: 'trend' },
  { href: '/dietitian/analytics', label: 'Thống kê chuyên môn', icon: 'chart' },
  { href: '/eval', label: 'Đánh giá hệ thống', icon: 'shield', adminOnly: true },
]

export function WorkspaceShell({ role, children }: { role: WorkspaceRole; children: React.ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()
  const [open, setOpen] = useState(false)
  const [sessionRole] = useState<Role | null>(() => getSession()?.role ?? null)
  const [pending, setPending] = useState<number | null>(null)

  useEffect(() => {
    const session = getSession()
    const accepted = role === 'patient'
      ? session?.role === 'patient'
      : session?.role === 'dietitian' || session?.role === 'admin'
    if (!session || !accepted) {
      const returnTo = encodeURIComponent(pathname || (role === 'patient' ? '/patient' : '/dietitian'))
      router.replace(`/login?returnTo=${returnTo}`)
      return
    }
  }, [pathname, role, router])

  useEffect(() => {
    if (role !== 'dietitian') return
    const refresh = () => {
      const token = getToken()
      if (!token) return
      void createApiClient(token).listPendingReviews()
        .then(rows => setPending(rows.length))
        .catch(() => setPending(null))
    }
    const sync = (event: Event) => {
      const count = (event as CustomEvent<ReviewQueueChangedDetail>).detail?.count
      if (typeof count === 'number') setPending(count)
      else refresh()
    }
    refresh()
    window.addEventListener(REVIEW_QUEUE_CHANGED_EVENT, sync)
    return () => window.removeEventListener(REVIEW_QUEUE_CHANGED_EVENT, sync)
  }, [role])

  const nav = useMemo(() => {
    const source = role === 'patient' ? PATIENT_NAV : DIETITIAN_NAV
    return source.filter(item => !item.adminOnly || sessionRole === 'admin')
  }, [role, sessionRole])

  const logout = () => {
    clearSession()
    router.push('/login')
  }

  const openTour = () => window.dispatchEvent(new Event('vn:open-tour'))

  return (
    <div className={styles.shell} data-role={role}>
      <aside className={`${styles.sidebar}${open ? ` ${styles.open}` : ''}`}>
        <div className={styles.brand}>
          <LeafMark />
          <div>
            <strong>VNUTRICARE</strong>
            <small>{role === 'patient' ? 'Không gian chăm sóc' : 'Clinical nutrition intelligence'}</small>
          </div>
          <button type="button" className={styles.close} onClick={() => setOpen(false)} aria-label="Đóng menu">
            <Icon name="close" />
          </button>
        </div>

        <nav className={styles.nav} aria-label={role === 'patient' ? 'Điều hướng người bệnh' : 'Điều hướng chuyên gia'}>
          {nav.map(item => {
            const active = item.exact ? pathname === item.href : pathname.startsWith(item.href)
            return (
              <Link key={item.href} href={item.href} className={active ? styles.active : undefined} onClick={() => setOpen(false)}>
                <Icon name={item.icon} />
                <span>{item.label}</span>
                {item.badge === 'pending' && pending !== null && <b>{pending}</b>}
              </Link>
            )
          })}
        </nav>

        <div className={styles.help}>
          <Icon name="info" />
          <div><strong>Mới dùng VNutriCare?</strong><small>Xem hướng dẫn nhanh theo vai trò.</small></div>
          <button type="button" onClick={openTour}>Mở</button>
        </div>

        <div className={styles.account}>
          <span>{role === 'patient' ? 'BN' : 'CG'}</span>
          <div>
            <strong>{role === 'patient' ? 'Tài khoản người bệnh' : 'Tài khoản chuyên gia'}</strong>
            <small>{role === 'patient' ? 'Người bệnh' : 'Chuyên gia dinh dưỡng'}</small>
          </div>
          <button type="button" onClick={logout} aria-label="Đăng xuất" title="Đăng xuất"><Icon name="logout" /></button>
        </div>
      </aside>

      <main className={styles.main}>
        <button type="button" className={styles.mobileMenu} onClick={() => setOpen(true)} aria-label="Mở menu">
          <Icon name="menu" />
        </button>
        {children}
      </main>
      {open && <button type="button" className={styles.overlay} onClick={() => setOpen(false)} aria-label="Đóng menu" />}
    </div>
  )
}
