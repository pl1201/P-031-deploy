'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Icon } from '@/components/brand-artwork'
import { PatientAvatar } from '@/components/patient-avatar'
import { ApiError, createApiClient, type ClinicalTargets, type MealPlan, type MealPlanItem, type NutrientTarget, type PatientProfile, type ReplacementCandidate } from '@/lib/api'
import { getToken } from '@/lib/auth'
import { CONDITION_LABELS } from '@/lib/labels'
import { notifyReviewQueueChanged } from '@/lib/review-queue'
import styles from './page.module.css'

const SLOT_ORDER = ['breakfast', 'lunch', 'snack', 'dinner']
const SLOT_LABEL: Record<string, string> = { breakfast: 'Bữa sáng', lunch: 'Bữa trưa', snack: 'Bữa phụ', dinner: 'Bữa tối' }
const SLOT_TIME: Record<string, string> = { breakfast: '07:00', lunch: '12:00', snack: '15:30', dinner: '18:30' }
// FE-13: trước đó breakfast/lunch dùng chung icon 'sun', và 'moon' gán cho snack (15:30, giữa chiều)
// thay vì dinner (18:30, chập tối) — 4 icon khác nhau, gán đúng ngữ nghĩa thời điểm trong ngày.
const MEAL_ICON: Record<string, string> = { breakfast: 'sun', lunch: 'bowl', snack: 'sparkle', dinner: 'moon' }
const POLL_DELAYS_MS = [0, 200, 400, 800, 1200, 1800]
const POLL_ATTEMPTS = 40
// FE-19: trang trước đây nhét cả hồ sơ, mục tiêu và canvas tạo/kiểm tra vào 1 trang cuộn dài —
// stepper trên đầu đã HỨA 3 bước riêng (Hồ sơ/Mục tiêu/Tạo & kiểm tra) nhưng không bước nào thật.
// Tách thành wizard 3 bước thật, mỗi bước 1 việc, đúng cái stepper đang mô tả — không phải
// accordion thu gọn trong cùng 1 trang.
type WizardStep = 'profile' | 'targets' | 'build'
const STEP_TITLES = ['Hồ sơ', 'Mục tiêu', 'Tạo & kiểm tra', 'Chuyên gia duyệt']
const STEP_ICONS = ['profile', 'target', 'sparkles', 'profile']

// Nhãn dưỡng chất đọc được cho dietitian — key thô (kcal, na_mg…) là tên field backend,
// không nên leak ra UI. Nutrient nào chưa có trong map vẫn hiển thị được qua fallback
// (bỏ hậu tố đơn vị, viết hoa chữ đầu) thay vì rơi về key thô.
const NUTRIENT_LABEL: Record<string, string> = {
  kcal: 'Năng lượng', carb_g: 'Carbohydrate', protein_g: 'Protein', na_mg: 'Natri',
  k_mg: 'Kali', fiber_g: 'Chất xơ', phospho_mg: 'Phốt pho', purine_mg: 'Purine', sugar_g: 'Đường',
}
function nutrientLabel(key: string) {
  return NUTRIENT_LABEL[key] ?? key.replace(/_(mg|g|mcg)$/i, '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}
function formatRange(item: Pick<NutrientTarget, 'min_value' | 'max_value'>) {
  return item.min_value != null && item.max_value != null ? `${Math.round(item.min_value)}–${Math.round(item.max_value)}`
    : item.max_value != null ? `≤ ${Math.round(item.max_value)}`
    : item.min_value != null ? `≥ ${Math.round(item.min_value)}` : 'Không giới hạn'
}
function formatTargetValue(item: NutrientTarget) { return `${formatRange(item)} ${item.unit}` }
function bmiOf(patient: PatientProfile) { const h = patient.height_cm / 100; return patient.weight_kg / (h * h) }
// Phân loại BMI theo ngưỡng châu Á-Thái Bình Dương (WHO) — chỉ mang tính mô tả trên UI,
// không phải kết luận lâm sàng, không thay cho đánh giá của chuyên gia.
function bmiLabel(bmi: number) { return bmi < 18.5 ? 'Thiếu cân' : bmi < 23 ? 'Bình thường' : bmi < 25 ? 'Thừa cân' : 'Béo phì' }
function regionLabel(region: string | null) { return region ? `Miền ${region === 'north' ? 'Bắc' : region === 'central' ? 'Trung' : 'Nam'}` : 'Món Việt' }

// FE-24: thay các con số BMI/mục tiêu năng lượng/dưỡng chất khô khan bằng thanh
// khoảng giá trị (bullet chart) — cùng ngôn ngữ hình khối với MacroTrio đã có,
// chỉ trực quan hoá lại số đã tính sẵn từ backend, không tự tính thêm (RULE-1).
const BMI_MIN = 15, BMI_MAX = 35
const BMI_BANDS = [
  { key: 'under', label: 'Thiếu cân', from: 15, to: 18.5, color: 'var(--c-sky)' },
  { key: 'normal', label: 'Bình thường', from: 18.5, to: 23, color: 'var(--c-green)' },
  { key: 'over', label: 'Thừa cân', from: 23, to: 25, color: 'var(--c-yellow)' },
  { key: 'obese', label: 'Béo phì', from: 25, to: 35, color: 'var(--c-orange)' },
]
function BmiGauge({ value }: { value: number }) {
  const clamped = Math.min(BMI_MAX, Math.max(BMI_MIN, value))
  const pos = ((clamped - BMI_MIN) / (BMI_MAX - BMI_MIN)) * 100
  return (
    <div
      className={styles.bmiGauge}
      data-static-surface
      role="img"
      aria-label={`BMI ${value.toFixed(1)}, ${bmiLabel(value)}`}
    >
      <div className={styles.bmiTrack}>
        {BMI_BANDS.map(band => <i key={band.key} style={{ width: `${((band.to - band.from) / (BMI_MAX - BMI_MIN)) * 100}%`, background: band.color }} />)}
        <b style={{ left: `${pos}%` }} />
      </div>
      <div className={styles.bmiLegend}>{BMI_BANDS.map(band => <span key={band.key}><i style={{ background: band.color }} />{band.label}</span>)}</div>
    </div>
  )
}
function EnergyBar({ min, max, bmr, tdee }: { min: number; max: number; bmr: number; tdee: number }) {
  const scaleMax = Math.max(max, tdee, bmr, 1) * 1.12
  const pct = (v: number) => Math.min(100, Math.max(0, (v / scaleMax) * 100))
  return (
    <div className={styles.energyBar}>
      <div className={styles.energyTrack}>
        <i className={styles.energyRange} style={{ left: `${pct(min)}%`, width: `${Math.max(0, pct(max) - pct(min))}%` }} />
        <span className={styles.energyTick} data-tick="bmr" style={{ left: `${pct(bmr)}%` }} />
        <span className={styles.energyTick} data-tick="tdee" style={{ left: `${pct(tdee)}%` }} />
      </div>
      <div className={styles.energyScale}><span>0</span><span>{Math.round(scaleMax).toLocaleString('vi-VN')} kcal</span></div>
    </div>
  )
}
// Mỗi dưỡng chất chỉ có 1 trong 3 dạng: khoảng (min–max), trần tối đa (chỉ max),
// Màn hình này chỉ hiển thị RULE tĩnh (mục tiêu đã tính), chưa có giá trị đã ăn
// thực tế để so sánh — thanh tiến độ tô 3 vùng dễ bị đọc nhầm thành "đang đạt
// bao nhiêu %". Đổi sang data badge: một pill duy nhất nêu đúng khoảng/ngưỡng,
// kèm icon mũi tên chỉ hướng ràng buộc (↓ không vượt quá, ↑ tối thiểu) — không
// còn ngụ ý "giá trị hiện tại". Vẫn chỉ trình bày lại số đã tính sẵn từ backend
// (RULE-1/RULE-2), không tự suy ra giá trị mới.
function NutrientRow({ label, item }: { label: string; item: NutrientTarget }) {
  const { min_value: min, max_value: max, unit } = item
  const hasRange = min != null && max != null
  const direction: 'max' | 'min' | null = hasRange ? null : max != null ? 'max' : min != null ? 'min' : null
  const value = hasRange ? `${Math.round(min!)}–${Math.round(max!)}` : direction === 'max' ? `${Math.round(max!)}` : direction === 'min' ? `${Math.round(min!)}` : '—'
  const hint = direction === 'max' ? 'Không vượt quá' : direction === 'min' ? 'Tối thiểu' : 'Vùng tiêu chuẩn'
  return (
    <div className={styles.nrow}>
      <div className={styles.nrowLabel}><strong>{label}</strong><small>{hint}</small></div>
      <div className={styles.nrowBadgeWrap}>
        {direction && <span className={styles.nrowArrow} data-dir={direction} aria-hidden="true"><Icon name="chevronDown"/></span>}
        <span className={styles.nrowBadge}>{value}<small>{unit}</small></span>
      </div>
      {item.guideline_refs.length>0 && <span className={styles.nrowRef} title={item.guideline_refs.join('; ')}><Icon name="database"/>{item.guideline_refs.length}</span>}
    </div>
  )
}
const PLAN_STATUS_LABELS: Record<string, string> = {
  drafting: 'Đang tạo', pending_review: 'Chờ duyệt', manual_review_required: 'Cần xem xét thủ công', approved: 'Đã duyệt', rejected: 'Đã từ chối', failed: 'Thất bại',
}

export default function NewMealPlanPage() {
  const router = useRouter()
  const [patients, setPatients] = useState<PatientProfile[]>([])
  const [patientSearch, setPatientSearch] = useState('')
  const [patientId, setPatientId] = useState('')
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10))
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [plan, setPlan] = useState<MealPlan | null>(null)
  const [planId, setPlanId] = useState('')
  const [failedDetail, setFailedDetail] = useState<MealPlan['last_error']>(null)
  const [swapItem, setSwapItem] = useState<MealPlanItem | null>(null)
  const [candidates, setCandidates] = useState<ReplacementCandidate[]>([])
  const [selectedCandidate, setSelectedCandidate] = useState<ReplacementCandidate | null>(null)
  const [conflictPlan, setConflictPlan] = useState<MealPlan | null>(null)
  const [swapping, setSwapping] = useState(false)
  const [comboOpen, setComboOpen] = useState(false)
  const [step, setStep] = useState<WizardStep>('profile')
  const [targets, setTargets] = useState<ClinicalTargets | null>(null)
  const [targetsLoading, setTargetsLoading] = useState(false)
  const [targetsError, setTargetsError] = useState('')

  const selected = useMemo(() => patients.find(item => item.id === patientId), [patientId, patients])
  const grouped = useMemo(() => plan?.items.reduce<Record<string, MealPlanItem[]>>((acc, item) => { (acc[item.slot] ??= []).push(item); return acc }, {}) ?? {}, [plan])

  useEffect(() => {
    const token = getToken()
    if (!token) { router.replace('/login'); return }
    const api = createApiClient(token)
    api.listPatients(1, 30).then(async result => {
      const requested = new URLSearchParams(window.location.search).get('profile_id') ?? new URLSearchParams(window.location.search).get('patient_id')
      if (requested && !result.items.some(item => item.id === requested)) {
        const requestedPatient = await api.getPatient(requested)
        setPatients([requestedPatient, ...result.items])
        setPatientId(requestedPatient.id)
      } else {
        setPatients(result.items)
        setPatientId(requested ?? result.items[0]?.id ?? '')
      }
    }).catch(value => setError(value instanceof Error ? value.message : 'Không thể tải hồ sơ.')).finally(() => setLoading(false))
  }, [router])

  useEffect(() => {
    const token = getToken()
    if (!token) return
    const timer = window.setTimeout(() => {
      setLoading(true)
      createApiClient(token).listPatients(1, 30, patientSearch || undefined).then(result => {
        setPatients(current => {
          const selectedPatient = current.find(item => item.id === patientId)
          return selectedPatient && !result.items.some(item => item.id === selectedPatient.id)
            ? [selectedPatient, ...result.items]
            : result.items
        })
      }).catch(value => setError(value instanceof Error ? value.message : 'Không thể tìm hồ sơ.')).finally(() => setLoading(false))
    }, 350)
    return () => window.clearTimeout(timer)
  }, [patientSearch, patientId])

  function resetDraftContext() {
    setPlan(null)
    setPlanId('')
    setConflictPlan(null)
    setNotice('')
    setError('')
  }

  function selectPatient(id: string) {
    setPatientId(id)
    resetDraftContext()
    setTargets(null); setTargetsError('')
    setStep('profile')
  }

  async function goToTargets() {
    if (!patientId) return
    setStep('targets')
    if (targets) return // đã tính rồi, không gọi lại khi bấm qua lại giữa các bước
    const token = getToken()
    if (!token) return
    setTargetsLoading(true); setTargetsError(''); setTargets(null)
    try { setTargets(await createApiClient(token).computeTargets(patientId)) }
    catch (value) { setTargetsError(value instanceof Error ? value.message : 'Không tính được mục tiêu dinh dưỡng.') }
    finally { setTargetsLoading(false) }
  }

  function handleStepClick(index: number) {
    if (index === 0) { setStep('profile'); return }
    if (index === 1) { if (patientId) void goToTargets(); return }
    if (index === 2) { if (targets) setStep('build'); return }
  }

  async function generate() {
    const token = getToken()
    if (!token || !patientId) return
    setGenerating(true); setError(''); setNotice(''); setPlan(null); setPlanId(''); setConflictPlan(null); setFailedDetail(null)
    try {
      const api = createApiClient(token)
      const result = await api.createMealPlan(patientId, date)
      setPlanId(result.plan_id)
      for (let attempt = 0; attempt < POLL_ATTEMPTS; attempt += 1) {
        const wait = POLL_DELAYS_MS[Math.min(attempt, POLL_DELAYS_MS.length - 1)]
        if (wait) await new Promise(resolve => setTimeout(resolve, wait))
        const current = await api.getMealPlan(result.plan_id)
        if (current.status === 'drafting') continue
        setGenerating(false)
        if (current.status === 'failed' || current.status === 'rejected') {
          setError('Không thể tạo thực đơn an toàn với cấu hình này. Bản xử lý vẫn được lưu để chuyên gia xem nguyên nhân.')
          if (current.status === 'failed') setFailedDetail(current.last_error)
          return
        }
        setPlan(current)
        if (current.status === 'pending_review') notifyReviewQueueChanged()
        if (current.status === 'manual_review_required') setNotice('Cổng an toàn đang chặn bản này. Hãy mở màn hình duyệt để xem vấn đề cần xử lý.')
        else if (current.review_packet?.can_approve === false) setNotice('Thực đơn đã lưu nhưng chưa đủ điều kiện duyệt. Các lý do được hiển thị trong phần kiểm tra.')
        return
      }
      throw new Error('Quá thời gian chờ. Bản nháp vẫn được lưu; hãy mở bản đã lưu thay vì gửi lại yêu cầu.')
    } catch (value) {
      if (value instanceof ApiError && value.status === 409) {
        try {
          const existing = await createApiClient(token).listMealPlans(patientId)
          const match = existing.items.find(item => item.plan_date === date && ['drafting', 'pending_review', 'manual_review_required'].includes(item.status))
          if (match) { setConflictPlan(match); setPlanId(match.id) }
        } catch { /* Giữ thông báo gốc nếu không tải được bản hiện có. */ }
      }
      setError(value instanceof ApiError ? value.message : value instanceof Error ? value.message : 'Không thể tạo thực đơn.')
      setGenerating(false)
    }
  }

  const blockedReasons = plan ? [...(plan.review_packet?.target_gate_reasons ?? []), ...plan.safety_findings.filter(finding => finding.risk_level === 'P0').map(finding => finding.message_vi)] : []
  const target = (key: string) => { const item = plan?.targets?.targets?.[key]; return item?.max_value ?? item?.min_value ?? null }
  const kcal = plan?.computed_nutrition?.kcal
  const carb = plan?.computed_nutrition?.carb_g
  const hasViolation = (term: string) => plan?.violations.some(item => (item.nutrient || '').toLowerCase().includes(term) || (item.message_vi || '').toLowerCase().includes(term))
  // Trạng thái cho panel "Kiểm tra thực đơn" — tách riêng khỏi JSX để mỗi dòng chỉ còn diễn giải câu chữ,
  // không phải tự suy luận lại điều kiện.
  const checksVerified = Boolean(plan?.review_packet && Object.keys(plan.review_packet).length && plan.menu_hash_ready && plan.nutrition_hash_ready)
  const carbWarn = Boolean(plan && hasViolation('carb'))
  const allergyWarn = Boolean(plan && hasViolation('dị ứng'))
  const drugWarn = Boolean(plan && plan.violations.some(item => item.kind?.includes('interaction')))

  async function openSwap(item: MealPlanItem) {
    const token = getToken()
    if (!token || !plan) return
    setSwapItem(item); setCandidates([]); setSelectedCandidate(null); setError('')
    try { setCandidates(await createApiClient(token).listReplacementCandidates(plan.id, item.id)) }
    catch (value) { setError(value instanceof Error ? value.message : 'Không thể tải món thay thế.') }
  }

  async function replaceItem(candidate: ReplacementCandidate) {
    const token = getToken()
    if (!token || !plan || !swapItem) return
    setSwapping(true); setError('')
    try { setPlan(await createApiClient(token).replaceMealPlanItem(plan.id, swapItem.id, candidate.dish_id, candidate.serving_g)); setSwapItem(null) }
    catch (value) { setError(value instanceof Error ? value.message : 'Không thể đổi món.') }
    finally { setSwapping(false) }
  }

  return <div className={styles.page}>
    <header className={styles.pageHeader}>
      <div><div className={styles.breadcrumb}><Link href="/dietitian">Tổng quan</Link><Icon name="chevronRight"/><span>Tạo thực đơn</span></div><h1>Tạo thực đơn cá nhân hóa</h1><p>Chọn bệnh nhân, kiểm tra đầu vào rồi tạo thực đơn để chuyên gia xem và duyệt.</p></div>
      <div className={styles.headerMeta}><span><Icon name="database"/>Dữ liệu có nguồn</span><span><Icon name="shield"/>Cổng an toàn server</span></div>
    </header>

    <section className={styles.workflow} aria-label="Quy trình tạo thực đơn">
      {/* FE-19: stepper giờ là điều hướng THẬT, không còn trang trí — bấm vào bước đã hoàn tất
          để quay lại, không cho nhảy cóc tới bước chưa đủ điều kiện (VD chưa có mục tiêu thì
          không vào được "Tạo & kiểm tra"). */}
      {STEP_TITLES.map((title,index)=>{
        const complete = index===0 ? Boolean(patientId) : index===1 ? Boolean(targets) : index===2 ? Boolean(plan) : false
        const current = (index===0&&step==='profile')||(index===1&&step==='targets')||(index===2&&step==='build')
        const state = index===0 ? (patientId?'Hoàn tất':'Chờ chọn') : index===1 ? (targetsLoading?'Đang tính':targets?'Hoàn tất':patientId?'Sẵn sàng':'Chờ hồ sơ') : index===2 ? (generating?'Đang xử lý':plan?'Hoàn tất':targets?'Sẵn sàng tạo':'Chờ mục tiêu') : (plan?'Chờ duyệt':'Chưa tới')
        const clickable = index===0 || (index===1&&Boolean(patientId)) || (index===2&&Boolean(targets))
        const handoff = index===3
        return <article className={`${current?styles.current:''} ${complete?styles.complete:''} ${clickable?styles.stepClickable:''} ${handoff?styles.stepHandoff:''}`} key={title} onClick={clickable?()=>handleStepClick(index):undefined} role={clickable?'button':undefined} tabIndex={clickable?0:undefined}><span><Icon name={handoff?'arrowRight':STEP_ICONS[index]}/><i>{index+1}</i></span><div><small>{state}</small><strong>{title}</strong></div>{index<3&&<Icon name="arrowRight"/>}</article>
      })}
    </section>

    {step==='profile' && <>
      {/* Bước 1/3 — chỉ 1 việc: tìm và xác nhận đúng bệnh nhân. Mục tiêu và canvas tạo thực đơn
          không còn hiện cùng trang này (FE-19). */}
      <section className={styles.caseBand}>
        {/* Search chỉ chiếm chỗ khi thật sự cần tìm — đã chọn bệnh nhân thì thu về một dòng
            "đang chọn ai", bấm "Đổi bệnh nhân" mới mở lại ô tìm kiếm. */}
        {selected && !comboOpen ? (
          <div className={styles.patientbar}>
            <span className={styles.patientbarLbl}>BỆNH NHÂN ĐANG CHỌN</span>
            <span className={styles.patientbarVal}><i/>{selected.sex==='male'?'Nam':'Nữ'} · #{selected.id.slice(0,8).toUpperCase()}</span>
            <button type="button" className={styles.patientbarSwap} onClick={()=>{setPatientSearch('');setComboOpen(true)}}>Đổi bệnh nhân</button>
          </div>
        ) : (
          <div className={styles.combo}>
            <input id="patient-search" value={patientSearch} onChange={event=>setPatientSearch(event.target.value)} onFocus={()=>setComboOpen(true)} onBlur={()=>window.setTimeout(()=>setComboOpen(false),150)} placeholder={selected?'Tìm hồ sơ khác…':'Mã hồ sơ, email, bệnh lý hoặc thuốc'} autoComplete="off"/>
            {comboOpen && (loading ? <div className={styles.comboList}><div className={styles.inlineLoading}>Đang tìm hồ sơ…</div></div> : patients.length>0 && <ul className={styles.comboList} role="listbox" aria-label="Kết quả hồ sơ">{patients.map(patient=><li key={patient.id} role="option" aria-selected={patient.id===patientId}><button type="button" onMouseDown={event=>event.preventDefault()} onClick={()=>{selectPatient(patient.id);setComboOpen(false)}}>ID: {patient.id.slice(0,8).toUpperCase()} · {patient.sex==='male'?'Nam':'Nữ'}, {patient.age} tuổi{patient.conditions.length?` · ${patient.conditions.map(item=>item.code).join(', ')}`:''}</button></li>)}</ul>)}
          </div>
        )}

        {selected ? <div className={styles.contextgrid}>
          <div className={styles.identity}>
            <small className={styles.eyebrow}>Nhận diện</small>
            <div className={styles.idrow}>
              <span className={`${styles.ring} ${selected.allergies.length?styles.ringAlert:styles.ringOk}`}>
                <PatientAvatar sex={selected.sex}/>
                {selected.allergies.length>0 && <i className={styles.ringFlag}><Icon name="warning"/></i>}
              </span>
              <div>
                <div className={styles.idname}>MÃ HỒ SƠ {selected.id.slice(0,8).toUpperCase()}</div>
                <div className={styles.idmain}>{selected.sex==='male'?'Nam':'Nữ'} · {selected.age} tuổi</div>
              </div>
            </div>
            <Link className={styles.openlink} href={`/dietitian/patients/${selected.id}`}>Mở hồ sơ 360<Icon name="arrowRight"/></Link>
            <div className={styles.metricstrip} data-static-surface>
              <div><strong>{selected.height_cm} cm</strong><small>Chiều cao</small></div>
              <div><strong>{selected.weight_kg} kg</strong><small>Cân nặng</small></div>
              <div className={styles.metricBmi}><strong>{bmiOf(selected).toFixed(1)}</strong><small>BMI · <span>{bmiLabel(bmiOf(selected))}</span></small></div>
            </div>
            <BmiGauge value={bmiOf(selected)} />
          </div>
          <div className={styles.clinsum}>
            <small className={`${styles.eyebrow} ${styles.clinEyebrow}`}>Tóm tắt lâm sàng</small>
            <div className={styles.tier1Diag}>
              <span className={styles.tier1Dot}><Icon name="profile"/></span>
              <div><small>Chẩn đoán</small><strong>{selected.conditions.length?selected.conditions.map(item=>CONDITION_LABELS[item.code] ?? item.code).join(' · '):'Chưa ghi nhận bệnh nền'}</strong>
                {selected.conditions.length>0 && <div className={styles.tags}>{selected.conditions.map(item=><span className={styles.tag} key={item.code}>{CONDITION_LABELS[item.code] ?? item.code}{item.stage?` — ${item.stage}`:''}</span>)}</div>}
              </div>
            </div>
            <div className={selected.allergies.length?styles.tier1Alert:styles.tier1Diag}>
              <span className={selected.allergies.length?styles.tier1DotAlert:styles.tier1Dot}><Icon name="warning"/></span>
              <div><small>Dị ứng</small><strong>{selected.allergies.length?'Cần tránh khi chọn món':'Không ghi nhận dị ứng'}</strong>
                {selected.allergies.length>0 && <div className={styles.tags}>{selected.allergies.map(item=><span className={styles.tagAlert} key={item}>{item}</span>)}</div>}
              </div>
            </div>
            <div className={styles.tier2row}>
              <div className={styles.tier2}><small>Thuốc</small><strong>{selected.medications.join(', ')||'Không ghi nhận'}</strong></div>
              <div className={styles.tier2}><small>Khẩu vị</small><strong>{regionLabel(selected.region)}</strong></div>
            </div>
          </div>
        </div> : <div className={styles.noPatient}>Chưa có hồ sơ để lập kế hoạch.</div>}
      </section>
      <div className={styles.stepFooter}>
        <span className={styles.stepFooterStatus}>{selected ? <><i>✓</i>Hồ sơ bệnh nhân đầy đủ</> : 'Chọn một hồ sơ để tiếp tục'}</span>
        <button type="button" disabled={!selected} onClick={()=>void goToTargets()}>Tiếp tục: Mục tiêu<Icon name="arrowRight"/></button>
      </div>
    </>}

    {step!=='profile' && selected && (
      /* Dải nhận diện gọn — giữ ngữ cảnh "đang lập kế hoạch cho ai" xuyên suốt bước 2-3 mà
         không kéo lại nguyên khối Chẩn đoán/Dị ứng/Thuốc/Khẩu vị đã xem ở bước 1. Cảnh báo dị
         ứng luôn hiện diện (kể cả khi không có) thay vì biến mất lúc rỗng như trước. */
      <section className={styles.caseStrip}>
        <span className={`${styles.ring} ${selected.allergies.length?styles.ringAlert:styles.ringOk}`}><PatientAvatar sex={selected.sex} size="sm"/></span>
        <div><strong>{selected.conditions.length?selected.conditions.map(item=>item.code).join(' · '):'Chưa ghi nhận bệnh nền'}</strong><small>{selected.sex==='male'?'Nam':'Nữ'} · {selected.age} tuổi · MÃ {selected.id.slice(0,8).toUpperCase()}</small></div>
        <span className={selected.allergies.length?styles.stripAlert:styles.stripOk}><Icon name={selected.allergies.length?'warning':'check'}/>{selected.allergies.length?`Dị ứng: ${selected.allergies.join(', ')}`:'Không có dị ứng ghi nhận'}</span>
        <button type="button" className={styles.stripChange} onClick={()=>setStep('profile')}>Đổi bệnh nhân</button>
      </section>
    )}

    {step==='targets' && selected && (
      /* Bước 2/3 — MỚI: trước đây mục tiêu dinh dưỡng chỉ lộ ra SAU khi đã sinh thực đơn, giấu
         trong sidebar. Giờ xem/xác nhận mục tiêu trước, để bắt lỗi hồ sơ trước khi tốn 1 lượt
         sinh — /targets/compute đã có sẵn ở backend, chỉ chưa có màn hình riêng dùng tới. */
      <section className={styles.targetsCard}>
        <header><small className={styles.eyebrow}>Mục tiêu dinh dưỡng</small><h2>Mục tiêu tính cho lần tạo này</h2><p>Dựa trên hồ sơ, bệnh lý và rule lâm sàng hiện có — chưa liên quan tới món ăn.</p></header>
        {targetsLoading && <div className={styles.processing}><span className="spinner"/><div><strong>Đang tính mục tiêu</strong><p>Áp rule theo bệnh lý và giai đoạn của hồ sơ này.</p></div></div>}
        {targetsError && <div className={styles.error} role="alert"><Icon name="warning"/><div><strong>Chưa tính được mục tiêu</strong><p>{targetsError}</p></div><button type="button" onClick={()=>void goToTargets()}>Thử lại</button></div>}
        {targets && <>
          {targets.needs_expert_review ? (
            <div className={styles.warningNotice}><Icon name="warning"/>Ngưỡng dinh dưỡng có xung đột — cần bạn xác nhận trước khi tạo thực đơn, hệ thống không tự chọn bên nào.</div>
          ) : targets.conflict_notes.length>0 ? (
            /* Xung đột đã được rule tự xử lý (lấy ngưỡng chặt hơn) — trình bày như một việc đã
               xong, không phải cảnh báo cần đọc kỹ, để không đánh đồng với needs_expert_review. */
            <div className={styles.conflictOk}>
              <span className={styles.conflictCk}><Icon name="check"/></span>
              <div><strong>Đã xử lý xung đột mục tiêu</strong><p>{targets.conflict_notes.join(' ')}</p><span className={styles.conflictNoaction}><Icon name="check"/>Không cần xác nhận thêm</span></div>
            </div>
          ) : null}

          {targets.targets.kcal && <div className={styles.herotarget}>
            <small className={styles.eyebrow}>Mục tiêu năng lượng</small>
            <strong>{formatRange(targets.targets.kcal)}</strong>
            <span className={styles.herounit}>{targets.targets.kcal.unit} / ngày</span>
            <span className={styles.heroproposed}>Mục tiêu đề xuất</span>
            <EnergyBar min={targets.targets.kcal.min_value ?? 0} max={targets.targets.kcal.max_value ?? targets.targets.kcal.min_value ?? 0} bmr={targets.bmr_kcal} tdee={targets.tdee_kcal} />
            <div className={styles.supportpair}>
              <div><small><i className={styles.dotBmr}/>Cơ bản (BMR)</small><strong>{Math.round(targets.bmr_kcal)} kcal</strong><span>Chuyển hoá lúc nghỉ</span></div>
              <div><small><i className={styles.dotTdee}/>Tiêu hao ước tính (TDEE)</small><strong>{Math.round(targets.tdee_kcal)} kcal</strong><span>Theo mức vận động</span></div>
            </div>
          </div>}

          <small className={`${styles.eyebrow} ${styles.gridlabel}`}>Theo từng dưỡng chất</small>
          <div className={styles.targetsPanel}>
            {Object.entries(targets.targets).filter(([key])=>key!=='kcal').map(([key,item])=><NutrientRow key={key} label={nutrientLabel(key)} item={item}/>)}
          </div>

          {!targets.needs_expert_review && <div className={styles.confirmline}><i><Icon name="check"/></i>{Object.keys(targets.targets).length} mục tiêu dinh dưỡng · Không có xung đột cần xử lý</div>}
        </>}
        <div className={styles.stepActions}><button type="button" className={styles.stepBack} onClick={()=>setStep('profile')}><Icon name="arrowLeft"/>Quay lại</button><button type="button" disabled={!targets} onClick={()=>setStep('build')}>Xác nhận &amp; tạo thực đơn<Icon name="arrowRight"/></button></div>
      </section>
    )}

    {step==='build' && <div className={styles.workspace}>
      <main className={styles.canvas}>
        <section className={styles.briefCard}>
          <header><div><small className={styles.eyebrow}>Thiết lập thực đơn</small><h2>Thông tin cho lần tạo này</h2></div></header>
          <div className={styles.brieftiles}>
            <div className={styles.brieftileDate}><small>NGÀY ÁP DỤNG</small><div><Icon name="calendar"/><input type="date" value={date} onChange={event=>{setDate(event.target.value);resetDraftContext()}}/></div></div>
            <div><small>CẤU TRÚC BỮA</small><strong>3 bữa chính + 1 bữa phụ</strong></div>
            <div><small>ƯU TIÊN KHẨU VỊ</small><strong>{regionLabel(selected?.region ?? null)}</strong></div>
          </div>
          <div className={styles.generateRow}><div><strong>Giá trị dinh dưỡng được tính lại khi thực đơn thay đổi</strong><p>Hệ thống cập nhật năng lượng và các mục tiêu dinh dưỡng sau mỗi lần chỉnh sửa.</p></div><button type="button" onClick={()=>void generate()} disabled={!patientId||generating||Boolean(plan)}><Icon name="sparkles"/>{generating?'Đang tạo & kiểm tra…':plan?'Đã tạo thực đơn':'Tạo thực đơn'}</button></div>
          {generating&&<div className={styles.processing}><span className="spinner"/><div><strong>Đang tạo và kiểm tra thực đơn, vui lòng chờ trong giây lát…</strong></div></div>}
          {error&&<div className={styles.error} role="alert"><Icon name="warning"/><div><strong>Chưa hoàn tất yêu cầu</strong><p>{error}</p></div>{planId&&<button type="button" onClick={()=>router.push(`/dietitian/reviews/${planId}`)}>Mở bản #{planId.slice(0,8).toUpperCase()}</button>}</div>}
          {failedDetail&&<details className={styles.errorDetail}><summary>Chi tiết lỗi kỹ thuật ({failedDetail.type})</summary><p>{failedDetail.message}</p><pre>{failedDetail.traceback}</pre></details>}
          {conflictPlan&&<div className={styles.conflict}><Icon name="info"/><div><strong>Ngày này đã có một bản đang xử lý</strong><p>#{conflictPlan.id.slice(0,8).toUpperCase()} · {PLAN_STATUS_LABELS[conflictPlan.status] ?? conflictPlan.status}. Không tạo trùng.</p></div><button type="button" onClick={()=>router.push(`/dietitian/reviews/${conflictPlan.id}`)}>Mở bản hiện có</button></div>}
          {notice&&<div className={styles.warningNotice}><Icon name="warning"/>{notice}</div>}
        </section>

        <section className={styles.draftCard}>
          <header><div><small className={styles.eyebrow}>Kết quả tạo thực đơn</small><h2>{plan?<>Thực đơn đề xuất<span className={styles.idtag}>#{plan.id.slice(0,8).toUpperCase()}</span></>:'Bản xem trước thực đơn'}</h2></div></header>
          {!plan&&!generating&&<div className={styles.draftEmpty}><span><Icon name="bowl"/></span><h3>Canvas đang chờ thực đơn</h3><p>Kiểm tra hồ sơ và thông tin phía trên, sau đó nhấn &quot;Tạo thực đơn&quot;.</p></div>}
          {generating&&<div className={styles.draftEmpty}><h3>Đang chuẩn bị cấu trúc bữa</h3><p>Kết quả thật sẽ xuất hiện khi backend hoàn thành.</p></div>}
          {plan&&!plan.items.length&&<div className={styles.blocked}><Icon name="warning"/><div><strong>Chưa có món để hiển thị</strong>{blockedReasons.length?<ul>{blockedReasons.map(reason=><li key={reason}>{reason}</li>)}</ul>:<p>Bản nháp đã lưu. Mở màn hình duyệt để xem dữ liệu server đã ghi.</p>}</div></div>}
          {plan&&plan.items.length>0&&<div className={styles.mealGrid}>{SLOT_ORDER.map(slot=><MealSlot key={slot} slot={slot} items={grouped[slot]??[]} onSwap={item=>void openSwap(item)}/>)}</div>}
          {plan&&<footer className={styles.draftFooter}><div><Icon name="info"/><span>Thực đơn này chưa được gửi cho người bệnh. Bạn vẫn có thể thay đổi món và kiểm tra lại trước khi duyệt.</span></div><button type="button" onClick={()=>router.push(`/dietitian/reviews/${plan.id}`)}>Xem nguồn tham chiếu<Icon name="arrowRight"/></button></footer>}
        </section>
      </main>

      <aside className={styles.evidenceRail}>
        <section className={styles.evidenceCard}>
          <header><h2>Kiểm tra thực đơn</h2></header>
          <div className={styles.checklist}>
            <div className={`${styles.checkrow} ${plan&&kcal?styles.checkOk:styles.checkIdle}`}><span className={styles.checkSt}><Icon name={plan&&kcal?'check':'info'}/></span><div><strong>Năng lượng</strong><p>{plan?(kcal?`${Math.round(kcal)}${target('kcal')?` / ${Math.round(target('kcal')!)} kcal`:' kcal'} · Phù hợp`:'Chưa tính được năng lượng cho lần này'):'Chưa có thực đơn để kiểm tra'}</p></div></div>
            <div className={`${styles.checkrow} ${carbWarn?styles.checkWarn:plan&&carb?styles.checkOk:styles.checkIdle}`}><span className={styles.checkSt}><Icon name={carbWarn?'warning':plan&&carb?'check':'info'}/></span><div><strong>Carbohydrate</strong><p>{plan?(carbWarn?'Vượt ngưỡng carbohydrate — cần điều chỉnh trước khi duyệt':carb?`${Math.round(carb)}${target('carb_g')?` / ${Math.round(target('carb_g')!)} g`:' g'} · Phù hợp`:'Chưa tính được carbohydrate cho lần này'):'Chưa có thực đơn để kiểm tra'}</p></div></div>
            <div className={`${styles.checkrow} ${plan&&checksVerified?styles.checkOk:styles.checkIdle}`}><span className={styles.checkSt}><Icon name={plan&&checksVerified?'check':'info'}/></span><div><strong>Phân bổ bữa ăn</strong><p>{plan?(checksVerified?'Đúng tỷ lệ 3 bữa chính + 1 bữa phụ':'Đang chờ kết quả kiểm tra'):'Chưa có thực đơn để kiểm tra'}</p></div></div>
            {/* Chưa có nguồn tính GI/GL trong hệ thống — luôn hiện "chưa có dữ liệu" thay vì
                gộp vào trạng thái "Đạt" chung khi review_packet sẵn sàng, để không ngầm nhận
                một con số chưa từng được tính (RULE-2). */}
            <div className={`${styles.checkrow} ${styles.checkIdle}`}><span className={styles.checkSt}><Icon name="info"/></span><div><strong>Chỉ số đường huyết (GI/GL)</strong><p>Chưa có dữ liệu cho lần tạo này</p></div></div>
            <div className={`${styles.checkrow} ${allergyWarn?styles.checkWarn:plan?styles.checkOk:styles.checkIdle}`}><span className={styles.checkSt}><Icon name={allergyWarn?'warning':plan?'check':'info'}/></span><div><strong>Dị ứng</strong><p>{plan?(allergyWarn?'Phát hiện món có thể chứa dị ứng — cần rà soát trước khi duyệt':selected?.allergies.length?`Không phát hiện ${selected.allergies.join(', ')}`:'Hồ sơ không ghi nhận dị ứng'):'Chưa có thực đơn để kiểm tra'}</p></div></div>
            <div className={`${styles.checkrow} ${drugWarn?styles.checkWarn:plan?styles.checkOk:styles.checkIdle}`}><span className={styles.checkSt}><Icon name={drugWarn?'warning':plan?'check':'info'}/></span><div><strong>Lưu ý thuốc &amp; thực phẩm</strong><p>{!plan?(selected?.medications.length?`${selected.medications.join(', ')} — sẽ đối chiếu khi có thực đơn.`:'Hồ sơ chưa ghi nhận thuốc đang dùng.'):drugWarn?`${selected?.medications.join(', ')||'Thuốc đã ghi nhận'} — phát hiện tương tác cần rà soát, xem chi tiết ở màn duyệt.`:`${selected?.medications.join(', ')||'Không ghi nhận thuốc'} — đã đối chiếu, không phát hiện tương tác.`}</p></div></div>
          </div>
          {plan&&<button type="button" className={styles.evidencelink} onClick={()=>router.push(`/dietitian/reviews/${plan.id}`)}>Xem nguồn tham chiếu<Icon name="arrowRight"/></button>}
          <div className={styles.constraintRow}><small>YÊU CẦU KHI TẠO THỰC ĐƠN</small><div><span><Icon name="bowl"/>Ưu tiên món Việt</span><span><Icon name="profile"/>Theo hồ sơ bệnh nhân</span><span><Icon name="scale"/>Gram chuẩn</span><span><Icon name="shield"/>{selected?.allergies.length?'Loại trừ món gây dị ứng':'Không có dị ứng cần loại trừ'}</span></div></div>
        </section>
      </aside>
    </div>}

    {step==='build' && <footer className={styles.actionBar}><div><span><Icon name="warning"/></span><p><strong>Chưa gửi cho người bệnh</strong><small>Chỉ phiên bản được duyệt mới xuất hiện ở không gian bệnh nhân.</small></p></div><button type="button" disabled={!planId||generating} onClick={()=>planId&&router.push(`/dietitian/reviews/${planId}`)}>{plan?'Tiếp tục duyệt thực đơn':'Mở bản đã lưu'}<Icon name="arrowRight"/></button></footer>}

    {swapItem&&<SwapDrawer item={swapItem} candidates={candidates} selected={selectedCandidate} busy={swapping} onSelect={setSelectedCandidate} onClose={()=>!swapping&&setSwapItem(null)} onApply={candidate=>void replaceItem(candidate)}/>}
  </div>
}

function MealSlot({slot,items,onSwap}:{slot:string;items:MealPlanItem[];onSwap:(item:MealPlanItem)=>void}) {
  const grams=items.reduce((sum,item)=>sum+item.grams,0)
  return <section className={`${styles.mealSlot} ${styles[slot]}`}><header><div><span><Icon name={MEAL_ICON[slot]}/></span><div><small>{SLOT_TIME[slot]}</small><h3>{SLOT_LABEL[slot]}</h3></div></div><b>{Math.round(grams)} g</b></header><div>{items.length?items.map(item=><article key={item.id}><div><strong>{item.name_vi}{item.is_estimated&&<span className={styles.estBadge}>Ước tính</span>}</strong><small title={item.source_ref||undefined}>{Math.round(item.grams)} g · {item.is_estimated?'Ước tính':`Theo ${item.source||'chưa rõ nguồn'}`}</small></div><button type="button" onClick={()=>onSwap(item)}><Icon name="refresh"/>Đổi</button></article>):<p className={styles.noItems}>Không có món ở khung bữa này.</p>}</div></section>
}

function SwapDrawer({item,candidates,selected,busy,onSelect,onClose,onApply}:{item:MealPlanItem;candidates:ReplacementCandidate[];selected:ReplacementCandidate|null;busy:boolean;onSelect:(value:ReplacementCandidate)=>void;onClose:()=>void;onApply:(value:ReplacementCandidate)=>void}) {
  return <div className={styles.swapBackdrop} role="presentation" onMouseDown={onClose}><section className={styles.swapPanel} role="dialog" aria-modal="true" aria-label="Đổi món" onMouseDown={event=>event.stopPropagation()}><header><div><small>ĐỔI MÓN · {SLOT_LABEL[item.slot]}</small><h2>Xem trước thay đổi</h2><p>Chỉ ghi thay đổi sau khi bạn xác nhận. Backend sẽ tính lại dinh dưỡng và an toàn.</p></div><button type="button" onClick={onClose} aria-label="Đóng"><Icon name="close"/></button></header><div className={styles.swapCompare}><article><small>HIỆN TẠI</small><strong>{item.name_vi}</strong><span>{Math.round(item.grams)} g</span></article><Icon name="arrowRight"/><article><small>THAY THẾ</small><strong>{selected?.name_vi||'Chưa chọn món'}</strong><span>{selected?`${Math.round(selected.serving_g)} g`:'Chọn ứng viên bên dưới'}</span></article></div><section className={styles.candidates}><header><h3>Món cùng vai trò trong bữa</h3><span>{candidates.length} ứng viên</span></header>{candidates.length?candidates.map(candidate=><button type="button" className={selected?.dish_id===candidate.dish_id?styles.candidateSelected:undefined} key={candidate.dish_id} disabled={busy} onClick={()=>onSelect(candidate)}><span><strong>{candidate.name_vi}</strong><small>{candidate.region?regionLabel(candidate.region):'Phù hợp toàn quốc'}</small></span><b>{Math.round(candidate.serving_g)} g</b><Icon name="chevronRight"/></button>):<div className={styles.candidateEmpty}><span className="spinner"/>Đang tải hoặc chưa có món phù hợp.</div>}</section><footer><button type="button" onClick={onClose}>Hủy</button><button type="button" disabled={!selected||busy} onClick={()=>selected&&onApply(selected)}>{busy?'Đang tính lại…':'Áp dụng & kiểm tra lại'}<Icon name="arrowRight"/></button></footer></section></div>
}
