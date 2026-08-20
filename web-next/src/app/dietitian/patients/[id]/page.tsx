'use client'

import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Icon } from '@/components/brand-artwork'
import {
  ApiError,
  createApiClient,
  type ClinicalNote,
  type FoodLog,
  type MealPlan,
  type PatientObservation,
  type PatientProfile,
  type ReviewEvent,
} from '@/lib/api'
import { getToken } from '@/lib/auth'
import { ACTIVITY_LABELS, CONDITION_LABELS, REGION_LABELS } from '@/lib/labels'

type Tab = 'overview' | 'clinical' | 'plans' | 'diary' | 'weekly' | 'notes' | 'history'

// FE-24: các class Tailwind dùng lặp lại nhiều nơi trong trang hồ sơ 360 — gom
// thành hằng số để tránh lặp chuỗi dài, tương đương việc dùng chung 1 class CSS
// module như bản cũ (.card, .list article, .icon chip...).
const CARD = 'rounded-2xl border border-[#d8e1e3] bg-white p-[21px] shadow-[0_11px_32px_rgba(24,77,76,.045)]'
const TWO_COL = 'grid grid-cols-[1.35fr_.8fr] gap-3.5 max-[1050px]:grid-cols-1'
const LIST_ROW = 'grid min-h-[68px] grid-cols-[38px_1fr_auto] items-center gap-2.5 border-b border-[#e3e8e9] px-1 py-2.5 last:border-0 max-[700px]:grid-cols-[38px_1fr] max-[700px]:[&>time]:col-start-2'
const ICON_CHIP = 'grid h-9 w-9 flex-none place-items-center rounded-[11px] bg-[#e3f0f4] text-[var(--c-green2)]'
const PRIMARY_LINK = 'mt-5 flex min-h-[42px] items-center justify-between rounded-lg bg-[var(--c-green)] px-[13px] text-[9px] font-extrabold text-white'
const BADGE_TONE:Record<string,string>={pending_review:'text-[#9a6517] bg-[#fff2d5]',approved:'text-[var(--c-green2)] bg-[#e4f0f4]',rejected:'text-[#a34230] bg-[#fff0ec]',failed:'text-[#a34230] bg-[#fff0ec]'}

const STATUS_LABELS: Record<string, string> = {
  drafting: 'Đang tạo', pending_review: 'Chờ duyệt', approved: 'Đã duyệt', rejected: 'Đã từ chối', failed: 'Thất bại',
}
const SLOT_LABELS: Record<string, string> = { breakfast: 'Bữa sáng', lunch: 'Bữa trưa', snack: 'Bữa phụ', dinner: 'Bữa tối' }

function recentDays() {
  const today = new Date()
  return Array.from({ length: 7 }, (_, index) => {
    const value = new Date(today)
    value.setDate(today.getDate() - index)
    return value.toISOString().slice(0, 10)
  })
}

export default function PatientDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [patient, setPatient] = useState<PatientProfile | null>(null)
  const [plans, setPlans] = useState<MealPlan[]>([])
  const [observations, setObservations] = useState<PatientObservation[]>([])
  const [notes, setNotes] = useState<ClinicalNote[]>([])
  const [reviewEvents, setReviewEvents] = useState<ReviewEvent[]>([])
  const [logs, setLogs] = useState<FoodLog[]>([])
  const [loading, setLoading] = useState(true)
  const [loadedExtras, setLoadedExtras] = useState<Record<string, boolean>>({})
  const [extraLoading, setExtraLoading] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [activeTab, setActiveTab] = useState<Tab>('overview')
  const [editing, setEditing] = useState(false)
  const [noteContent, setNoteContent] = useState('')
  const [savingNote, setSavingNote] = useState(false)

  const load = useCallback(async () => {
    const token = getToken()
    if (!token || !id) return
    setError('')
    try {
      const api = createApiClient(token)
      const [profile, history] = await Promise.all([api.getPatient(id), api.listMealPlans(id)])
      setPatient(profile)
      setPlans(history.items)
    } catch (value) {
      setError(value instanceof ApiError ? value.message : 'Không thể tải hồ sơ bệnh nhân.')
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => { const timer = window.setTimeout(() => void load(), 0); return () => window.clearTimeout(timer) }, [load])

  useEffect(() => {
    const key = activeTab === 'clinical' ? 'clinical' : activeTab === 'notes' ? 'notes' : activeTab === 'history' ? 'history' : activeTab === 'diary' || activeTab === 'weekly' ? 'logs' : ''
    const token = getToken()
    if (!key || !token || !id || loadedExtras[key]) return
    let cancelled = false
    const loadingTimer = window.setTimeout(() => { if (!cancelled) setExtraLoading(true) }, 0)
    const api = createApiClient(token)
    const task = key === 'clinical' ? api.listObservations(id).then(setObservations)
      : key === 'notes' ? api.listClinicalNotes(id).then(setNotes)
      : key === 'history' ? api.listPatientReviewEvents(id).then(setReviewEvents)
      : Promise.all(recentDays().map(day => api.listFoodLogs(id, day))).then(days => setLogs(days.flat()))
    void task.then(() => { if (!cancelled) setLoadedExtras(current => ({ ...current, [key]: true })) })
      .catch(value => { if (!cancelled) setError(value instanceof ApiError ? value.message : 'Không thể tải dữ liệu của mục này.') })
      .finally(() => { if (!cancelled) setExtraLoading(false) })
    return () => { cancelled = true; window.clearTimeout(loadingTimer) }
  }, [activeTab, id, loadedExtras])

  const latestPlan = useMemo(() => [...plans].sort((a, b) => b.plan_date.localeCompare(a.plan_date))[0], [plans])
  const activePlan = useMemo(() => [...plans].filter(plan => plan.status === 'approved').sort((a, b) => b.plan_date.localeCompare(a.plan_date))[0], [plans])
  const skipped = logs.filter(log => log.free_text_vi?.toLocaleLowerCase('vi-VN').startsWith('bỏ ')).length
  const unmatched = logs.filter(log => log.match_status === 'unmatched' && !log.free_text_vi?.toLocaleLowerCase('vi-VN').startsWith('bỏ ')).length

  async function handleCreateNote() {
    const token = getToken()
    if (!token || !noteContent.trim()) return
    setSavingNote(true)
    try {
      const note = await createApiClient(token).createClinicalNote(id, { note_type: 'follow_up', content: noteContent.trim(), visibility: 'care_team' })
      setNotes(current => [note, ...current])
      setNoteContent('')
      setNotice('Đã lưu ghi chú vào hồ sơ chăm sóc.')
    } catch (value) {
      setError(value instanceof ApiError ? value.message : 'Không thể lưu ghi chú.')
    } finally {
      setSavingNote(false)
    }
  }

  if (loading) return <PatientDetailSkeleton />
  if (!patient) return <div className="min-h-screen px-[38px] pt-8 pb-[50px] text-[var(--c-ink)]"><div className="mt-4 flex items-center gap-2 rounded-[11px] border border-[#efb3a2] bg-[#fff5f1] p-3 text-[9px] text-[#8f402c]"><Icon name="warning" className="w-[18px]"/>{error || 'Không tìm thấy hồ sơ.'}<button type="button" className="ml-auto font-bold" onClick={() => void load()}>Thử lại</button></div></div>

  const bmi = patient.weight_kg / (patient.height_cm / 100) ** 2

  return <div className="min-h-screen px-[38px] pt-8 pb-[50px] text-[var(--c-ink)] max-[700px]:px-[15px] max-[700px]:pt-[72px] max-[700px]:pb-[30px]">
    <header className="flex items-end justify-between gap-6 max-[700px]:grid max-[700px]:items-start">
      <div className="grid">
        <Link className="mb-3.5 flex w-fit items-center gap-1.5 text-[9px] font-bold text-[#195782]" href="/dietitian/patients"><Icon name="arrowLeft" className="w-[15px]"/>Danh sách bệnh nhân</Link>
        <small className="text-[8px] font-extrabold tracking-[.13em] text-[#0e5f95]">PATIENT 360 · #{patient.id.slice(0, 8)}</small>
        <h1 className="mt-[5px] font-[family-name:var(--f-serif)] text-[27px] font-semibold tracking-[-.01em]">{patient.sex === 'male' ? 'Nam' : 'Nữ'}, {patient.age} tuổi</h1>
        <p className="mt-[5px] text-[10px] text-[#657077]">{patient.conditions.map(item => CONDITION_LABELS[item.code] ?? item.code).join(' · ') || 'Chưa ghi nhận bệnh nền'} · BMI {bmi.toFixed(1)}</p>
      </div>
      <div className="flex gap-2 max-[700px]:grid max-[700px]:grid-cols-2">
        <button type="button" className="flex min-h-[43px] items-center gap-[7px] rounded-[10px] border border-[#cbd6da] px-3.5 text-[9px] font-extrabold" onClick={() => setEditing(true)}><Icon name="edit" className="w-[17px]"/>Chỉnh sửa hồ sơ</button>
        <Link className="flex min-h-[43px] items-center gap-[7px] rounded-[10px] border border-transparent bg-[linear-gradient(100deg,var(--c-green),#7ba2bb)] px-3.5 text-[9px] font-extrabold text-white" href={`/dietitian/meal-plans/new?profile_id=${patient.id}`}><Icon name="sparkles" className="w-[17px]"/>Tạo phương án</Link>
      </div>
    </header>

    {error && <div className="mt-4 flex items-center gap-2 rounded-[11px] border border-[#efb3a2] bg-[#fff5f1] p-3 text-[9px] text-[#8f402c]"><Icon name="warning" className="w-[18px]"/>{error}<button type="button" className="ml-auto font-bold" onClick={() => void load()}>Thử lại</button></div>}
    {notice && <div className="fixed top-[18px] right-[22px] z-[60] flex max-w-[560px] items-center gap-2 rounded-[11px] border-0 bg-[#145582] p-3 text-[9px] text-white shadow-[0_15px_40px_rgba(13,73,75,.22)]"><Icon name="check" className="w-[18px]"/>{notice}<button type="button" className="ml-auto font-bold" aria-label="Đóng" onClick={() => setNotice('')}><Icon name="close" className="w-[15px]"/></button></div>}

    <section className="mt-[22px] grid grid-cols-4 overflow-hidden rounded-2xl border border-[#d8e1e3] bg-white shadow-[0_12px_35px_rgba(20,80,78,.05)] max-[1050px]:grid-cols-2 max-[700px]:grid-cols-1">
      <article className="min-h-[105px] border-r border-[#e1e8e9] p-[17px] max-[700px]:border-r-0"><small className="text-[7px] font-extrabold text-[#0e5f95]">TRẠNG THÁI THEO DÕI</small><strong className="mt-2 block font-[family-name:var(--f-serif)] text-[19px]">Đang theo dõi</strong><span className="mt-[5px] block text-[8px] text-[#69747a]">Hồ sơ có thể dùng để lập phương án</span></article>
      <article className="min-h-[105px] border-r border-[#e1e8e9] p-[17px] max-[1050px]:border-r-0 max-[700px]:border-r-0"><small className="text-[7px] font-extrabold text-[#0e5f95]">THỰC ĐƠN ĐANG ÁP DỤNG</small><strong className="mt-2 block font-[family-name:var(--f-serif)] text-[19px]">{activePlan?.plan_date ? new Date(`${activePlan.plan_date}T00:00:00`).toLocaleDateString('vi-VN') : 'Chưa có'}</strong><span className="mt-[5px] block text-[8px] text-[#69747a]">{activePlan ? `#${activePlan.id.slice(0, 8)} · ${activePlan.items.length} món` : 'Chưa có bản được phát hành'}</span></article>
      <article className="min-h-[105px] border-r border-[#e1e8e9] p-[17px] max-[700px]:border-r-0"><small className="text-[7px] font-extrabold text-[#0e5f95]">BẢN GẦN NHẤT</small><strong className="mt-2 block font-[family-name:var(--f-serif)] text-[19px]">{latestPlan ? STATUS_LABELS[latestPlan.status] ?? latestPlan.status : 'Chưa có'}</strong><span className="mt-[5px] block text-[8px] text-[#69747a]">{latestPlan ? `${latestPlan.plan_date} · #${latestPlan.id.slice(0, 8)}` : 'Tạo phương án đầu tiên'}</span></article>
      <article className="min-h-[105px] p-[17px]"><small className="text-[7px] font-extrabold text-[#0e5f95]">7 NGÀY GẦN NHẤT</small><strong className="mt-2 block font-[family-name:var(--f-serif)] text-[19px]">{loadedExtras.logs ? `${logs.length} ghi nhận` : 'Tải khi cần'}</strong><span className="mt-[5px] block text-[8px] text-[#69747a]">{loadedExtras.logs ? `${skipped} bỏ bữa · ${unmatched} món cần đối chiếu` : 'Mở Nhật ký hoặc Báo cáo tuần'}</span></article>
    </section>

    <nav className="my-[18px] mt-[18px] mb-[13px] flex gap-[3px] overflow-auto rounded-[11px] bg-[#e9f1f2] p-1" aria-label="Nội dung hồ sơ">
      {([['overview','Tổng quan'],['clinical','Lâm sàng'],['plans','Thực đơn'],['diary','Nhật ký'],['weekly','Báo cáo tuần'],['notes','Ghi chú'],['history','Lịch sử']] as Array<[Tab,string]>).map(([value,label]) => <button type="button" key={value} className={`min-h-9 whitespace-nowrap rounded-lg px-3.5 text-[9px] font-bold ${activeTab===value?'bg-white text-[var(--c-green2)] shadow-[0_4px_12px_rgba(22,85,83,.08)]':'text-[#647077]'}`} onClick={() => setActiveTab(value)}>{label}</button>)}
    </nav>

    {activeTab === 'overview' && <Overview patient={patient} activePlan={activePlan} />}
    {extraLoading && <TabLoading />}
    {!extraLoading && activeTab === 'clinical' && <Clinical patient={patient} observations={observations} />}
    {activeTab === 'plans' && <Plans plans={plans} />}
    {!extraLoading && activeTab === 'diary' && <Diary logs={logs} />}
    {!extraLoading && activeTab === 'weekly' && <Weekly logs={logs} skipped={skipped} unmatched={unmatched} />}
    {!extraLoading && activeTab === 'notes' && <Notes notes={notes} value={noteContent} saving={savingNote} onChange={setNoteContent} onSave={() => void handleCreateNote()} />}
    {!extraLoading && activeTab === 'history' && <History events={reviewEvents} />}
    {editing && <EditPatientModal patient={patient} onClose={() => setEditing(false)} onSaved={updated => { setPatient(updated); setEditing(false); setNotice('Đã cập nhật hồ sơ. Thuốc, dị ứng, bệnh nền hoặc chỉ số thay đổi cần được kiểm tra lại trước lần phát hành tiếp theo.') }} />}
  </div>
}

function Overview({patient,activePlan}:{patient:PatientProfile;activePlan?:MealPlan}) {
  return <div className={TWO_COL}>
    <section className={CARD}><CardTitle eyebrow="THÔNG TIN CỐT LÕI" title="Dữ liệu đang được sử dụng"/>
      <dl className="mt-3 grid grid-cols-2 max-[700px]:grid-cols-1">
        <div className="min-h-[61px] border-b border-[#e5eaeb] px-2 py-3"><dt className="text-[8px] text-[#6a757c]">Chiều cao</dt><dd className="mt-[5px] text-[10px] font-extrabold">{patient.height_cm} cm</dd></div>
        <div className="min-h-[61px] border-b border-[#e5eaeb] px-2 py-3"><dt className="text-[8px] text-[#6a757c]">Cân nặng</dt><dd className="mt-[5px] text-[10px] font-extrabold">{patient.weight_kg} kg</dd></div>
        <div className="min-h-[61px] border-b border-[#e5eaeb] px-2 py-3"><dt className="text-[8px] text-[#6a757c]">Hoạt động</dt><dd className="mt-[5px] text-[10px] font-extrabold">{ACTIVITY_LABELS[patient.activity_level] ?? patient.activity_level}</dd></div>
        <div className="min-h-[61px] border-b border-[#e5eaeb] px-2 py-3"><dt className="text-[8px] text-[#6a757c]">Vùng miền</dt><dd className="mt-[5px] text-[10px] font-extrabold">{patient.region ? `Miền ${REGION_LABELS[patient.region] ?? patient.region}` : 'Chưa cập nhật'}</dd></div>
        <div className="min-h-[61px] border-b border-[#e5eaeb] px-2 py-3"><dt className="text-[8px] text-[#6a757c]">Dị ứng</dt><dd className="mt-[5px] text-[10px] font-extrabold">{patient.allergies.join(', ') || 'Không ghi nhận'}</dd></div>
        <div className="min-h-[61px] border-b border-[#e5eaeb] px-2 py-3"><dt className="text-[8px] text-[#6a757c]">Thuốc</dt><dd className="mt-[5px] text-[10px] font-extrabold">{patient.medications.join(', ') || 'Không ghi nhận'}</dd></div>
      </dl>
    </section>
    <aside className={CARD}><CardTitle eyebrow="ĐƯỜNG ĐI TIẾP THEO" title="Thực đơn và an toàn"/>
      <div className="mt-[18px] flex gap-[11px]"><span className={ICON_CHIP}><Icon name={activePlan?'check':'info'}/></span><div><strong className="text-[11px]">{activePlan?'Đã có thực đơn đang áp dụng':'Chưa có thực đơn được phát hành'}</strong><p className="mt-1.5 text-[9px] leading-[1.6] text-[#68737a]">{activePlan?'Người bệnh chỉ nhìn thấy phiên bản đã được duyệt.':'Tạo phương án mới sau khi hồ sơ lâm sàng đã đủ dữ liệu.'}</p></div></div>
      <Link className={PRIMARY_LINK} href={`/dietitian/meal-plans/new?profile_id=${patient.id}`}>Tạo phương án thực đơn<Icon name="arrowRight" className="w-4"/></Link>
    </aside>
  </div>
}

function Clinical({patient,observations}:{patient:PatientProfile;observations:PatientObservation[]}) {
  const weightPoints = useMemo(() => [...observations]
    .filter(item => item.observation_type === 'weight')
    .sort((a, b) => a.measured_at.localeCompare(b.measured_at))
    .map(item => ({ date: item.measured_at.slice(0, 10), value: item.value })), [observations])

  return <div className={TWO_COL}>
    <section className={CARD}><CardTitle eyebrow="AN TOÀN LÂM SÀNG" title="Bệnh nền, thuốc và dị ứng"/>
      <DataGroup title="Bệnh lý" values={patient.conditions.map(item => `${CONDITION_LABELS[item.code] ?? item.code}${item.stage ? ` · ${item.stage}` : ''}`)}/>
      <DataGroup title="Thuốc đang dùng" values={patient.medications}/>
      <DataGroup title="Dị ứng" values={patient.allergies}/>
      <div className="mt-5 flex gap-2 rounded-[10px] border border-[#efc486] bg-[#fff8ea] p-3 text-[8px] leading-[1.5] text-[#8a5a18]"><Icon name="warning" className="w-[18px] flex-none"/>Thay đổi các dữ liệu này có thể làm quyết định duyệt cũ không còn phù hợp.</div>
    </section>
    <section className={CARD}>
      <CardTitle eyebrow="DÒNG THỜI GIAN" title="Chỉ số và diễn biến"/>
      {weightPoints.length > 1 && <div className="mt-3 h-[160px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={weightPoints} margin={{ left: -20, right: 8, top: 4, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e3e9ea" />
            <XAxis dataKey="date" tick={{ fontSize: 8 }} tickFormatter={d => d.slice(5)} />
            <YAxis tick={{ fontSize: 8 }} domain={['dataMin - 2', 'dataMax + 2']} />
            <Tooltip formatter={(v) => [`${v} kg`, 'Cân nặng']} labelFormatter={d => new Date(`${d}T00:00:00`).toLocaleDateString('vi-VN')} />
            <Line type="monotone" dataKey="value" stroke="var(--c-carb)" strokeWidth={2} dot={{ r: 3 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>}
      <div className="mt-3 grid">{observations.length ? observations.map(item => <article key={item.id} className={LIST_ROW}><span className={ICON_CHIP}><Icon name="trend"/></span><div><strong className="text-[10px]">{item.observation_type.toUpperCase()} · {item.value} {item.unit}</strong><p className="mt-1 block text-[8px] text-[#68737a]">{item.source === 'patient_reported' ? 'Bệnh nhân tự báo cáo' : item.source}{item.note ? ` · ${item.note}` : ''}</p></div><time className="text-[8px] text-[#737d83]">{new Date(item.measured_at).toLocaleDateString('vi-VN')}</time></article>) : <Empty text="Chưa có chỉ số được ghi theo thời gian."/>}</div>
    </section>
  </div>
}

function Plans({plans}:{plans:MealPlan[]}) {
  return <section className={CARD}><CardTitle eyebrow="TẤT CẢ PHIÊN BẢN" title="Lịch sử thực đơn"/>
    <div className="mt-3 grid">{plans.length ? [...plans].sort((a,b)=>b.plan_date.localeCompare(a.plan_date)).map(plan => <Link href={`/dietitian/reviews/${plan.id}`} key={plan.id} className="grid min-h-[68px] grid-cols-[104px_1fr_20px] items-center gap-2.5 border-b border-[#e3e8e9] py-2.5 last:border-0 max-[700px]:grid-cols-[1fr_20px]"><span className={`w-fit rounded-full px-2 py-1.5 text-center text-[8px] font-bold max-[700px]:col-span-full ${BADGE_TONE[plan.status]??''}`}>{STATUS_LABELS[plan.status] ?? plan.status}</span><div><strong className="text-[10px]">{new Date(`${plan.plan_date}T00:00:00`).toLocaleDateString('vi-VN')}</strong><small className="mt-1 block text-[8px] text-[#68737a]">#{plan.id.slice(0,8)} · {plan.items.length} món · phiên bản {plan.menu_version}</small></div><Icon name="chevronRight" className="w-[17px] text-[var(--c-green2)]"/></Link>) : <Empty text="Hồ sơ này chưa có thực đơn."/>}</div>
  </section>
}

function Diary({logs}:{logs:FoodLog[]}) {
  return <section className={CARD}><CardTitle eyebrow="7 NGÀY GẦN NHẤT" title="Nhật ký ăn uống"/>
    <div className="mt-3 grid">{logs.length ? [...logs].sort((a,b)=>b.logged_at.localeCompare(a.logged_at)).map(log => { const unresolved = log.match_status === 'unmatched' || log.match_status === 'no_data'; return <article key={log.id} className={LIST_ROW}><span className={ICON_CHIP}><Icon name="diary"/></span><div><strong className="text-[10px]">{log.free_text_vi || 'Ghi nhận bữa ăn'}</strong><small className="mt-1 block text-[8px] text-[#68737a]">{SLOT_LABELS[log.slot ?? ''] ?? 'Chưa rõ bữa'} · {log.grams ? `${Math.round(log.grams)} g` : 'không có gram'} · {unresolved ? 'Chờ đối chiếu' : 'Đã tra được'}</small></div><time className="text-[8px] text-[#737d83]">{new Date(log.logged_at).toLocaleString('vi-VN')}</time></article> }) : <Empty text="Người bệnh chưa có ghi nhận trong 7 ngày gần nhất."/>}</div>
  </section>
}

function Weekly({logs,skipped,unmatched}:{logs:FoodLog[];skipped:number;unmatched:number}) {
  const activeDays = new Set(logs.map(log => log.logged_at.slice(0,10))).size
  return <div className={TWO_COL}>
    <section className={CARD}><CardTitle eyebrow="TÓM TẮT NGOẠI LỆ" title="Điểm cần chuyên gia chú ý"/>
      <div className="mt-[18px] grid grid-cols-3 gap-2 max-[700px]:grid-cols-1">
        <article className="grid min-h-[92px] content-center rounded-[11px] border border-[#dce4e5] p-3.5"><strong className="font-[family-name:var(--f-serif)] text-[25px]">{activeDays}/7</strong><span className="mt-1 text-[8px] text-[#68737a]">ngày có dữ liệu</span></article>
        <article className="grid min-h-[92px] content-center rounded-[11px] border border-[#dce4e5] p-3.5"><strong className="font-[family-name:var(--f-serif)] text-[25px]">{skipped}</strong><span className="mt-1 text-[8px] text-[#68737a]">bữa được báo bỏ</span></article>
        <article className="grid min-h-[92px] content-center rounded-[11px] border border-[#dce4e5] p-3.5"><strong className="font-[family-name:var(--f-serif)] text-[25px]">{unmatched}</strong><span className="mt-1 text-[8px] text-[#68737a]">món cần đối chiếu</span></article>
      </div>
      <div className="mt-5 flex gap-2 rounded-[10px] border border-[#efc486] bg-[#fff8ea] p-3 text-[8px] leading-[1.5] text-[#8a5a18]"><Icon name="info" className="w-[18px] flex-none"/>Đây là tóm tắt từ dữ liệu hiện có, chưa phải báo cáo lâm sàng tự động đầy đủ.</div>
    </section>
    <aside className={CARD}><CardTitle eyebrow="HÀNH ĐỘNG" title="Theo dõi theo ngoại lệ"/>
      <p className="mt-1.5 text-[9px] leading-[1.6] text-[#68737a]">{skipped || unmatched ? 'Hồ sơ đang có dữ liệu cần xem. Chuyên gia có thể đối chiếu món hoặc ghi nhận hướng theo dõi ở tab Ghi chú.' : 'Chưa phát hiện ngoại lệ từ nhật ký hiện có. Không cần mở từng bữa để duyệt lại.'}</p>
      <Link className={PRIMARY_LINK} href="/dietitian/food-logs">Mở trung tâm theo dõi tuần<Icon name="arrowRight" className="w-4"/></Link>
    </aside>
  </div>
}

const NOTE_TYPE_LABELS: Record<string, string> = { follow_up: 'Theo dõi' }
const VISIBILITY_LABELS: Record<string, string> = { care_team: 'Nhóm chăm sóc' }
function Notes({notes,value,saving,onChange,onSave}:{notes:ClinicalNote[];value:string;saving:boolean;onChange:(value:string)=>void;onSave:()=>void}) {
  return <section className={CARD}><CardTitle eyebrow="NHÓM CHĂM SÓC" title="Ghi chú chuyên gia"/>
    <div className="mt-4 grid gap-2">
      <textarea className="min-h-[100px] resize-y rounded-[10px] border border-[#ccd7da] p-3 text-[10px] outline-none" value={value} onChange={event=>onChange(event.target.value)} placeholder="Đánh giá, mục tiêu hoặc nội dung cần theo dõi…"/>
      <button type="button" className="ml-auto w-fit rounded-lg bg-[var(--c-green)] px-3.5 py-2.5 text-[9px] font-bold text-white disabled:cursor-not-allowed disabled:opacity-50" disabled={saving || value.trim().length < 3} onClick={onSave}>{saving?'Đang lưu…':'Lưu ghi chú'}</button>
    </div>
    <div className="mt-3 grid">{notes.length ? notes.map(note=><article key={note.id} className="mt-2.5 rounded-[11px] border border-[#e0e7e8] p-3.5"><header className="flex justify-between"><strong className="text-[9px]">{NOTE_TYPE_LABELS[note.note_type] ?? note.note_type}</strong><time className="text-[8px] text-[#717b81]">{new Date(note.created_at).toLocaleString('vi-VN')}</time></header><p className="my-2 text-[10px] leading-[1.55]">{note.content}</p><small className="text-[8px] text-[#717b81]">{VISIBILITY_LABELS[note.visibility] ?? note.visibility} · phiên bản {note.version}</small></article>) : <Empty text="Chưa có ghi chú chăm sóc."/>}</div>
  </section>
}

function History({events}:{events:ReviewEvent[]}) {
  return <section className={CARD}><CardTitle eyebrow="NHẬT KÝ QUYẾT ĐỊNH" title="Lịch sử quyết định"/>
    <div className="mt-3 grid">{events.length ? events.map(event=><Link href={`/dietitian/reviews/${event.meal_plan_id}`} key={event.id} className={LIST_ROW}><span className={ICON_CHIP}><Icon name={event.decision==='approved'?'check':'close'}/></span><div><strong className="text-[10px]">{event.decision==='approved'?'Đã duyệt':'Đã từ chối'} · phiên bản {event.menu_version}</strong><p className="mt-1 text-[8px] text-[#68737a]">{event.notes || event.reason || 'Không có ghi chú'}</p></div><time className="text-[8px] text-[#737d83]">{new Date(event.created_at).toLocaleString('vi-VN')}</time></Link>) : <Empty text="Chưa có quyết định duyệt được ghi nhận."/>}</div>
  </section>
}

function EditPatientModal({patient,onClose,onSaved}:{patient:PatientProfile;onClose:()=>void;onSaved:(patient:PatientProfile)=>void}) {
  const [form,setForm]=useState<{age:string;height:string;weight:string;activity:string;region:string;conditions:string;medications:string;allergies:string}>({age:String(patient.age),height:String(patient.height_cm),weight:String(patient.weight_kg),activity:patient.activity_level,region:patient.region??'',conditions:patient.conditions.map(item=>item.code).join(', '),medications:patient.medications.join(', '),allergies:patient.allergies.join(', ')})
  const [saving,setSaving]=useState(false)
  const [error,setError]=useState('')
  const split=(value:string)=>value.split(',').map(item=>item.trim()).filter(Boolean)
  async function save(){const token=getToken();if(!token)return;setSaving(true);setError('');try{const conditionCodes=split(form.conditions);const updated=await createApiClient(token).updatePatient(patient.id,{age:Number(form.age),height_cm:Number(form.height),weight_kg:Number(form.weight),activity_level:form.activity as PatientProfile['activity_level'],region:(form.region||null) as PatientProfile['region'],conditions:conditionCodes.map(code=>({code,stage:patient.conditions.find(item=>item.code===code)?.stage??null})),medications:split(form.medications),allergies:split(form.allergies)});onSaved(updated)}catch(value){setError(value instanceof ApiError?value.message:'Không thể cập nhật hồ sơ.')}finally{setSaving(false)}}
  const fieldInput = '[&_input]:h-[41px] [&_input]:rounded-[9px] [&_input]:border [&_input]:border-[#cbd6d9] [&_input]:bg-white [&_input]:px-2.5 [&_input]:text-[9px] [&_input]:outline-none [&_select]:h-[41px] [&_select]:rounded-[9px] [&_select]:border [&_select]:border-[#cbd6d9] [&_select]:bg-white [&_select]:px-2.5 [&_select]:text-[9px] [&_select]:outline-none'
  return <div className="fixed inset-0 z-[100]" role="dialog" aria-modal="true" aria-label="Chỉnh sửa hồ sơ">
    <button className="absolute inset-0 h-full w-full bg-[rgba(13,46,47,.5)] backdrop-blur-[3px]" type="button" onClick={onClose} aria-label="Đóng"/>
    <form className="absolute top-1/2 left-1/2 max-h-[calc(100vh-28px)] w-[min(700px,calc(100vw-28px))] -translate-x-1/2 -translate-y-1/2 overflow-auto rounded-[18px] bg-[#fbfdfd] p-[22px] shadow-[0_30px_90px_rgba(10,50,51,.28)]" onSubmit={event=>{event.preventDefault();void save()}}>
      <header className="flex justify-between gap-5">
        <div><small className="text-[8px] font-extrabold tracking-[.13em] text-[#0e5f95]">CHỈNH SỬA CÓ KIỂM SOÁT</small><h2 className="mt-1 font-[family-name:var(--f-serif)] text-[19px] font-semibold">Cập nhật hồ sơ</h2><p className="mt-[5px] text-[9px] text-[#677279]">Thay đổi lâm sàng quan trọng cần được kiểm tra lại trước lần phát hành tiếp theo.</p></div>
        <button type="button" className="grid h-[35px] w-[35px] place-items-center rounded-lg bg-[#edf2f4]" onClick={onClose} aria-label="Đóng"><Icon name="close" className="w-[17px]"/></button>
      </header>
      {error&&<div className="mt-3.5 rounded-lg bg-[#fff1ec] p-2.5 text-[9px] text-[#9a402e]">{error}</div>}
      <div className={`mt-[18px] grid grid-cols-2 gap-[11px] max-[700px]:grid-cols-1 ${fieldInput}`}>
        <label className="grid gap-1.5 text-[8px] font-bold">Tuổi<input required type="number" min="1" max="120" value={form.age} onChange={e=>setForm({...form,age:e.target.value})}/></label>
        <label className="grid gap-1.5 text-[8px] font-bold">Chiều cao (cm)<input required type="number" min="50" max="250" value={form.height} onChange={e=>setForm({...form,height:e.target.value})}/></label>
        <label className="grid gap-1.5 text-[8px] font-bold">Cân nặng (kg)<input required type="number" min="10" max="500" step="0.1" value={form.weight} onChange={e=>setForm({...form,weight:e.target.value})}/></label>
        <label className="grid gap-1.5 text-[8px] font-bold">Mức hoạt động<select value={form.activity} onChange={e=>setForm({...form,activity:e.target.value})}><option value="light">Nhẹ</option><option value="moderate">Trung bình</option><option value="heavy">Nặng</option><option value="very_heavy">Rất nặng</option></select></label>
        <label className="grid gap-1.5 text-[8px] font-bold">Vùng miền<select value={form.region} onChange={e=>setForm({...form,region:e.target.value})}><option value="">Chưa cập nhật</option><option value="north">Miền Bắc</option><option value="central">Miền Trung</option><option value="south">Miền Nam</option></select></label>
        <label className="col-span-full grid gap-1.5 text-[8px] font-bold max-[700px]:col-auto">Mã bệnh lý, cách nhau bằng dấu phẩy<input value={form.conditions} onChange={e=>setForm({...form,conditions:e.target.value})}/></label>
        <label className="col-span-full grid gap-1.5 text-[8px] font-bold max-[700px]:col-auto">Thuốc đang dùng, cách nhau bằng dấu phẩy<input value={form.medications} onChange={e=>setForm({...form,medications:e.target.value})}/></label>
        <label className="col-span-full grid gap-1.5 text-[8px] font-bold max-[700px]:col-auto">Dị ứng, cách nhau bằng dấu phẩy<input value={form.allergies} onChange={e=>setForm({...form,allergies:e.target.value})}/></label>
      </div>
      <footer className="sticky bottom-[-22px] mx-[-22px] mt-5 mb-[-22px] flex justify-end gap-2 border-t border-[#dce2e4] bg-[rgba(251,253,252,.96)] px-[22px] py-3.5">
        <button type="button" className="min-h-[39px] rounded-[9px] border border-[#cbd6d9] px-3.5 text-[9px] font-bold" onClick={onClose}>Hủy</button>
        <button type="submit" className="min-h-[39px] rounded-[9px] border-0 bg-[var(--c-green)] px-3.5 text-[9px] font-bold text-white" disabled={saving}>{saving?'Đang lưu…':'Lưu thay đổi'}</button>
      </footer>
    </form>
  </div>
}

function CardTitle({eyebrow,title}:{eyebrow:string;title:string}) { return <div className="border-b border-[#e2e7e9] pb-4"><small className="text-[8px] font-extrabold tracking-[.13em] text-[#0e5f95]">{eyebrow}</small><h2 className="mt-1 font-[family-name:var(--f-serif)] text-[16.5px] font-semibold">{title}</h2></div> }
function DataGroup({title,values}:{title:string;values:string[]}) { return <div className="mt-[18px]"><h3 className="text-[10px]">{title}</h3><div className="mt-2 flex flex-wrap gap-1.5">{values.length?values.map(value=><span key={value} className="rounded-full bg-[#e5f0f4] px-2 py-1.5 text-[8px] font-bold text-[var(--c-green2)]">{value}</span>):<span className="rounded-full bg-[#e5f0f4] px-2 py-1.5 text-[8px] font-bold text-[var(--c-green2)]">Chưa ghi nhận</span>}</div></div> }
function Empty({text}:{text:string}) { return <div className="grid min-h-[170px] content-center place-items-center text-center text-[#68737a]"><Icon name="info" className="mb-2.5 w-[31px] text-[var(--c-green2)]"/><p className="text-[9px]">{text}</p></div> }
function TabLoading(){return <section className={CARD}><div className="grid min-h-[170px] content-center place-items-center text-center text-[#68737a]"><Icon name="clock" className="mb-2.5 w-[31px] text-[var(--c-green2)]"/><p className="text-[9px]">Đang tải dữ liệu của mục này…</p></div></section>}
function PatientDetailSkeleton(){return <div className="min-h-screen px-[38px] pt-8 pb-[50px] text-[var(--c-ink)]"><div className="h-[90px] animate-[skeleton-pulse_1.3s_infinite] rounded-2xl bg-[linear-gradient(90deg,#e7eeef,#f8fafa,#e7eeef)] bg-[length:200%_100%]"/><div className="mt-[22px] h-[105px] animate-[skeleton-pulse_1.3s_infinite] rounded-2xl bg-[linear-gradient(90deg,#e7eeef,#f8fafa,#e7eeef)] bg-[length:200%_100%]"/><div className="mt-[65px] h-[420px] animate-[skeleton-pulse_1.3s_infinite] rounded-2xl bg-[linear-gradient(90deg,#e7eeef,#f8fafa,#e7eeef)] bg-[length:200%_100%]"/></div>}
