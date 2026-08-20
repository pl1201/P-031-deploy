/**
 * Vòng tròn calo kiểu MyFitnessPal — chỉ trực quan hoá lại số đã có sẵn từ
 * backend (`computed_nutrition.kcal` / `targets.targets.kcal`), không tự tính
 * gì thêm ở frontend (RULE-1/RULE-2). Đổi màu theo trạng thái ăn nhưng dùng
 * token thương hiệu (--c-green/--c-accent), KHÔNG dùng màu cảnh báo lâm sàng
 * (--c-red/--c-orange/--c-yellow) để tránh gây hiểu nhầm là cảnh báo y tế.
 */
export function CalorieRing({ consumedKcal, targetKcal, size = 200 }: { consumedKcal: number; targetKcal: number | null; size?: number }) {
  const stroke = Math.round(size * 0.09)
  const radius = (size - stroke) / 2
  const circumference = 2 * Math.PI * radius
  const ratio = targetKcal && targetKcal > 0 ? Math.min(1, consumedKcal / targetKcal) : 0
  const over = targetKcal != null && consumedKcal > targetKcal
  const remaining = targetKcal != null ? Math.round(targetKcal - consumedKcal) : null
  const ringColor = !targetKcal ? 'var(--c-border2)' : over ? 'var(--c-accent)' : 'var(--c-green)'

  return (
    <div className="relative mx-auto grid place-items-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="block">
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="var(--c-lime)" strokeWidth={stroke} />
        <circle
          cx={size / 2} cy={size / 2} r={radius} fill="none" stroke={ringColor} strokeWidth={stroke}
          strokeLinecap="round" strokeDasharray={circumference} strokeDashoffset={circumference * (1 - ratio)}
          transform={`rotate(-90 ${size / 2} ${size / 2})`} style={{ transition: 'stroke-dashoffset .4s var(--ease-out), stroke .25s' }}
        />
      </svg>
      <div className="absolute inset-0 grid place-items-center gap-0.5 text-center">
        <strong className="font-[family-name:var(--f-serif)] text-[clamp(26px,7cqw,34px)] font-bold tabular-nums text-[var(--c-ink)]">{Math.round(consumedKcal).toLocaleString('vi-VN')}</strong>
        <small className="text-xs font-semibold uppercase tracking-[.04em] text-[var(--c-muted)]">kcal đã ăn</small>
        {remaining != null && <span className={`mt-1 rounded-full px-[10px] py-[4px] text-xs font-bold tabular-nums ${over ? 'bg-[#fff6dc] text-[#8a6d16]' : 'bg-[var(--c-lime2)] text-[var(--c-green2)]'}`}>{over ? `Vượt ${Math.abs(remaining).toLocaleString('vi-VN')}` : `Còn ${remaining.toLocaleString('vi-VN')}`}</span>}
      </div>
    </div>
  )
}
