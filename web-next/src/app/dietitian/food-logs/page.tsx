'use client'
import { useCallback, useEffect, useState } from 'react'
import { createApiClient, type FoodLog } from '@/lib/api'
import { getToken } from '@/lib/auth'

const SLOT_LABELS: Record<string, string> = {
  breakfast: 'Sáng',
  lunch: 'Trưa',
  dinner: 'Tối',
  snack: 'Phụ',
}

/**
 * Hàng chờ giải quyết món chưa tra được.
 *
 * Đây là chỗ chuyên gia đóng vòng lặp: bệnh nhân ghi món bằng ngôn ngữ của họ,
 * hệ thống không đoán bừa, và chuyên gia quyết. Mỗi lần giải quyết là một lần
 * dữ liệu tốt lên.
 */
export default function DietitianFoodLogsPage() {
  const [rows, setRows] = useState<FoodLog[]>([])
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    const token = getToken()
    if (!token) return
    try {
      setRows(await createApiClient(token).listUnresolvedLogs())
    } catch (e) {
      setError((e as Error).message)
    }
  }, [])

  useEffect(() => {
    // Bọc trong hàm async rồi mới gọi: gọi thẳng `refresh()` ở thân effect bị
    // react-hooks/set-state-in-effect chặn (cascading render).
    let huy = false
    async function tai() {
      await refresh()
      if (!huy) setLoading(false)
    }
    void tai()
    return () => {
      huy = true
    }
  }, [refresh])

  async function resolve(
    logId: string,
    body: { action: 'map_to_existing' | 'mark_no_data'; food_id?: number; grams?: number }
  ) {
    setBusyId(logId)
    setError(null)
    try {
      await createApiClient(getToken()!).resolveFoodLog(logId, body)
      await refresh()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusyId(null)
    }
  }

  return (
    <>
      <div className="topbar">
        <h1 className="page-title">Món chờ đối chiếu</h1>
        <div className="topbar-actions">
          <span style={{ fontSize: 13, color: 'var(--c-muted)' }}>{rows.length} dòng</span>
        </div>
      </div>

      <div className="page-body">
        <div className="disclaimer" style={{ marginBottom: 16 }}>
          Các món bệnh nhân đã ghi mà hệ thống chưa tra được. Chúng <strong>không</strong> được tính
          vào tổng dinh dưỡng cho tới khi bạn xử lý. Nếu không đủ thông tin để tra, chọn
          <strong> “Không đủ dữ liệu”</strong> — đó là câu trả lời hợp lệ, tốt hơn là đoán.
        </div>

        {error && (
          <p style={{ color: 'var(--c-red)', fontSize: 13, marginBottom: 12 }}>{error}</p>
        )}

        {loading ? (
          <div style={{ display: 'grid', placeItems: 'center', height: '40vh' }}>
            <span className="spinner" style={{ width: 32, height: 32, color: 'var(--c-green)' }} />
          </div>
        ) : rows.length === 0 ? (
          <div className="card" style={{ padding: 60, textAlign: 'center' }}>
            <div style={{ fontSize: 44, marginBottom: 12 }}>✓</div>
            <h2 style={{ fontFamily: 'var(--f-serif)', fontSize: 22, marginBottom: 6 }}>
              Không còn món nào chờ xử lý
            </h2>
            <p style={{ color: 'var(--c-muted)' }}>
              Mọi món bệnh nhân ghi đều đã tra được hoặc đã được bạn xử lý.
            </p>
          </div>
        ) : (
          <div style={{ display: 'grid', gap: 12 }}>
            {rows.map(row => (
              <UnresolvedRow
                key={row.id}
                row={row}
                busy={busyId === row.id}
                onResolve={resolve}
              />
            ))}
          </div>
        )}
      </div>
    </>
  )
}

function UnresolvedRow({
  row,
  busy,
  onResolve,
}: {
  row: FoodLog
  busy: boolean
  onResolve: (
    logId: string,
    body: { action: 'map_to_existing' | 'mark_no_data'; food_id?: number; grams?: number }
  ) => void
}) {
  const [grams, setGrams] = useState<string>(row.grams != null ? String(row.grams) : '')
  const [chosen, setChosen] = useState<number | null>(row.suggestions[0]?.food_id ?? null)

  const thieuGram = !grams || Number(grams) <= 0

  return (
    <div className="card" style={{ padding: 16 }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginBottom: 10 }}>
        <span style={{ fontFamily: 'var(--f-serif)', fontSize: 17 }}>
          “{row.free_text_vi}”
        </span>
        <span className="badge badge-draft">{SLOT_LABELS[row.slot ?? ''] ?? '—'}</span>
        <span style={{ fontSize: 12.5, color: 'var(--c-muted)', marginLeft: 'auto' }}>
          {new Date(row.logged_at).toLocaleString('vi-VN')}
        </span>
      </div>

      {row.suggestions.length > 0 ? (
        <div style={{ display: 'grid', gap: 6, marginBottom: 12 }}>
          <span style={{ fontSize: 12.5, color: 'var(--c-muted)' }}>
            Hệ thống gợi ý (điểm càng cao càng giống, nhưng bạn là người quyết):
          </span>
          {row.suggestions.slice(0, 5).map(s => (
            <label
              key={s.food_id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                fontSize: 13.5,
                padding: '6px 10px',
                borderRadius: 'var(--r-sm, 6px)',
                border: '1px solid var(--c-border)',
                cursor: 'pointer',
                background: chosen === s.food_id ? 'rgba(0,0,0,.03)' : 'transparent',
              }}
            >
              <input
                type="radio"
                name={`sug-${row.id}`}
                checked={chosen === s.food_id}
                onChange={() => setChosen(s.food_id)}
              />
              <span style={{ flex: 1 }}>{s.name_vi}</span>
              <span style={{ fontSize: 12, color: 'var(--c-muted)' }}>
                {s.matched_on} · {(s.score * 100).toFixed(0)}%
              </span>
            </label>
          ))}
        </div>
      ) : (
        <p style={{ fontSize: 13, color: 'var(--c-muted)', marginBottom: 12 }}>
          Không có ứng viên nào đủ gần để gợi ý — cần bổ sung thực phẩm này vào cơ sở dữ liệu,
          hoặc đánh dấu không đủ dữ liệu.
        </p>
      )}

      <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
        <input
          className="input"
          type="number"
          placeholder="gram"
          value={grams}
          onChange={e => setGrams(e.target.value)}
          style={{ width: 110 }}
          min={1}
          max={5000}
        />
        <button
          className="btn btn-primary"
          disabled={busy || chosen == null || thieuGram}
          onClick={() =>
            onResolve(row.id, {
              action: 'map_to_existing',
              food_id: chosen!,
              grams: Number(grams),
            })
          }
          title={thieuGram ? 'Không có gram thì không tính vào tổng được' : undefined}
        >
          {busy ? 'Đang lưu…' : 'Gán món này'}
        </button>
        <button
          className="btn"
          disabled={busy}
          onClick={() => onResolve(row.id, { action: 'mark_no_data' })}
        >
          Không đủ dữ liệu
        </button>
        {thieuGram && chosen != null && (
          <span style={{ fontSize: 12, color: 'var(--c-muted)' }}>
            Cần nhập gram — không có số thì không cộng vào tổng được.
          </span>
        )}
      </div>
    </div>
  )
}
