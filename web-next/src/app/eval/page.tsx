'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { getSession } from '@/lib/auth'

interface EvalResult {
  case_id: string
  patient_label: string
  status: 'pass' | 'fail' | 'needs_expert'
  retry_count: number
  pass_on_first: boolean
  energy_error_pct: number
  hard_violations: number
  soft_violations: number
  sources_complete: boolean
  allergy_detected: boolean
  drug_interaction_detected: boolean
  plan_id: string | null
  error: string | null
}

interface EvalReport {
  run_at: string
  backend_url: string
  total_cases: number
  results: EvalResult[]
  summary: {
    rq1_m1_sources_complete_pct: number
    rq1_m2_pass_first_pct: number
    rq1_m3_pass_total_pct: number
    rq1_m4_energy_error_avg: number
    safe_m1_allergy_pct: number
    safe_m2_drug_pct: number
  }
}

const KPI = [
  { key: 'rq1_m1_sources_complete_pct', label: 'RQ1-M1: Nguồn dinh dưỡng đầy đủ', target: 100, unit: '%', desc: 'Mọi giá trị dinh dưỡng có nguồn hợp lệ' },
  { key: 'rq1_m2_pass_first_pct', label: 'RQ1-M2: Pass rule lần đầu', target: 70, unit: '%', desc: 'Thực đơn không cần retry' },
  { key: 'rq1_m3_pass_total_pct', label: 'RQ1-M3: Pass sau ≤3 lần', target: 95, unit: '%', desc: 'Sau tối đa 3 lần retry' },
  { key: 'safe_m1_allergy_pct', label: 'SAFE-M1: Phát hiện dị ứng', target: 100, unit: '%', desc: '100% ca dị ứng được chặn' },
  { key: 'safe_m2_drug_pct', label: 'SAFE-M2: Cảnh báo tương tác thuốc', target: 90, unit: '%', desc: 'Recall tương tác nghiêm trọng' },
]

export default function EvalPage() {
  const router = useRouter()
  const [report, setReport] = useState<EvalReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [noReport, setNoReport] = useState(false)

  useEffect(() => {
    const session = getSession()
    if (!session || (session.role !== 'dietitian' && session.role !== 'admin')) {
      router.replace('/login')
      return
    }
    // Load results.json nếu có
    fetch('/eval-results.json')
      .then(r => {
        if (!r.ok) throw new Error('no report')
        return r.json()
      })
      .then(setReport)
      .catch(() => setNoReport(true))
      .finally(() => setLoading(false))
  }, [router])

  const pct = (v: number) => `${v.toFixed(1)}%`

  return (
    <>
      <div className="topbar">
        <div><p className="page-kicker">Model & safety operations</p><h1 className="page-title">Chất lượng hệ thống</h1></div>
        <span className="synthetic-label">DỮ LIỆU MÔ PHỎNG</span>
      </div>
      <div className="page-body" style={{ maxWidth: 1200 }}>

      {loading ? (
        <div style={{ display: 'grid', placeItems: 'center', height: '40vh' }}>
          <span className="spinner" style={{ width: 32, height: 32, color: 'var(--c-green)' }} />
        </div>
      ) : noReport || !report ? (
        <div className="card" style={{ padding: 48, textAlign: 'center' }}>
          <div style={{ fontSize: 40, marginBottom: 16 }}>◫</div>
          <h2 style={{ fontFamily: 'var(--f-serif)', fontSize: 24, marginBottom: 8 }}>Chưa có báo cáo eval</h2>
          <p style={{ color: 'var(--c-muted)', maxWidth: 460, margin: '0 auto 24px', fontSize: 14, lineHeight: 1.6 }}>
            Chạy script eval để sinh kết quả thật. Script sẽ chạy 10 ca mô phỏng qua API và ghi kết quả vào file.
          </p>
          <div style={{ background: 'var(--c-surface)', border: '1px solid var(--c-border)', borderRadius: 'var(--r-md)', padding: '16px 20px', textAlign: 'left', maxWidth: 480, margin: '0 auto', fontFamily: 'var(--f-mono)', fontSize: 13 }}>
            <div style={{ color: 'var(--c-muted)', marginBottom: 6 }}># Chạy từ thư mục gốc dự án:</div>
            <div>python eval/scripts/run_eval.py \</div>
            <div style={{ paddingLeft: 16 }}>--backend http://localhost:8000 \</div>
            <div style={{ paddingLeft: 16 }}>--email dietitian1@nutricare.demo \</div>
            <div style={{ paddingLeft: 16 }}>--password Demo1234</div>
            <div style={{ marginTop: 10, color: 'var(--c-muted)' }}># Kết quả lưu tại: eval/results/report.md</div>
          </div>
          <p style={{ marginTop: 16, fontSize: 12, color: 'var(--c-muted)' }}>
            Sau khi chạy xong, copy <code>eval/results/results.json</code> vào <code>web-next/public/eval-results.json</code> để xem tại đây.
          </p>
        </div>
      ) : (
        <>
          {/* Header */}
          <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 24 }}>
            <div>
              <p style={{ fontSize: 12, color: 'var(--c-muted)' }}>
                Chạy lúc {new Date(report.run_at).toLocaleString('vi-VN')} · {report.total_cases} ca kiểm thử · {report.backend_url}
              </p>
            </div>
          </div>

          {/* KPI Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px,1fr))', gap: 16, marginBottom: 32 }}>
            {KPI.map(kpi => {
              const val = report.summary[kpi.key as keyof typeof report.summary]
              const pass = val >= kpi.target
              const pctVal = kpi.unit === '%' ? val : null
              return (
                <div key={kpi.key} className="card" style={{ borderTop: `3px solid ${pass ? 'var(--c-green2)' : 'var(--c-red)'}` }}>
                  <div className="card-body">
                    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 8 }}>
                      <span className={`badge ${pass ? 'badge-ok' : 'badge-hard'}`}>
                        {pass ? '✓ Pass' : '✗ Fail'}
                      </span>
                      <span style={{ fontFamily: 'var(--f-mono)', fontSize: 11, color: 'var(--c-muted)' }}>
                        target ≥{kpi.target}{kpi.unit}
                      </span>
                    </div>
                    <div style={{ fontFamily: 'var(--f-serif)', fontSize: 36, marginBottom: 4, color: pass ? 'var(--c-green)' : 'var(--c-red)' }}>
                      {pct(val)}
                    </div>
                    <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 4 }}>{kpi.label}</div>
                    <div style={{ fontSize: 12, color: 'var(--c-muted)' }}>{kpi.desc}</div>
                    {pctVal !== null && (
                      <div style={{ marginTop: 10 }}>
                        <div className="nutrition-bar-track">
                          <div
                            className="nutrition-bar-fill"
                            style={{ width: `${Math.min(pctVal, 100)}%`, background: pass ? 'var(--c-green2)' : 'var(--c-red)' }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>

          {/* Results table */}
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Chi tiết từng ca kiểm thử</h2>
            </div>
            <div className="table-wrap" style={{ border: 'none', borderTop: '1px solid var(--c-border)', borderRadius: 0 }}>
              <table>
                <thead>
                  <tr>
                    <th>Ca</th>
                    <th>Bệnh nhân</th>
                    <th>Kết quả</th>
                    <th>Pass lần đầu</th>
                    <th>Lần thử</th>
                    <th>Lỗi kcal</th>
                    <th>Vi phạm</th>
                    <th>Nguồn đủ</th>
                    <th>Dị ứng</th>
                    <th>Thuốc</th>
                  </tr>
                </thead>
                <tbody>
                  {report.results.map(r => (
                    <tr key={r.case_id}>
                      <td><span className="font-mono text-sm text-muted">{r.case_id}</span></td>
                      <td>{r.patient_label}</td>
                      <td>
                        <span className={`badge ${r.status === 'pass' ? 'badge-ok' : r.status === 'fail' ? 'badge-hard' : 'badge-soft'}`}>
                          {r.status === 'pass' ? '✓ Pass' : r.status === 'fail' ? '✗ Fail' : '⚑ Expert'}
                        </span>
                      </td>
                      <td>{r.pass_on_first ? <span className="badge badge-ok">✓</span> : <span className="badge badge-soft">✗</span>}</td>
                      <td><span className="font-mono">{r.retry_count}</span></td>
                      <td>
                        <span className={`font-mono ${Math.abs(r.energy_error_pct) > 10 ? 'text-muted' : ''}`} style={{ color: Math.abs(r.energy_error_pct) > 10 ? 'var(--c-red)' : undefined }}>
                          {r.energy_error_pct.toFixed(1)}%
                        </span>
                      </td>
                      <td>
                        {r.hard_violations > 0 && <span className="badge badge-hard" style={{ marginRight: 4 }}>{r.hard_violations} cứng</span>}
                        {r.soft_violations > 0 && <span className="badge badge-soft">{r.soft_violations} mềm</span>}
                        {r.hard_violations === 0 && r.soft_violations === 0 && <span className="badge badge-ok">✓</span>}
                      </td>
                      <td>{r.sources_complete ? <span className="badge badge-ok">✓</span> : <span className="badge badge-hard">✗</span>}</td>
                      <td>{r.allergy_detected !== null ? (r.allergy_detected ? <span className="badge badge-ok">✓</span> : <span className="badge badge-hard">✗</span>) : <span style={{ color: 'var(--c-muted)' }}>N/A</span>}</td>
                      <td>{r.drug_interaction_detected !== null ? (r.drug_interaction_detected ? <span className="badge badge-ok">✓</span> : <span className="badge badge-hard">✗</span>) : <span style={{ color: 'var(--c-muted)' }}>N/A</span>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <p className="disclaimer" style={{ marginTop: 20 }}>
            Kết quả eval trên {report.total_cases} ca dữ liệu mô phỏng. Không phản ánh hiệu quả lâm sàng trên bệnh nhân thật.
            Xem chi tiết tại <code>eval/results/report.md</code>.
          </p>
        </>
      )}
      </div>
    </>
  )
}
