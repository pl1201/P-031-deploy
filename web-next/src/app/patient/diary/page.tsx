'use client'
import { useCallback, useEffect, useState } from 'react'
import {
  createApiClient,
  type DaySummary,
  type FoodLog,
  type NutrientVerdict,
  type Violation,
} from '@/lib/api'
import { getToken } from '@/lib/auth'

const SLOTS = [
  { value: 'breakfast', label: 'Sáng' },
  { value: 'lunch', label: 'Trưa' },
  { value: 'dinner', label: 'Tối' },
  { value: 'snack', label: 'Phụ' },
]

/**
 * Nhãn cho từng kết luận.
 *
 * `insufficient_data` CÓ Ý ĐỒ không dùng màu xanh và không dùng chữ "đạt":
 * khi còn món chưa tra được, tổng tính ra chỉ là MỨC TỐI THIỂU, nên "chưa vượt
 * ngưỡng" hoàn toàn không đồng nghĩa với "ổn". Hiển thị nhầm chỗ này là biến
 * một hệ thống trung thực thành một hệ thống trấn an sai.
 */
const VERDICT_UI: Record<string, { text: string; cls: string; icon: string }> = {
  exceeded: { text: 'Đã vượt ngưỡng', cls: 'badge-hard', icon: '▲' },
  below_min: { text: 'Thấp hơn mức tối thiểu', cls: 'badge-soft', icon: '▼' },
  within: { text: 'Trong ngưỡng', cls: 'badge-ok', icon: '✓' },
  insufficient_data: { text: 'Chưa đủ dữ liệu để kết luận', cls: 'badge-draft', icon: '?' },
}

function todayISO() {
  return new Date().toISOString().slice(0, 10)
}

export default function DiaryPage() {
  const [profileId, setProfileId] = useState<string | null>(null)
  const [logs, setLogs] = useState<FoodLog[]>([])
  const [summary, setSummary] = useState<DaySummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [text, setText] = useState('')
  const [grams, setGrams] = useState('')
  const [slot, setSlot] = useState('lunch')
  const [lastResult, setLastResult] = useState<FoodLog | null>(null)

  const day = todayISO()

  const refresh = useCallback(async (pid: string) => {
    const token = getToken()
    if (!token) return
    const api = createApiClient(token)
    const [l, s] = await Promise.all([api.listFoodLogs(pid, day), api.getDaySummary(pid, day)])
    setLogs(l)
    setSummary(s)
  }, [day])

  useEffect(() => {
    const token = getToken()
    if (!token) return
    createApiClient(token)
      .getMyProfile()
      .then(async p => {
        setProfileId(p.id)
        await refresh(p.id)
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }, [refresh])

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault()
    if (!profileId || !text.trim()) return
    setSaving(true)
    setError(null)
    try {
      const api = createApiClient(getToken()!)
      const created = await api.createFoodLog({
        profile_id: profileId,
        free_text_vi: text.trim(),
        grams: grams ? Number(grams) : null,
        slot,
      })
      setLastResult(created)
      setText('')
      setGrams('')
      await refresh(profileId)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setSaving(false)
    }
  }

  const unmatchedViolations = summary?.violations.filter(v => v.kind === 'unmatched_food') ?? []
  const otherViolations = summary?.violations.filter(v => v.kind !== 'unmatched_food') ?? []

  return (
    <>
      <div className="topbar">
        <h1 className="page-title">Nhật ký ăn uống</h1>
        <div className="topbar-actions">
          <span style={{ fontSize: 13, color: 'var(--c-muted)' }}>{day}</span>
        </div>
      </div>

      <div className="page-body">
        {loading ? (
          <div style={{ display: 'grid', placeItems: 'center', height: '40vh' }}>
            <span className="spinner" style={{ width: 32, height: 32, color: 'var(--c-green)' }} />
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 24, alignItems: 'start' }}>
            {/* ------------------------------------------------ cột trái */}
            <div style={{ display: 'grid', gap: 20 }}>
              <form className="card" style={{ padding: 20 }} onSubmit={handleAdd}>
                <h2 style={{ fontFamily: 'var(--f-serif)', fontSize: 18, marginBottom: 4 }}>
                  Hôm nay bạn ăn gì?
                </h2>
                <p style={{ fontSize: 13, color: 'var(--c-muted)', marginBottom: 14 }}>
                  Cứ gõ tên món như bạn vẫn gọi. Nếu hệ thống chưa có món đó, chuyên gia dinh dưỡng
                  sẽ bổ sung giúp bạn — bạn không cần tự tra cứu.
                </p>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 110px 110px auto', gap: 10 }}>
                  <input
                    className="input"
                    placeholder="VD: cơm tẻ, canh rau muống, thịt kho…"
                    value={text}
                    onChange={e => setText(e.target.value)}
                    maxLength={255}
                  />
                  <input
                    className="input"
                    type="number"
                    placeholder="gram"
                    value={grams}
                    onChange={e => setGrams(e.target.value)}
                    min={1}
                    max={5000}
                  />
                  <select className="input" value={slot} onChange={e => setSlot(e.target.value)}>
                    {SLOTS.map(s => (
                      <option key={s.value} value={s.value}>{s.label}</option>
                    ))}
                  </select>
                  <button className="btn btn-primary" disabled={saving || !text.trim()}>
                    {saving ? 'Đang lưu…' : 'Ghi lại'}
                  </button>
                </div>

                <p style={{ fontSize: 12, color: 'var(--c-muted)', marginTop: 8 }}>
                  Không nhớ chính xác bao nhiêu gram? Cứ để trống — thà ghi thiếu còn hơn ghi sai.
                </p>

                {error && (
                  <p style={{ color: 'var(--c-red, #c0392b)', fontSize: 13, marginTop: 10 }}>{error}</p>
                )}

                {lastResult && lastResult.match_status === 'unmatched' && (
                  <div className="disclaimer" style={{ marginTop: 12 }}>
                    Đã ghi <strong>“{lastResult.free_text_vi}”</strong>. Hệ thống chưa tra được món này
                    nên <strong>chưa tính vào tổng của bạn</strong> — chuyên gia sẽ đối chiếu và bổ sung.
                    {lastResult.suggestions.length > 0 && (
                      <> Có thể là: {lastResult.suggestions.slice(0, 3).map(s => s.name_vi).join(', ')}.</>
                    )}
                  </div>
                )}
              </form>

              <div className="card" style={{ padding: 20 }}>
                <h2 style={{ fontFamily: 'var(--f-serif)', fontSize: 18, marginBottom: 12 }}>
                  Đã ghi hôm nay ({logs.length})
                </h2>
                {logs.length === 0 ? (
                  <p style={{ color: 'var(--c-muted)', fontSize: 14 }}>Chưa có món nào.</p>
                ) : (
                  <div style={{ display: 'grid', gap: 8 }}>
                    {logs.map(log => (
                      <LogRow key={log.id} log={log} />
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* ------------------------------------------------ cột phải */}
            <div style={{ display: 'grid', gap: 16 }}>
              {summary && <CoverageCard summary={summary} />}

              {summary && (
                <div className="card" style={{ padding: 18 }}>
                  <h3 style={{ fontSize: 15, marginBottom: 12 }}>Tổng hợp ngày</h3>
                  <div style={{ display: 'grid', gap: 10 }}>
                    {summary.verdicts.map(v => (
                      <VerdictRow key={v.nutrient} v={v} />
                    ))}
                  </div>
                </div>
              )}

              {unmatchedViolations.length > 0 && (
                <div className="card" style={{ padding: 18 }}>
                  <h3 style={{ fontSize: 15, marginBottom: 10 }}>
                    Món chờ chuyên gia đối chiếu ({unmatchedViolations.length})
                  </h3>
                  <div style={{ display: 'grid', gap: 8 }}>
                    {unmatchedViolations.map((v, i) => (
                      <ViolationRow key={i} v={v} />
                    ))}
                  </div>
                </div>
              )}

              {otherViolations.length > 0 && (
                <div className="card" style={{ padding: 18 }}>
                  <h3 style={{ fontSize: 15, marginBottom: 10 }}>Lưu ý ({otherViolations.length})</h3>
                  <div style={{ display: 'grid', gap: 8 }}>
                    {otherViolations.map((v, i) => (
                      <ViolationRow key={i} v={v} />
                    ))}
                  </div>
                </div>
              )}

              <p className="disclaimer">
                ⚕️ Nhật ký giúp chuyên gia hiểu bạn ăn gì. Đây không phải chẩn đoán y khoa.
              </p>
            </div>
          </div>
        )}
      </div>
    </>
  )
}

function LogRow({ log }: { log: FoodLog }) {
  const chuaTraDuoc = log.match_status === 'unmatched'
  const khongDuDuLieu = log.match_status === 'no_data'
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '10px 12px',
        borderRadius: 'var(--r-md)',
        background: chuaTraDuoc || khongDuDuLieu ? 'rgba(0,0,0,.03)' : 'transparent',
        border: '1px solid var(--c-border, rgba(0,0,0,.08))',
      }}
    >
      <span style={{ fontSize: 13, minWidth: 46, color: 'var(--c-muted)' }}>
        {SLOTS.find(s => s.value === log.slot)?.label ?? '—'}
      </span>
      <span style={{ flex: 1, fontSize: 14 }}>
        {log.food_name_vi ?? log.free_text_vi}
        {log.food_name_vi && log.free_text_vi !== log.food_name_vi && (
          <span style={{ color: 'var(--c-muted)', fontSize: 12 }}> (bạn ghi: {log.free_text_vi})</span>
        )}
      </span>
      <span style={{ fontSize: 13, color: 'var(--c-muted)', minWidth: 60, textAlign: 'right' }}>
        {log.grams != null ? `${log.grams} g` : '— g'}
      </span>
      {chuaTraDuoc && <span className="badge badge-soft">chờ đối chiếu</span>}
      {khongDuDuLieu && <span className="badge badge-draft">không đủ dữ liệu</span>}
    </div>
  )
}

function CoverageCard({ summary }: { summary: DaySummary }) {
  const pct = Math.round(summary.coverage * 100)
  return (
    <div className="card" style={{ padding: 18 }}>
      <h3 style={{ fontSize: 15, marginBottom: 8 }}>Độ đầy đủ dữ liệu</h3>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
        <span style={{ fontSize: 30, fontFamily: 'var(--f-serif)' }}>{pct}%</span>
        <span style={{ fontSize: 13, color: 'var(--c-muted)' }}>
          {summary.matched_count}/{summary.matched_count + summary.unmatched_count} món tra được
        </span>
      </div>
      {!summary.is_complete && (
        <p style={{ fontSize: 12.5, color: 'var(--c-muted)', marginTop: 8, lineHeight: 1.5 }}>
          Còn món chưa tra được, nên các con số bên dưới là <strong>mức tối thiểu</strong> — thực tế
          có thể cao hơn. Vì vậy hệ thống không kết luận “đạt ngưỡng”.
        </p>
      )}
    </div>
  )
}

function VerdictRow({ v }: { v: NutrientVerdict }) {
  const ui = VERDICT_UI[v.verdict] ?? VERDICT_UI.insufficient_data
  const gioiHan =
    v.max_value != null ? `tối đa ${v.max_value}` : v.min_value != null ? `tối thiểu ${v.min_value}` : '—'
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
      <span className={`badge ${ui.cls}`} style={{ minWidth: 22, textAlign: 'center' }}>{ui.icon}</span>
      <span style={{ flex: 1 }}>{v.label_vi}</span>
      <span style={{ color: 'var(--c-muted)' }}>
        {/* counted=null nghĩa là chưa cộng được gì — hiện "—", không hiện 0 */}
        {v.counted != null ? `${v.counted}${v.unit ? ' ' + v.unit : ''}` : '—'}
        <span style={{ opacity: 0.6 }}> / {gioiHan}</span>
      </span>
      <span style={{ fontSize: 11.5, color: 'var(--c-muted)', minWidth: 130, textAlign: 'right' }}>
        {ui.text}
      </span>
    </div>
  )
}

function ViolationRow({ v }: { v: Violation }) {
  return (
    <div style={{ fontSize: 13, lineHeight: 1.5 }}>
      <div style={{ display: 'flex', gap: 6, alignItems: 'flex-start' }}>
        <span className={`badge ${v.severity === 'hard' ? 'badge-hard' : 'badge-soft'}`}>
          {v.severity === 'hard' ? 'Chặn' : 'Lưu ý'}
        </span>
        <span>{v.message_vi}</span>
      </div>
      {v.suggestion && (
        <div style={{ color: 'var(--c-muted)', fontSize: 12.5, marginTop: 3, paddingLeft: 4 }}>
          → {v.suggestion}
        </div>
      )}
      {/* Chỉ hiện số khi THẬT SỰ có số. actual=null là cảnh báo định tính. */}
      {v.actual != null && v.limit != null && (
        <div style={{ color: 'var(--c-muted)', fontSize: 12, marginTop: 2, paddingLeft: 4 }}>
          {v.actual} / {v.limit} {v.unit}
        </div>
      )}
    </div>
  )
}
