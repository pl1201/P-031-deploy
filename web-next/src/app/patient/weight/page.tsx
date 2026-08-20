'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Icon } from '@/components/brand-artwork'
import { ApiError, createApiClient, type PatientObservation } from '@/lib/api'
import { getToken } from '@/lib/auth'

const CARD = 'rounded-2xl border border-[#d8e1e3] bg-white p-5 shadow-[0_9px_28px_rgba(27,83,81,.045)]'

type Period = 'day' | 'week'

/** Gộp điểm thô theo tuần (trung bình các điểm trong tuần) + trung bình trượt 7
 * điểm — phép toán thuần trên số cân nặng đã có, không suy đoán giá trị lâm sàng
 * mới (đúng quy ước RULE-1/RULE-2 đã áp dụng ở dietitian/analytics/charts.tsx). */
function buildChartModel(rows: PatientObservation[], period: Period) {
  const sorted = [...rows].sort((a, b) => a.measured_at.localeCompare(b.measured_at))
  const daily = sorted.map(row => ({ date: row.measured_at.slice(0, 10), value: row.value }))

  const points = period === 'day' ? daily : (() => {
    const byWeek = new Map<string, number[]>()
    for (const row of daily) {
      const d = new Date(`${row.date}T00:00:00`)
      const monday = new Date(d)
      monday.setDate(d.getDate() - ((d.getDay() + 6) % 7))
      const key = monday.toISOString().slice(0, 10)
      byWeek.set(key, [...(byWeek.get(key) ?? []), row.value])
    }
    return Array.from(byWeek.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([date, values]) => ({ date, value: values.reduce((s, v) => s + v, 0) / values.length }))
  })()

  const withTrend = points.map((point, index) => {
    const window = points.slice(Math.max(0, index - 6), index + 1)
    const trend = window.reduce((s, p) => s + p.value, 0) / window.length
    return { ...point, trend: Math.round(trend * 10) / 10 }
  })

  const latest = points.at(-1)?.value ?? null
  const previous = points.length > 1 ? points[points.length - 2].value : null
  const deltaVsPrevious = latest != null && previous != null ? latest - previous : null

  return { points: withTrend, latest, deltaVsPrevious }
}

export default function WeightPage() {
  const [rows, setRows] = useState<PatientObservation[]>([])
  const [period, setPeriod] = useState<Period>('day')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const [value, setValue] = useState('')
  const [note, setNote] = useState('')
  const [toast, setToast] = useState('')

  const refresh = useCallback(async () => {
    const token = getToken()
    if (!token) return
    setRows(await createApiClient(token).listMyWeightObservations())
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      refresh().catch(err => setError(err instanceof ApiError ? err.message : 'Không thể tải dữ liệu cân nặng.')).finally(() => setLoading(false))
    }, 0)
    return () => window.clearTimeout(timer)
  }, [refresh])

  const model = useMemo(() => buildChartModel(rows, period), [rows, period])

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    const parsed = Number(value)
    if (!Number.isFinite(parsed) || parsed < 20 || parsed > 300) {
      setError('Cân nặng phải trong khoảng 20–300 kg.')
      return
    }
    const token = getToken()
    if (!token) return
    setSaving(true)
    setError('')
    try {
      await createApiClient(token).logMyWeight(parsed, undefined, note.trim() || undefined)
      setValue('')
      setNote('')
      setToast('Đã lưu cân nặng hôm nay.')
      window.setTimeout(() => setToast(''), 2500)
      await refresh()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể lưu cân nặng.')
    } finally {
      setSaving(false)
    }
  }

  return <div className="min-h-screen px-[38px] pt-[34px] pb-12 text-[var(--c-ink)] max-[680px]:px-[15px] max-[680px]:pt-[72px] max-[680px]:pb-[30px]">
    <header>
      <small className="text-xs font-bold tracking-[.08em] text-[var(--c-green2)]">THEO DÕI ĐỊNH KỲ</small>
      <h1 className="mt-[6px] font-[family-name:var(--f-serif)] text-[clamp(30px,4vw,38px)] leading-[1.15] font-semibold">Cân nặng</h1>
      <p className="mt-[6px] max-w-[62ch] text-base leading-[1.6] text-[var(--c-muted)]">Ghi cân nặng theo ngày hoặc tuần để chuyên gia theo dõi xu hướng — số này KHÔNG thay hồ sơ lâm sàng gốc, chuyên gia vẫn là người xác nhận mọi thay đổi hồ sơ.</p>
    </header>

    {error && <div className="mt-3.5 flex gap-2 rounded-[11px] border border-[#efb4a4] bg-[#fff5f1] p-3 text-sm text-[#8b3d2b]" role="alert"><Icon name="warning" className="w-[18px]" />{error}</div>}
    {toast && <div className="mt-3.5 flex gap-2 rounded-[11px] border border-[#b8dfd7] bg-[#e8f5f3] p-3 text-sm text-[var(--c-green2)]" role="status"><Icon name="check" className="w-[18px]" />{toast}</div>}

    {loading ? <div className="mt-[18px] h-[390px] animate-[skeleton-pulse_1.3s_infinite] rounded-2xl bg-[linear-gradient(90deg,#e7eeef,var(--c-bg),#e7eeef)] bg-[length:200%_100%]" /> : <div className="mt-[18px] grid grid-cols-[minmax(0,1.35fr)_minmax(280px,.65fr)] gap-3.5 max-[950px]:grid-cols-1">
      <main className="grid content-start gap-3.5">
        <section className={CARD}>
          <div className="flex items-center justify-between">
            <div>
              <small className="text-xs font-bold tracking-[.08em] text-[var(--c-green2)]">XU HƯỚNG</small>
              <h2 className="mt-1 font-[family-name:var(--f-serif)] text-2xl font-semibold tabular-nums">{model.latest != null ? `${model.latest} kg` : 'Chưa có dữ liệu'}</h2>
              {model.deltaVsPrevious != null && <small className={`text-sm font-semibold tabular-nums ${model.deltaVsPrevious > 0 ? 'text-[#c0392b]' : model.deltaVsPrevious < 0 ? 'text-[var(--c-green2)]' : 'text-[var(--c-muted)]'}`}>{model.deltaVsPrevious > 0 ? '+' : ''}{model.deltaVsPrevious.toFixed(1)} kg so với kỳ trước</small>}
            </div>
            <div className="flex gap-1 rounded-xl bg-[var(--c-lime2)] p-1">
              {(['day', 'week'] as const).map(item => <button key={item} type="button" onClick={() => setPeriod(item)} className={`min-h-[38px] rounded-[9px] px-3.5 text-sm font-semibold ${period === item ? 'bg-white text-[var(--c-green2)] shadow-sm' : 'text-[var(--c-muted)]'}`}>{item === 'day' ? 'Ngày' : 'Tuần'}</button>)}
            </div>
          </div>
          {model.points.length ? <div className="mt-4 h-[220px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={model.points} margin={{ left: -12, right: 8, top: 8, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e3e9ea" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} tickFormatter={d => d.slice(5)} />
                <YAxis tick={{ fontSize: 12 }} domain={['dataMin - 2', 'dataMax + 2']} />
                <Tooltip formatter={(v) => [`${v} kg`, '']} labelFormatter={d => new Date(`${d}T00:00:00`).toLocaleDateString('vi-VN')} />
                <Line type="monotone" dataKey="value" stroke="var(--c-carb)" strokeWidth={2} dot={{ r: 3 }} name="Cân nặng" />
                <Line type="monotone" dataKey="trend" stroke="#98948f" strokeWidth={1.5} strokeDasharray="4 3" dot={false} name="Trung bình trượt" />
              </LineChart>
            </ResponsiveContainer>
          </div> : <p className="py-6 text-center text-sm text-[var(--c-muted)]">Chưa có bản ghi nào — nhập cân nặng đầu tiên ở bên phải.</p>}
        </section>

        <section className={CARD}>
          <small className="text-xs font-bold tracking-[.08em] text-[var(--c-green2)]">LỊCH SỬ</small>
          <h2 className="mt-1 font-[family-name:var(--f-serif)] text-2xl font-semibold">Các lần ghi gần đây</h2>
          <div className="mt-3.5">{rows.length ? [...rows].slice(0, 20).map(row => <article key={row.id} className="flex items-center justify-between gap-2.5 border-b border-[#e3e9ea] py-2.5 last:border-0">
            <div><strong className="text-base font-semibold tabular-nums">{row.value} kg</strong>{row.note && <span className="ml-2 text-sm text-[var(--c-muted)]">{row.note}</span>}</div>
            <time className="text-xs text-[var(--c-muted)]">{new Date(row.measured_at).toLocaleString('vi-VN')}</time>
          </article>) : <p className="py-6 text-center text-sm text-[var(--c-muted)]">Chưa có bản ghi.</p>}</div>
        </section>
      </main>

      <aside className="grid content-start gap-3.5">
        <form onSubmit={submit} className={CARD}>
          <small className="text-xs font-bold tracking-[.08em] text-[var(--c-green2)]">GHI NHANH</small>
          <h2 className="mt-1 font-[family-name:var(--f-serif)] text-2xl font-semibold">Nhập cân nặng hôm nay</h2>
          <label className="mt-3.5 grid gap-1.5 text-sm font-semibold">Cân nặng (kg)
            <input required type="number" min={20} max={300} step={0.1} value={value} onChange={e => setValue(e.target.value)} className="h-11 rounded-[9px] border border-[#cad5d8] bg-white px-3 text-base" placeholder="Ví dụ: 64.5" />
          </label>
          <label className="mt-2.5 grid gap-1.5 text-sm font-semibold">Ghi chú (tuỳ chọn)
            <input type="text" value={note} onChange={e => setNote(e.target.value)} maxLength={200} className="h-11 rounded-[9px] border border-[#cad5d8] bg-white px-3 text-base" placeholder="Trước ăn sáng…" />
          </label>
          <button type="submit" disabled={saving || !value} className="mt-3.5 flex h-11 w-full items-center justify-center gap-2 rounded-xl bg-[var(--c-green)] text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50">
            {saving ? <span className="spinner" /> : <Icon name="check" className="w-4" />}
            {saving ? 'Đang lưu…' : 'Lưu cân nặng'}
          </button>
        </form>
        <section className="grid grid-cols-[39px_1fr] gap-2.5 rounded-2xl border border-[#d8e1e3] bg-white p-5 shadow-[0_9px_28px_rgba(27,83,81,.045)]">
          <Icon name="info" className="w-[37px] rounded-xl bg-[#e3f0f4] p-2.5 text-[var(--c-green2)]" />
          <div><h2 className="font-[family-name:var(--f-serif)] text-lg font-semibold">Vì sao tách khỏi hồ sơ?</h2><p className="mt-[6px] text-sm leading-[1.6] text-[var(--c-muted)]">Số bạn tự ghi ở đây giúp chuyên gia thấy xu hướng giữa các lần khám, nhưng không tự động cập nhật hồ sơ lâm sàng gốc — mọi thay đổi hồ sơ vẫn cần chuyên gia xác nhận.</p></div>
        </section>
      </aside>
    </div>}
  </div>
}
