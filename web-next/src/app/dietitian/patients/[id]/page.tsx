'use client'

import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useCallback, useEffect, useMemo, useState } from 'react'
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
import styles from './patient-detail.module.css'

type Tab = 'overview' | 'clinical' | 'plans' | 'diary' | 'weekly' | 'notes' | 'history'

const CONDITION_LABELS: Record<string, string> = {
  T2DM: 'Đái tháo đường type 2', HTN: 'Tăng huyết áp', CKD: 'Bệnh thận mạn', GOUT: 'Gout',
}
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
  if (!patient) return <div className={styles.page}><div className={styles.error}><Icon name="warning" />{error || 'Không tìm thấy hồ sơ.'}<button type="button" onClick={() => void load()}>Thử lại</button></div></div>

  const bmi = patient.weight_kg / (patient.height_cm / 100) ** 2

  return <div className={styles.page}>
    <header className={styles.header}>
      <div><Link href="/dietitian/patients"><Icon name="arrowLeft" />Danh sách bệnh nhân</Link><small>PATIENT 360 · #{patient.id.slice(0, 8)}</small><h1>{patient.sex === 'male' ? 'Nam' : 'Nữ'}, {patient.age} tuổi</h1><p>{patient.conditions.map(item => CONDITION_LABELS[item.code] ?? item.code).join(' · ') || 'Chưa ghi nhận bệnh nền'} · BMI {bmi.toFixed(1)}</p></div>
      <div className={styles.headerActions}><button type="button" onClick={() => setEditing(true)}><Icon name="edit" />Chỉnh sửa hồ sơ</button><Link href={`/dietitian/meal-plans/new?profile_id=${patient.id}`}><Icon name="sparkles" />Tạo phương án</Link></div>
    </header>

    {error && <div className={styles.error}><Icon name="warning" />{error}<button type="button" onClick={() => void load()}>Thử lại</button></div>}
    {notice && <div className={styles.notice}><Icon name="check" />{notice}<button type="button" aria-label="Đóng" onClick={() => setNotice('')}><Icon name="close" /></button></div>}

    <section className={styles.statusStrip}>
      <article><small>TRẠNG THÁI THEO DÕI</small><strong>Đang theo dõi</strong><span>Hồ sơ có thể dùng để lập phương án</span></article>
      <article><small>THỰC ĐƠN ĐANG ÁP DỤNG</small><strong>{activePlan?.plan_date ? new Date(`${activePlan.plan_date}T00:00:00`).toLocaleDateString('vi-VN') : 'Chưa có'}</strong><span>{activePlan ? `#${activePlan.id.slice(0, 8)} · ${activePlan.items.length} món` : 'Chưa có bản được phát hành'}</span></article>
      <article><small>BẢN GẦN NHẤT</small><strong>{latestPlan ? STATUS_LABELS[latestPlan.status] ?? latestPlan.status : 'Chưa có'}</strong><span>{latestPlan ? `${latestPlan.plan_date} · #${latestPlan.id.slice(0, 8)}` : 'Tạo phương án đầu tiên'}</span></article>
      <article><small>7 NGÀY GẦN NHẤT</small><strong>{loadedExtras.logs ? `${logs.length} ghi nhận` : 'Tải khi cần'}</strong><span>{loadedExtras.logs ? `${skipped} bỏ bữa · ${unmatched} món cần đối chiếu` : 'Mở Nhật ký hoặc Báo cáo tuần'}</span></article>
    </section>

    <nav className={styles.tabs} aria-label="Nội dung hồ sơ">
      {([['overview','Tổng quan'],['clinical','Lâm sàng'],['plans','Thực đơn'],['diary','Nhật ký'],['weekly','Báo cáo tuần'],['notes','Ghi chú'],['history','Lịch sử']] as Array<[Tab,string]>).map(([value,label]) => <button type="button" key={value} className={activeTab === value ? styles.active : undefined} onClick={() => setActiveTab(value)}>{label}</button>)}
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
  return <div className={styles.twoColumns}><section className={styles.card}><CardTitle eyebrow="THÔNG TIN CỐT LÕI" title="Dữ liệu đang được sử dụng"/><dl className={styles.details}><div><dt>Chiều cao</dt><dd>{patient.height_cm} cm</dd></div><div><dt>Cân nặng</dt><dd>{patient.weight_kg} kg</dd></div><div><dt>Hoạt động</dt><dd>{patient.activity_level}</dd></div><div><dt>Vùng miền</dt><dd>{patient.region ?? 'Chưa cập nhật'}</dd></div><div><dt>Dị ứng</dt><dd>{patient.allergies.join(', ') || 'Không ghi nhận'}</dd></div><div><dt>Thuốc</dt><dd>{patient.medications.join(', ') || 'Không ghi nhận'}</dd></div></dl></section><aside className={styles.card}><CardTitle eyebrow="ĐƯỜNG ĐI TIẾP THEO" title="Thực đơn và an toàn"/><div className={styles.nextStep}><span><Icon name={activePlan?'check':'info'}/></span><div><strong>{activePlan?'Đã có thực đơn đang áp dụng':'Chưa có thực đơn được phát hành'}</strong><p>{activePlan?'Người bệnh chỉ nhìn thấy phiên bản đã được duyệt.':'Tạo phương án mới sau khi hồ sơ lâm sàng đã đủ dữ liệu.'}</p></div></div><Link className={styles.primaryLink} href={`/dietitian/meal-plans/new?profile_id=${patient.id}`}>Tạo phương án thực đơn<Icon name="arrowRight"/></Link></aside></div>
}

function Clinical({patient,observations}:{patient:PatientProfile;observations:PatientObservation[]}) {
  return <div className={styles.twoColumns}><section className={styles.card}><CardTitle eyebrow="AN TOÀN LÂM SÀNG" title="Bệnh nền, thuốc và dị ứng"/><DataGroup title="Bệnh lý" values={patient.conditions.map(item => `${CONDITION_LABELS[item.code] ?? item.code}${item.stage ? ` · ${item.stage}` : ''}`)}/><DataGroup title="Thuốc đang dùng" values={patient.medications}/><DataGroup title="Dị ứng" values={patient.allergies}/><div className={styles.warning}><Icon name="warning"/>Thay đổi các dữ liệu này có thể làm quyết định duyệt cũ không còn phù hợp.</div></section><section className={styles.card}><CardTitle eyebrow="DÒNG THỜI GIAN" title="Chỉ số và diễn biến"/><div className={styles.list}>{observations.length ? observations.map(item => <article key={item.id}><span><Icon name="trend"/></span><div><strong>{item.observation_type.toUpperCase()} · {item.value} {item.unit}</strong><p>{item.source}{item.note ? ` · ${item.note}` : ''}</p></div><time>{new Date(item.measured_at).toLocaleDateString('vi-VN')}</time></article>) : <Empty text="Chưa có chỉ số được ghi theo thời gian."/>}</div></section></div>
}

function Plans({plans}:{plans:MealPlan[]}) { return <section className={styles.card}><CardTitle eyebrow="VERSIONED MEAL PLANS" title="Lịch sử thực đơn"/><div className={styles.planList}>{plans.length ? [...plans].sort((a,b)=>b.plan_date.localeCompare(a.plan_date)).map(plan => <Link href={`/dietitian/reviews/${plan.id}`} key={plan.id}><span className={`${styles.badge} ${styles[plan.status] ?? ''}`}>{STATUS_LABELS[plan.status] ?? plan.status}</span><div><strong>{new Date(`${plan.plan_date}T00:00:00`).toLocaleDateString('vi-VN')}</strong><small>#{plan.id.slice(0,8)} · {plan.items.length} món · phiên bản {plan.menu_version}</small></div><Icon name="chevronRight"/></Link>) : <Empty text="Hồ sơ này chưa có thực đơn."/>}</div></section> }

function Diary({logs}:{logs:FoodLog[]}) { return <section className={styles.card}><CardTitle eyebrow="7 NGÀY GẦN NHẤT" title="Nhật ký ăn uống"/><div className={styles.logList}>{logs.length ? [...logs].sort((a,b)=>b.logged_at.localeCompare(a.logged_at)).map(log => <article key={log.id}><span><Icon name="diary"/></span><div><strong>{log.free_text_vi || 'Ghi nhận bữa ăn'}</strong><small>{SLOT_LABELS[log.slot ?? ''] ?? 'Chưa rõ bữa'} · {log.grams ? `${Math.round(log.grams)} g` : 'không có gram'} · {log.match_status}</small></div><time>{new Date(log.logged_at).toLocaleString('vi-VN')}</time></article>) : <Empty text="Người bệnh chưa có ghi nhận trong 7 ngày gần nhất."/>}</div></section> }

function Weekly({logs,skipped,unmatched}:{logs:FoodLog[];skipped:number;unmatched:number}) {
  const activeDays = new Set(logs.map(log => log.logged_at.slice(0,10))).size
  return <div className={styles.twoColumns}><section className={styles.card}><CardTitle eyebrow="TÓM TẮT NGOẠI LỆ" title="Điểm cần chuyên gia chú ý"/><div className={styles.weekStats}><article><strong>{activeDays}/7</strong><span>ngày có dữ liệu</span></article><article><strong>{skipped}</strong><span>bữa được báo bỏ</span></article><article><strong>{unmatched}</strong><span>món cần đối chiếu</span></article></div><div className={styles.warning}><Icon name="info"/>Đây là tóm tắt từ dữ liệu hiện có, chưa phải báo cáo lâm sàng tự động đầy đủ.</div></section><aside className={styles.card}><CardTitle eyebrow="HÀNH ĐỘNG" title="Theo dõi theo ngoại lệ"/><p className={styles.bodyText}>{skipped || unmatched ? 'Hồ sơ đang có dữ liệu cần xem. Chuyên gia có thể đối chiếu món hoặc ghi nhận hướng theo dõi ở tab Ghi chú.' : 'Chưa phát hiện ngoại lệ từ nhật ký hiện có. Không cần mở từng bữa để duyệt lại.'}</p><Link className={styles.primaryLink} href="/dietitian/food-logs">Mở trung tâm theo dõi tuần<Icon name="arrowRight"/></Link></aside></div>
}

function Notes({notes,value,saving,onChange,onSave}:{notes:ClinicalNote[];value:string;saving:boolean;onChange:(value:string)=>void;onSave:()=>void}) { return <section className={styles.card}><CardTitle eyebrow="CARE TEAM" title="Ghi chú chuyên gia"/><div className={styles.noteComposer}><textarea value={value} onChange={event=>onChange(event.target.value)} placeholder="Đánh giá, mục tiêu hoặc nội dung cần theo dõi…"/><button type="button" disabled={saving || value.trim().length < 3} onClick={onSave}>{saving?'Đang lưu…':'Lưu ghi chú'}</button></div><div className={styles.noteList}>{notes.length ? notes.map(note=><article key={note.id}><header><strong>{note.note_type}</strong><time>{new Date(note.created_at).toLocaleString('vi-VN')}</time></header><p>{note.content}</p><small>{note.visibility} · phiên bản {note.version}</small></article>) : <Empty text="Chưa có ghi chú chăm sóc."/>}</div></section> }

function History({events}:{events:ReviewEvent[]}) { return <section className={styles.card}><CardTitle eyebrow="AUDIT TRAIL" title="Lịch sử quyết định"/><div className={styles.history}>{events.length ? events.map(event=><Link href={`/dietitian/reviews/${event.meal_plan_id}`} key={event.id}><span><Icon name={event.decision==='approved'?'check':'close'}/></span><div><strong>{event.decision==='approved'?'Đã duyệt':'Đã từ chối'} · phiên bản {event.menu_version}</strong><p>{event.notes || event.reason || 'Không có ghi chú'}</p></div><time>{new Date(event.created_at).toLocaleString('vi-VN')}</time></Link>) : <Empty text="Chưa có quyết định duyệt được ghi nhận."/>}</div></section> }

function EditPatientModal({patient,onClose,onSaved}:{patient:PatientProfile;onClose:()=>void;onSaved:(patient:PatientProfile)=>void}) {
  const [form,setForm]=useState<{age:string;height:string;weight:string;activity:string;region:string;conditions:string;medications:string;allergies:string}>({age:String(patient.age),height:String(patient.height_cm),weight:String(patient.weight_kg),activity:patient.activity_level,region:patient.region??'',conditions:patient.conditions.map(item=>item.code).join(', '),medications:patient.medications.join(', '),allergies:patient.allergies.join(', ')})
  const [saving,setSaving]=useState(false)
  const [error,setError]=useState('')
  const split=(value:string)=>value.split(',').map(item=>item.trim()).filter(Boolean)
  async function save(){const token=getToken();if(!token)return;setSaving(true);setError('');try{const conditionCodes=split(form.conditions);const updated=await createApiClient(token).updatePatient(patient.id,{age:Number(form.age),height_cm:Number(form.height),weight_kg:Number(form.weight),activity_level:form.activity as PatientProfile['activity_level'],region:(form.region||null) as PatientProfile['region'],conditions:conditionCodes.map(code=>({code,stage:patient.conditions.find(item=>item.code===code)?.stage??null})),medications:split(form.medications),allergies:split(form.allergies)});onSaved(updated)}catch(value){setError(value instanceof ApiError?value.message:'Không thể cập nhật hồ sơ.')}finally{setSaving(false)}}
  return <div className={styles.modalLayer} role="dialog" aria-modal="true" aria-label="Chỉnh sửa hồ sơ"><button className={styles.scrim} type="button" onClick={onClose} aria-label="Đóng"/><form className={styles.modal} onSubmit={event=>{event.preventDefault();void save()}}><header><div><small>CHỈNH SỬA CÓ KIỂM SOÁT</small><h2>Cập nhật hồ sơ</h2><p>Thay đổi lâm sàng quan trọng cần được kiểm tra lại trước lần phát hành tiếp theo.</p></div><button type="button" onClick={onClose} aria-label="Đóng"><Icon name="close"/></button></header>{error&&<div className={styles.formError}>{error}</div>}<div className={styles.formGrid}><label>Tuổi<input required type="number" min="1" max="120" value={form.age} onChange={e=>setForm({...form,age:e.target.value})}/></label><label>Chiều cao (cm)<input required type="number" min="50" max="250" value={form.height} onChange={e=>setForm({...form,height:e.target.value})}/></label><label>Cân nặng (kg)<input required type="number" min="10" max="500" step="0.1" value={form.weight} onChange={e=>setForm({...form,weight:e.target.value})}/></label><label>Mức hoạt động<select value={form.activity} onChange={e=>setForm({...form,activity:e.target.value})}><option value="light">Nhẹ</option><option value="moderate">Trung bình</option><option value="heavy">Nặng</option><option value="very_heavy">Rất nặng</option></select></label><label>Vùng miền<select value={form.region} onChange={e=>setForm({...form,region:e.target.value})}><option value="">Chưa cập nhật</option><option value="north">Miền Bắc</option><option value="central">Miền Trung</option><option value="south">Miền Nam</option></select></label><label className={styles.full}>Mã bệnh lý, cách nhau bằng dấu phẩy<input value={form.conditions} onChange={e=>setForm({...form,conditions:e.target.value})}/></label><label className={styles.full}>Thuốc đang dùng, cách nhau bằng dấu phẩy<input value={form.medications} onChange={e=>setForm({...form,medications:e.target.value})}/></label><label className={styles.full}>Dị ứng, cách nhau bằng dấu phẩy<input value={form.allergies} onChange={e=>setForm({...form,allergies:e.target.value})}/></label></div><footer><button type="button" onClick={onClose}>Hủy</button><button type="submit" disabled={saving}>{saving?'Đang lưu…':'Lưu thay đổi'}</button></footer></form></div>
}

function CardTitle({eyebrow,title}:{eyebrow:string;title:string}) { return <div className={styles.cardTitle}><small>{eyebrow}</small><h2>{title}</h2></div> }
function DataGroup({title,values}:{title:string;values:string[]}) { return <div className={styles.dataGroup}><h3>{title}</h3><div>{values.length?values.map(value=><span key={value}>{value}</span>):<span>Chưa ghi nhận</span>}</div></div> }
function Empty({text}:{text:string}) { return <div className={styles.empty}><Icon name="info"/><p>{text}</p></div> }
function TabLoading(){return <section className={styles.card}><div className={styles.empty}><Icon name="clock"/><p>Đang tải dữ liệu của mục này…</p></div></section>}
function PatientDetailSkeleton(){return <div className={styles.page}><div className={styles.skeletonHeader}/><div className={styles.skeletonMetrics}/><div className={styles.skeletonBody}/></div>}
