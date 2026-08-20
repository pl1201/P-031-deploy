'use client'

import { useMemo, useState } from 'react'
import { Icon } from '@/components/brand-artwork'

type MetricKey = 'steps' | 'restingHeartRate' | 'sleep' | 'activeEnergy'

const METRICS: Array<{
  key: MetricKey
  icon: string
  label: string
  trust: string
  trustClass: string
  description: string
}> = [
  { key: 'steps', icon: 'trend', label: 'Bước chân', trust: 'Đáng tin cao', trustClass: 'bg-emerald-50 text-emerald-800', description: 'Dùng để chuyên gia xem xu hướng hoạt động.' },
  { key: 'restingHeartRate', icon: 'heart', label: 'Nhịp tim nghỉ', trust: 'Đáng tin khá', trustClass: 'bg-sky-50 text-sky-800', description: 'Chỉ hiển thị tham khảo; không dùng để tự chẩn đoán.' },
  { key: 'sleep', icon: 'moon', label: 'Giấc ngủ', trust: 'Tham khảo', trustClass: 'bg-amber-50 text-amber-900', description: 'Thiết bị tiêu dùng có thể nhận diện sai thời gian ngủ.' },
  { key: 'activeEnergy', icon: 'sparkles', label: 'Calo tiêu hao', trust: 'Sai số lớn', trustClass: 'bg-rose-50 text-rose-900', description: 'Không bao giờ dùng để tăng mục tiêu kcal hoặc khẩu phần.' },
]

export default function PatientActivityPage() {
  const [selected, setSelected] = useState<Record<MetricKey, boolean>>({
    steps: true,
    restingHeartRate: true,
    sleep: false,
    activeEnergy: false,
  })
  const [notice, setNotice] = useState('')
  const selectedCount = useMemo(() => Object.values(selected).filter(Boolean).length, [selected])

  const explainUnavailable = () => {
    setNotice('Kết nối Apple Health đang chờ backend HealthKit và kiểm duyệt consent. Chưa có dữ liệu nào được gửi đi.')
  }

  return (
    <div className="mx-auto w-full max-w-[1120px] px-5 py-8 text-[var(--c-ink)] md:px-9 md:py-11">
      <header className="grid gap-5 border-b border-[var(--c-border)] pb-8 lg:grid-cols-[1fr_360px] lg:items-end">
        <div>
          <span className="text-xs font-bold uppercase tracking-[.08em] text-[var(--c-green2)]">Quan sát sức khỏe</span>
          <h1 className="mt-3 max-w-[720px] font-[family-name:var(--f-serif)] text-[clamp(30px,5vw,50px)] font-semibold leading-[1.08] tracking-[-.02em]">Thiết bị ghi nhận.<br />Chuyên gia quyết định.</h1>
          <p className="mt-4 max-w-[680px] text-base leading-[1.6] text-[var(--c-muted)]">Apple Health chỉ cung cấp thêm bối cảnh cho hồ sơ của bạn. Dữ liệu thiết bị không tự thay đổi mục tiêu năng lượng, khẩu phần hay thuốc.</p>
        </div>
        <aside className="rounded-[18px] border border-emerald-200 bg-emerald-50/70 p-5">
          <div className="flex items-start gap-3"><span className="grid h-10 w-10 flex-none place-items-center rounded-xl bg-white text-emerald-800 shadow-sm"><Icon name="shield" className="w-5" /></span><div><strong className="text-base font-semibold">Bạn kiểm soát dữ liệu</strong><p className="mt-1 text-sm leading-[1.5] text-emerald-950/70">Chọn riêng từng chỉ số. Có thể tiếp tục sử dụng ứng dụng mà không kết nối thiết bị.</p></div></div>
        </aside>
      </header>

      <main className="mt-8 grid gap-6 lg:grid-cols-[1fr_320px]">
        <section aria-labelledby="health-permissions-title" className="rounded-[22px] border border-[var(--c-border)] bg-[var(--c-card)] p-5 shadow-[var(--shadow-sm)] md:p-7">
          <div className="flex flex-wrap items-end justify-between gap-3"><div><span className="text-xs font-bold uppercase tracking-[.08em] text-[var(--c-muted)]">Quyền đọc đề xuất</span><h2 id="health-permissions-title" className="mt-1 font-[family-name:var(--f-serif)] text-2xl font-semibold">Chọn chỉ số muốn chia sẻ</h2></div><span className="rounded-full bg-[var(--c-surface)] px-3 py-1.5 text-xs font-semibold text-[var(--c-muted)]">Đã chọn {selectedCount}/4</span></div>
          <div className="mt-6 grid gap-3">
            {METRICS.map(metric => (
              <label key={metric.key} className="grid min-h-[84px] cursor-pointer grid-cols-[42px_1fr_auto] items-center gap-3 rounded-2xl border border-[var(--c-border)] px-4 py-3 transition-colors hover:border-[var(--c-green2)] has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-[var(--c-green2)] has-[:focus-visible]:ring-offset-2">
                <span className="grid h-10 w-10 place-items-center rounded-xl bg-[var(--c-surface)] text-[var(--c-green2)]"><Icon name={metric.icon} className="w-5" /></span>
                <span><span className="flex flex-wrap items-center gap-2"><strong className="text-base font-semibold">{metric.label}</strong><small className={`rounded-full px-2.5 py-1 text-xs font-semibold ${metric.trustClass}`}>{metric.trust}</small></span><small className="mt-1 block text-sm leading-[1.5] text-[var(--c-muted)]">{metric.description}</small></span>
                <input className="h-5 w-5 accent-[var(--c-green2)]" type="checkbox" checked={selected[metric.key]} onChange={event => setSelected(current => ({ ...current, [metric.key]: event.target.checked }))} aria-label={`Chia sẻ ${metric.label}`} />
              </label>
            ))}
          </div>
          <div className="mt-6 flex flex-wrap gap-3"><button type="button" onClick={explainUnavailable} className="min-h-11 rounded-xl bg-[var(--c-green)] px-5 text-sm font-semibold text-white shadow-lg shadow-emerald-950/10">Tiếp tục với Apple Health</button><button type="button" onClick={() => setNotice('Bạn có thể nhập dữ liệu thủ công như trước. Không có quyền thiết bị nào được yêu cầu.')} className="min-h-11 rounded-xl border border-[var(--c-border)] bg-white px-5 text-sm font-semibold">Bỏ qua, nhập tay</button></div>
          <p className="mt-3 min-h-5 text-sm leading-[1.5] text-[var(--c-muted)]" aria-live="polite">{notice}</p>
        </section>

        <aside className="grid content-start gap-4">
          <section className="rounded-[22px] bg-[#173d3d] p-6 text-white shadow-xl shadow-emerald-950/10">
            <span className="text-xs font-bold uppercase tracking-[.08em] text-emerald-200">Ranh giới an toàn</span>
            <h2 className="mt-3 font-[family-name:var(--f-serif)] text-2xl font-semibold">Không có vòng “đốt rồi ăn bù”</h2>
            <p className="mt-3 text-sm leading-[1.6] text-white/70">Calo do đồng hồ ước tính có thể sai lệch đáng kể. VNUTRICARE không cộng số này vào TDEE và không tự tăng khẩu phần trong ngày.</p>
          </section>
          <section className="rounded-[18px] border border-amber-200 bg-amber-50 p-5">
            <div className="flex gap-3"><Icon name="info" className="mt-0.5 w-5 flex-none text-amber-800" /><div><strong className="text-base font-semibold text-amber-950">Tính năng đang chuẩn bị</strong><p className="mt-1 text-sm leading-[1.5] text-amber-950/70">Màn hình consent đã sẵn sàng. Kết nối thật cần backend HealthKit, chính sách quyền riêng tư và R2 duyệt ngưỡng cảnh báo.</p></div></div>
          </section>
        </aside>
      </main>
    </div>
  )
}
