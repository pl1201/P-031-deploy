'use client'

import { useEffect, useRef, useState } from 'react'
import { Icon } from '@/components/brand-artwork'
import { ApiError, createApiClient, type AppNotification } from '@/lib/api'
import { getToken } from '@/lib/auth'

const SEVERITY_DOT: Record<string, string> = {
  critical: 'bg-[var(--c-red)]',
  warning: 'bg-[#b8780a]',
  info: 'bg-[var(--c-green2)]',
}

function timeAgo(iso: string): string {
  const min = Math.round((Date.now() - new Date(iso).getTime()) / 60000)
  if (min < 1) return 'Vừa xong'
  if (min < 60) return `${min} phút trước`
  const hr = Math.round(min / 60)
  if (hr < 24) return `${hr} giờ trước`
  return `${Math.round(hr / 24)} ngày trước`
}

/** Chuông thông báo dùng chung 2 vai trò (bệnh nhân/chuyên gia) — đặt trong
 * WorkspaceShell nên không cần lặp lại ở từng trang. Poll unread-count giống cơ
 * chế REVIEW_QUEUE_CHANGED_EVENT đã có, nhưng không có event nội bộ để bắt (thông
 * báo được server tạo từ nơi khác), nên dùng interval — 30s đủ nhanh cho 1 trung
 * tâm thông báo không cần realtime tức thời. */
function patientMealReminder() {
  const hour = new Date().getHours()
  if (hour < 9) return { title: 'Chào buổi sáng', body: 'Khi ăn sáng xong, bạn nhớ ghi lại bữa ăn nhé.' }
  if (hour < 14) return { title: 'Một lời nhắc nhẹ cho bữa trưa', body: 'Khi thuận tiện, bạn hãy cho chúng tôi biết bữa trưa hôm nay thế nào nhé.' }
  if (hour < 17) return { title: 'Bạn đã dùng bữa phụ chưa?', body: 'Nếu có ăn món khác kế hoạch, bạn chỉ cần ghi lại đúng như thực tế.' }
  return { title: 'Một lời nhắc nhẹ cho bữa tối', body: 'Sau bữa tối, bạn nhớ ghi lại món đã ăn hoặc báo nếu đã bỏ bữa nhé.' }
}

export function NotificationBell({ className, role }: { className?: string; role?: 'patient' | 'dietitian' }) {
  const [open, setOpen] = useState(false)
  const [items, setItems] = useState<AppNotification[]>([])
  const [unread, setUnread] = useState(0)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const token = getToken()
    if (!token) return
    const api = createApiClient(token)
    const poll = () => { void api.unreadNotificationCount().then(r => setUnread(r.unread)).catch(() => {}) }
    poll()
    const timer = window.setInterval(poll, 30000)
    return () => window.clearInterval(timer)
  }, [])

  useEffect(() => {
    if (!open) return
    const token = getToken()
    if (!token) return
    createApiClient(token).listNotifications().then(setItems).catch(() => {})
  }, [open])

  useEffect(() => {
    if (!open) return
    const onClick = (event: MouseEvent) => { if (ref.current && !ref.current.contains(event.target as Node)) setOpen(false) }
    window.addEventListener('mousedown', onClick)
    return () => window.removeEventListener('mousedown', onClick)
  }, [open])

  const markAllRead = async () => {
    const token = getToken()
    if (!token) return
    try {
      await createApiClient(token).markAllNotificationsRead()
      setUnread(0)
      setItems(current => current.map(item => ({ ...item, read_at: item.read_at ?? new Date().toISOString() })))
    } catch (err) {
      if (!(err instanceof ApiError)) throw err
    }
  }

  // Cho phép caller override position (vd "fixed") — không hard-code "relative" đè lên,
  // 2 utility class Tailwind cùng set `position` có thể xung đột thứ tự nếu ép cả 2.
  const hasOwnPosition = /\b(fixed|absolute|sticky|static)\b/.test(className ?? '')
  return <div ref={ref} className={`${hasOwnPosition ? '' : 'relative '}${className ?? ''}`}>
    <button type="button" onClick={() => setOpen(v => !v)} aria-label={`Thông báo${unread > 0 ? ` (${unread} chưa đọc)` : ''}`} className="relative grid h-[30px] w-[30px] place-items-center rounded-lg text-[var(--c-muted)] hover:bg-[var(--c-lime2)] hover:text-[var(--c-green2)]">
      <Icon name="bell" className="w-[17px]" />
      {unread > 0 && <b className="absolute -right-1 -top-1 grid h-5 min-w-5 place-items-center rounded-full bg-[var(--c-red)] px-1 text-xs font-bold leading-none text-white">{unread > 9 ? '9+' : unread}</b>}
    </button>
    {open && <div className="absolute right-0 top-[38px] z-[60] w-[320px] max-w-[90vw] rounded-2xl border border-[var(--c-border)] bg-white shadow-[0_18px_44px_rgba(8,65,122,.18)]">
      <div className="flex items-center justify-between border-b border-[var(--c-border)] px-3.5 py-3">
        <strong className="text-sm font-semibold">Thông báo</strong>
        {unread > 0 && <button type="button" onClick={markAllRead} className="text-xs font-semibold text-[var(--c-green2)]">Đánh dấu đã đọc</button>}
      </div>
      <div className="max-h-[360px] overflow-y-auto">
        {role === 'patient' && <div className="flex gap-2.5 border-b border-[var(--c-border)] bg-[#f4faf7] px-3.5 py-3">
          <span className="mt-0.5 grid h-7 w-7 flex-none place-items-center rounded-full bg-white text-[var(--c-green2)] shadow-sm"><Icon name="bell" className="w-3.5" /></span>
          <div className="min-w-0"><strong className="block text-sm font-semibold">{patientMealReminder().title}</strong><p className="mt-0.5 text-xs leading-[1.5] text-[var(--c-muted)]">{patientMealReminder().body}</p><time className="mt-1 block text-xs text-[var(--c-subtle)]">Hôm nay</time></div>
        </div>}
        {items.length ? items.map(item => <div key={item.id} className={`flex gap-2.5 border-b border-[var(--c-border)] px-3.5 py-3 last:border-0 ${item.read_at ? '' : 'bg-[#f6faf9]'}`}>
          <span className={`mt-1.5 h-2 w-2 flex-none rounded-full ${SEVERITY_DOT[item.severity] ?? SEVERITY_DOT.info}`} />
          <div className="min-w-0">
            <strong className="block text-sm font-semibold">{item.title}</strong>
            <p className="mt-0.5 text-xs leading-[1.5] text-[var(--c-muted)]">{item.body}</p>
            <time className="mt-1 block text-xs text-[var(--c-subtle)]">{timeAgo(item.created_at)}</time>
          </div>
        </div>) : role !== 'patient' && <p className="px-3.5 py-8 text-center text-xs text-[var(--c-muted)]">Chưa có thông báo nào.</p>}
      </div>
    </div>}
  </div>
}
