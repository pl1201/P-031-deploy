function isNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value)
}

/**
 * Bộ 3 macro "khoá màu" kiểu MyFitnessPal — Carb/Đạm/Béo luôn cùng 1 màu ở
 * mọi nơi hiển thị (token --c-carb/--c-protein/--c-fat, xem globals.css).
 * kcal quy đổi từ gram dùng hệ số Atwater chuẩn (4/4/9 kcal/g) — hằng số khoa
 * học dinh dưỡng cố định, không phải giá trị lâm sàng cần backend tính (khác
 * RULE-1, vốn áp cho ngưỡng/mục tiêu theo bệnh lý cụ thể). Grams/kcal gốc vẫn
 * lấy nguyên từ `computed_nutrition` do SQL tính, không tự bịa số mới.
 */
export function MacroTrio({ carbG, proteinG, fatG, fiberG }: { carbG: number; proteinG: number; fatG: number; fiberG: number }) {
  const carbKcal = isNumber(carbG) ? carbG * 4 : 0
  const proteinKcal = isNumber(proteinG) ? proteinG * 4 : 0
  const fatKcal = isNumber(fatG) ? fatG * 9 : 0
  const total = carbKcal + proteinKcal + fatKcal
  const parts = [
    { key: 'carb', label: 'Carb', grams: carbG, kcal: carbKcal, color: 'bg-[var(--c-carb)]' },
    { key: 'protein', label: 'Đạm', grams: proteinG, kcal: proteinKcal, color: 'bg-[var(--c-protein)]' },
    { key: 'fat', label: 'Béo', grams: fatG, kcal: fatKcal, color: 'bg-[var(--c-fat)]' },
  ]
  return (
    <div className="mt-2.5">
      {total > 0 && <div className="flex h-3 overflow-hidden rounded-full bg-[var(--c-surface)]">{parts.map(part => part.kcal > 0 && <i key={part.key} className={`block h-full ${part.color}`} style={{ width: `${(part.kcal / total) * 100}%` }} />)}</div>}
      <div className="mt-3 grid gap-1.5">
        {parts.map(part => (
          <div key={part.key} className="flex items-center gap-[7px] rounded-[9px] border border-[var(--c-border)] px-[9px] py-2">
            <i className={`h-[9px] w-[9px] flex-none rounded-[3px] ${part.color}`} />
            <small className="text-xs text-[var(--c-muted)]">{part.label}</small>
            <strong className="ml-auto font-[family-name:var(--f-serif)] text-sm font-bold tabular-nums">{isNumber(part.grams) ? Math.round(part.grams) : '—'} g</strong>
            <span className="min-w-[30px] text-right text-xs tabular-nums text-[var(--c-subtle)]">{total > 0 ? `${Math.round((part.kcal / total) * 100)}%` : ''}</span>
          </div>
        ))}
        <div className="flex items-center gap-[7px] rounded-[9px] border border-[var(--c-border)] px-[9px] py-2">
          <i className="h-[9px] w-[9px] flex-none rounded-[3px] bg-[var(--c-green3)]" />
          <small className="text-xs text-[var(--c-muted)]">Xơ</small>
          <strong className="ml-auto font-[family-name:var(--f-serif)] text-sm font-bold tabular-nums">{isNumber(fiberG) ? Math.round(fiberG) : '—'} g</strong>
          <span className="min-w-[30px] text-right text-xs text-[var(--c-subtle)]" />
        </div>
      </div>
    </div>
  )
}
