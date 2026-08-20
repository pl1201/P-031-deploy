'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useEffect, useMemo, useState } from 'react'
import { Icon, LeafMark } from '@/components/brand-artwork'
import { useAssistant } from '@/components/experience-tools'
import { NotificationBell } from '@/components/notification-bell'
import { createApiClient, type Role } from '@/lib/api'
import { clearSession, getSession, getToken } from '@/lib/auth'
import { REVIEW_QUEUE_CHANGED_EVENT, type ReviewQueueChangedDetail } from '@/lib/review-queue'

type WorkspaceRole = 'patient' | 'dietitian'

type NavItem = {
  href: string
  label: string
  /** Nhãn ngắn cho thanh tab dưới cùng (mobile) — mặc định dùng label nếu không set. */
  tabLabel?: string
  icon: string
  exact?: boolean
  badge?: 'pending'
  adminOnly?: boolean
}

const PATIENT_NAV: NavItem[] = [
  { href: '/patient', label: 'Hôm nay', icon: 'home', exact: true },
  { href: '/patient/diary', label: 'Báo cáo dinh dưỡng', tabLabel: 'Báo cáo', icon: 'diary' },
  { href: '/patient/weekly', label: 'Tuần của tôi', tabLabel: 'Tuần', icon: 'trend' },
  { href: '/patient/weight', label: 'Cân nặng', icon: 'chart' },
  { href: '/patient/activity', label: 'Thiết bị sức khỏe', tabLabel: 'Thiết bị', icon: 'trend' },
  { href: '/patient/profile', label: 'Hồ sơ', icon: 'user' },
]

const DIETITIAN_NAV: NavItem[] = [
  { href: '/dietitian', label: 'Tổng quan hôm nay', tabLabel: 'Tổng quan', icon: 'home', exact: true },
  { href: '/dietitian/patients', label: 'Bệnh nhân', icon: 'user' },
  { href: '/dietitian/reviews', label: 'Duyệt thực đơn', tabLabel: 'Duyệt', icon: 'clipboard', badge: 'pending' },
  { href: '/dietitian/meal-plans/new', label: 'Tạo thực đơn', tabLabel: 'Tạo mới', icon: 'sparkles' },
  { href: '/dietitian/food-logs', label: 'Đối chiếu nhật ký', tabLabel: 'Nhật ký', icon: 'trend' },
  { href: '/dietitian/analytics', label: 'Thống kê chuyên môn', tabLabel: 'Thống kê', icon: 'chart' },
  { href: '/eval', label: 'Đánh giá hệ thống', icon: 'shield', adminOnly: true },
]

/** Chỉ đổi nhãn hiển thị VI/EN — chưa có hạ tầng i18n dịch nội dung, đây là
 * control UI theo đúng yêu cầu tham chiếu, không dịch phần còn lại của app. */
function LanguageToggle() {
  // Giá trị khởi tạo PHẢI giống nhau ở server và client (mặc định 'vi') — đọc
  // localStorage khác nhau giữa 2 bên gây hydration mismatch, xem pattern an
  // toàn tương tự ở AssistantProvider (experience-tools.tsx theme init).
  const [lang, setLang] = useState<'vi' | 'en'>('vi')
  useEffect(() => {
    const timer = window.setTimeout(() => {
      if (window.localStorage.getItem('vnutricare_lang') === 'en') setLang('en')
    }, 0)
    return () => window.clearTimeout(timer)
  }, [])
  const choose = (value: 'vi' | 'en') => {
    setLang(value)
    window.localStorage.setItem('vnutricare_lang', value)
  }
  return (
    <div className="flex items-center gap-0.5 rounded-full border border-[var(--c-border)] bg-[var(--c-surface)] p-[3px]" role="group" aria-label="Ngôn ngữ">
      <button type="button" onClick={() => choose('vi')} className={`rounded-full px-2.5 py-1 text-sm font-semibold ${lang === 'vi' ? 'bg-[var(--c-card)] text-[var(--c-ink)] shadow-[var(--shadow-sm)]' : 'text-[var(--c-subtle)]'}`}>VI</button>
      <button type="button" onClick={() => choose('en')} className={`rounded-full px-2.5 py-1 text-sm font-semibold ${lang === 'en' ? 'bg-[var(--c-card)] text-[var(--c-ink)] shadow-[var(--shadow-sm)]' : 'text-[var(--c-subtle)]'}`}>EN</button>
    </div>
  )
}

/** Cặp Sáng/Tối dạng pill — dùng lại state theme thật từ AssistantProvider
 * (useAssistant), chỉ đổi cách hiển thị so với ThemeToggleButton (icon đơn). */
function ThemeTogglePill() {
  const { theme, toggleTheme } = useAssistant()
  return (
    <div className="flex items-center gap-0.5 rounded-full border border-[var(--c-border)] bg-[var(--c-surface)] p-[3px]" role="group" aria-label="Giao diện sáng/tối">
      <button type="button" onClick={() => theme !== 'light' && toggleTheme()} className={`flex items-center gap-1.5 rounded-full px-2.5 py-1 text-sm font-semibold ${theme === 'light' ? 'bg-[var(--c-card)] text-[var(--c-ink)] shadow-[var(--shadow-sm)]' : 'text-[var(--c-subtle)]'}`}><Icon name="sun" className="w-[13px]" />Sáng</button>
      <button type="button" onClick={() => theme !== 'dark' && toggleTheme()} className={`flex items-center gap-1.5 rounded-full px-2.5 py-1 text-sm font-semibold ${theme === 'dark' ? 'bg-[var(--c-card)] text-[var(--c-ink)] shadow-[var(--shadow-sm)]' : 'text-[var(--c-subtle)]'}`}><Icon name="moon" className="w-[13px]" />Tối</button>
    </div>
  )
}

export function WorkspaceShell({ role, children }: { role: WorkspaceRole; children: React.ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()
  const [open, setOpen] = useState(false)
  const [sessionRole] = useState<Role | null>(() => getSession()?.role ?? null)
  const [pending, setPending] = useState<number | null>(null)
  const { setOpen: setAssistantOpen } = useAssistant()

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
    // Bệnh nhân lần đầu đăng nhập (chưa hoàn tất khảo sát intro) bị chặn vào mọi
    // trang khác cho tới khi qua /patient/onboarding — không áp cho chuyên gia
    // (tài khoản do đội vận hành tạo sẵn, không cần khảo sát này).
    if (role === 'patient' && pathname !== '/patient/onboarding') {
      const token = getToken()
      if (token) {
        void createApiClient(token).getMeStatus().then(status => {
          if (!status.onboarding_completed_at) router.replace('/patient/onboarding')
        }).catch(() => {})
      }
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

  // Thanh tab dưới cùng (mobile): tối đa 4 mục chính đi thẳng, còn lại + tài khoản/trợ
  // giúp/đăng xuất gộp vào nút "Thêm" mở lại đúng sidebar này dạng sheet trượt lên.
  const tabItems = nav.slice(0, 4)
  const tabActive = tabItems.some(item => (item.exact ? pathname === item.href : pathname.startsWith(item.href)))

  const logout = () => {
    clearSession()
    router.push('/login')
  }

  const openTour = () => window.dispatchEvent(new Event('vn:open-tour'))

  const navLinkClass = (active: boolean) =>
    `group flex min-h-[44px] items-center gap-[13px] rounded-xl border px-3 text-sm font-semibold transition-colors duration-[180ms] ${active ? 'border-[var(--c-border)] bg-[var(--c-card)] text-[var(--c-green2)] shadow-[var(--shadow-sm)]' : 'border-transparent text-[var(--c-ink2)] hover:bg-white/60 hover:text-[var(--c-green2)]'}`
  const navIconClass = (active: boolean) => `w-[17px] flex-none ${active ? 'text-[var(--c-green2)]' : 'text-[var(--c-subtle)] group-hover:text-[var(--c-green2)]'}`

  return (
    <div className="[--sidebar-w:240px] min-h-screen bg-[#f7faf8]" style={{ backgroundImage: 'radial-gradient(circle at 90% 0,rgba(0,114,188,.1),transparent 31rem)' }} data-role={role}>
      <aside className={`fixed inset-y-0 left-0 z-40 flex w-[var(--sidebar-w)] flex-col overflow-auto border-r border-[var(--c-border)] bg-[var(--c-surface)] px-4 py-5 text-[var(--c-ink)] max-[900px]:transition-transform max-[900px]:duration-[240ms] max-[900px]:ease-in-out max-[520px]:w-[min(86vw,300px)] ${open ? 'max-[900px]:translate-x-0' : 'max-[900px]:-translate-x-[105%]'}`}>
        <div className="relative z-[1] flex min-h-[62px] items-center border-b border-[var(--c-border)] px-2 pb-4">
          <Link href={role === 'patient' ? '/patient' : '/dietitian'} className="flex min-w-0 items-center gap-3" aria-label="VNUTRICARE — về trang chính">
            <LeafMark className="h-11 w-[34px] flex-none text-[var(--c-green2)]" />
            <strong className="whitespace-nowrap font-[family-name:var(--f-serif)] text-[22px] font-semibold tracking-[.015em] text-[var(--c-ink)]">VNUTRICARE</strong>
          </Link>
          <button type="button" className="ml-auto hidden h-[34px] w-[34px] place-items-center rounded-[10px] bg-[var(--c-card)] text-[var(--c-ink2)] max-[900px]:grid" onClick={() => setOpen(false)} aria-label="Đóng menu">
            <Icon name="close" className="w-[18px]" />
          </button>
        </div>

        <nav className="relative z-[1] mt-6 grid gap-[3px]" aria-label={role === 'patient' ? 'Điều hướng người bệnh' : 'Điều hướng chuyên gia'}>
          {nav.map(item => {
            const active = item.exact ? pathname === item.href : pathname.startsWith(item.href)
            return (
              <Link key={item.href} href={item.href} className={navLinkClass(active)} onClick={() => setOpen(false)}>
                <Icon name={item.icon} className={navIconClass(active)} />
                <span>{item.label}</span>
                {item.badge === 'pending' && pending !== null && <b className="ml-auto grid h-[26px] min-w-[26px] place-items-center rounded-full bg-[var(--c-green)] px-[7px] text-xs font-semibold text-white">{pending}</b>}
              </Link>
            )
          })}
        </nav>

        {/* Nhóm phụ cuối sidebar: hướng dẫn / hỗ trợ / đăng xuất — tài khoản +
            sáng-tối/ngôn ngữ/chuông đã chuyển lên header phía trên nội dung. */}
        <div className="relative z-[1] mt-auto grid gap-[2px] border-t border-[var(--c-border)] pt-2.5">
          <button type="button" onClick={openTour} className="flex min-h-[42px] items-center gap-3 rounded-xl px-3 text-sm font-semibold text-[var(--c-muted)] hover:bg-white/60 hover:text-[var(--c-green2)]">
            <Icon name="document" className="w-4 flex-none text-[var(--c-subtle)]" />Hướng dẫn
          </button>
          <button type="button" onClick={() => setAssistantOpen(true)} className="flex min-h-[42px] items-center gap-3 rounded-xl px-3 text-sm font-semibold text-[var(--c-muted)] hover:bg-white/60 hover:text-[var(--c-green2)]">
            <Icon name="headset" className="w-4 flex-none text-[var(--c-subtle)]" />Liên hệ hỗ trợ
          </button>
          <button type="button" onClick={logout} className="flex min-h-[42px] items-center gap-3 rounded-xl px-3 text-sm font-semibold text-[var(--c-red)] hover:bg-red-50">
            <Icon name="logout" className="w-4 flex-none" />Đăng xuất
          </button>
        </div>
      </aside>

      {/* Header tiện ích: sáng/tối, ngôn ngữ, chuông thông báo, tài khoản.
          Đứng trên cùng mọi trang (patient lẫn dietitian) vì phần lớn trang
          không dùng chung 1 topbar riêng — đặt ở đây để có đúng 1 chỗ. */}
      <header className="sticky top-0 z-30 ml-[var(--sidebar-w)] flex h-[62px] items-center justify-end gap-2.5 border-b border-[var(--c-border)] bg-[rgba(247,250,255,.9)] px-8 backdrop-blur-md max-[900px]:ml-0 max-[900px]:px-4">
        <ThemeTogglePill />
        <LanguageToggle />
        <NotificationBell role={role} />
        <span className="grid h-9 w-9 place-items-center rounded-lg border border-[var(--c-border)] bg-[var(--c-card)]">
          <span className="grid h-[26px] w-[26px] place-items-center rounded-full bg-[var(--c-green)] text-xs font-bold text-white">{role === 'patient' ? 'BN' : 'CG'}</span>
        </span>
      </header>

      <main className="ml-[var(--sidebar-w)] min-h-screen min-w-0 max-[900px]:ml-0 max-[900px]:pb-[calc(64px+env(safe-area-inset-bottom))]">
        {children}
      </main>
      {open && <button type="button" className="fixed inset-0 z-[35] block bg-[rgba(17,48,49,.45)] backdrop-blur-[3px]" onClick={() => setOpen(false)} aria-label="Đóng menu" />}

      {/* Ẩn khi sheet "Thêm" đang mở — nếu không, tabbar (z-index cao hơn để luôn nổi
          trên nội dung trang) đè lên đúng phần tài khoản/đăng xuất ở cuối sidebar. */}
      {!open && <nav className="hidden max-[900px]:fixed max-[900px]:inset-x-0 max-[900px]:bottom-0 max-[900px]:z-[45] max-[900px]:flex max-[900px]:border-t-[1.5px] max-[900px]:border-[var(--c-lime)] max-[900px]:bg-[var(--c-card)] max-[900px]:px-1 max-[900px]:pt-1.5 max-[900px]:pb-[calc(6px+env(safe-area-inset-bottom))] max-[900px]:shadow-[0_-8px_24px_rgba(0,86,140,.1)]" aria-label="Thanh điều hướng nhanh">
        {tabItems.map(item => {
          const active = item.exact ? pathname === item.href : pathname.startsWith(item.href)
          return (
            <Link key={item.href} href={item.href} className={`relative flex min-w-0 flex-1 flex-col items-center gap-[3px] rounded-[10px] px-0.5 py-1.5 text-center text-xs font-semibold text-[var(--c-subtle)] ${active ? '!text-[var(--c-green2)]' : ''}`}>
              <Icon name={item.icon} className="w-[19px] flex-none" />
              <span className="max-w-full overflow-hidden text-ellipsis whitespace-nowrap">{item.tabLabel ?? item.label}</span>
              {item.badge === 'pending' && pending !== null && pending > 0 && <b className="absolute -top-0.5 right-[calc(50%-18px)] grid h-5 min-w-5 place-items-center rounded-full bg-[var(--c-green)] px-1 text-xs font-semibold leading-none text-white">{pending}</b>}
            </Link>
          )
        })}
        <button type="button" className={`relative flex min-w-0 flex-1 flex-col items-center gap-[3px] rounded-[10px] px-0.5 py-1.5 text-center text-xs font-semibold text-[var(--c-subtle)] ${!tabActive ? '!text-[var(--c-green2)]' : ''}`} onClick={() => setOpen(true)} aria-label="Thêm mục và tài khoản">
          <Icon name="more" className="w-[19px] flex-none" />
          <span className="max-w-full overflow-hidden text-ellipsis whitespace-nowrap">Thêm</span>
        </button>
      </nav>}
    </div>
  )
}
