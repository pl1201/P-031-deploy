'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Icon } from '@/components/brand-artwork'
import { PatientAvatar } from '@/components/patient-avatar'
import { ApiError, createApiClient, type MealPlan, type MealPlanItem, type PatientProfile, type ReplacementCandidate } from '@/lib/api'
import { getToken } from '@/lib/auth'
import { notifyReviewQueueChanged } from '@/lib/review-queue'
import styles from './page.module.css'

const SLOT_ORDER = ['breakfast', 'lunch', 'snack', 'dinner']
const SLOT_LABEL: Record<string, string> = { breakfast: 'Bữa sáng', lunch: 'Bữa trưa', snack: 'Bữa phụ', dinner: 'Bữa tối' }
const SLOT_TIME: Record<string, string> = { breakfast: '07:00', lunch: '12:00', snack: '15:30', dinner: '18:30' }
// FE-13: trước đó breakfast/lunch dùng chung icon 'sun', và 'moon' gán cho snack (15:30, giữa chiều)
// thay vì dinner (18:30, chập tối) — 4 icon khác nhau, gán đúng ngữ nghĩa thời điểm trong ngày.
const MEAL_ICON: Record<string, string> = { breakfast: 'sun', lunch: 'bowl', snack: 'sparkle', dinner: 'moon' }
const CHECKS = [['energy', 'Năng lượng'], ['carb', 'Carbohydrate'], ['distribution', 'Phân bổ bữa'], ['gi', 'GI/GL'], ['allergy', 'Dị ứng']]
const POLL_DELAYS_MS = [0, 200, 400, 800, 1200, 1800]
const POLL_ATTEMPTS = 40

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
  const [swapItem, setSwapItem] = useState<MealPlanItem | null>(null)
  const [candidates, setCandidates] = useState<ReplacementCandidate[]>([])
  const [selectedCandidate, setSelectedCandidate] = useState<ReplacementCandidate | null>(null)
  const [conflictPlan, setConflictPlan] = useState<MealPlan | null>(null)
  const [swapping, setSwapping] = useState(false)
  const [comboOpen, setComboOpen] = useState(false)

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

  async function generate() {
    const token = getToken()
    if (!token || !patientId) return
    setGenerating(true); setError(''); setNotice(''); setPlan(null); setPlanId(''); setConflictPlan(null)
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
          setError('Không thể tạo phương án an toàn với cấu hình này. Bản xử lý vẫn được lưu để chuyên gia xem nguyên nhân.')
          return
        }
        setPlan(current)
        if (current.status === 'pending_review') notifyReviewQueueChanged()
        if (current.status === 'manual_review_required') setNotice('Cổng an toàn đang chặn bản này. Hãy mở màn hình duyệt để xem vấn đề cần xử lý.')
        else if (current.review_packet?.can_approve === false) setNotice('Phương án đã lưu nhưng chưa đủ điều kiện duyệt. Các lý do được hiển thị trong phần kiểm tra.')
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
      setError(value instanceof ApiError ? value.message : value instanceof Error ? value.message : 'Không thể tạo phương án.')
      setGenerating(false)
    }
  }

  const blockedReasons = plan ? [...(plan.review_packet?.target_gate_reasons ?? []), ...plan.safety_findings.filter(finding => finding.risk_level === 'P0').map(finding => finding.message_vi)] : []
  const target = (key: string) => { const item = plan?.targets?.targets?.[key]; return item?.max_value ?? item?.min_value ?? null }
  const kcal = plan?.computed_nutrition?.kcal
  const carb = plan?.computed_nutrition?.carb_g
  const hasViolation = (term: string) => plan?.violations.some(item => (item.nutrient || '').toLowerCase().includes(term) || (item.message_vi || '').toLowerCase().includes(term))

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
      <div><div className={styles.breadcrumb}><Link href="/dietitian">Tổng quan</Link><Icon name="chevronRight"/><span>Tạo thực đơn</span></div><h1>Tạo thực đơn cá nhân hóa</h1><p>Chọn bệnh nhân, kiểm tra đầu vào rồi tạo phương án để chuyên gia xem và duyệt.</p></div>
      <div className={styles.headerMeta}><span><Icon name="database"/>Dữ liệu có nguồn</span><span><Icon name="shield"/>Cổng an toàn server</span></div>
    </header>

    <section className={styles.workflow} aria-label="Quy trình tạo thực đơn">
      {/* FE-16: nhãn trạng thái trước đây lẫn lộn phạm trù ngữ pháp (quá khứ/điều kiện/vị trí:
          "Đã chọn"/"Khi tạo"/"Bước hiện tại"/"Bước tiếp") — đổi thành 1 bộ từ vựng trạng thái
          nhất quán để đọc lướt nhanh hơn, không cần đổi cấu trúc 2 tầng nhãn. */}
      {[['profile','Hồ sơ','Hoàn tất'],['target','Mục tiêu',plan?'Hoàn tất':'Chờ tạo'],['sparkles','Tạo & kiểm tra',generating?'Đang xử lý':plan?'Hoàn tất':'Sẵn sàng tạo'],['profile','Chuyên gia duyệt',plan?'Chờ duyệt':'Chưa tới']].map(([icon,title,state],index)=><article className={`${index===2?styles.current:''} ${index<2||plan?styles.complete:''}`} key={title}><span><Icon name={icon}/><i>{index+1}</i></span><div><small>{state}</small><strong>{title}</strong></div>{index<3&&<Icon name="arrowRight"/>}</article>)}
    </section>

    {/* Thiết kế lại theo mẫu 2 tầng phổ biến ở các dashboard (Stripe customer page, Linear
        issue header): tầng 1 = tìm/chọn hồ sơ (compact, không chiếm hết chiều rộng); tầng 2 =
        thanh định danh + hành động chính (Mở hồ sơ 360) TÁCH RIÊNG khỏi lưới dữ liệu lâm sàng
        (Thuốc/Dị ứng/Khẩu vị) — trước đây cả 4 nhóm bị ép chung 1 hàng ngang, gây mật độ cao. */}
    <section className={styles.caseBand}>
      <div className={styles.caseSelect}>
        <label htmlFor="patient-search">TÌM HỒ SƠ LẬP KẾ HOẠCH</label>
        {/* Combobox gộp: hồ sơ đang chọn hiện thành chip trong ô search thay vì dropdown
            riêng bên dưới — 1 điểm tương tác duy nhất thay vì 2 điều khiển tách rời. */}
        <div className={styles.combo}>
          {selected && !comboOpen && <span className={styles.comboChip}>ID: {selected.id.slice(0,8).toUpperCase()} · {selected.sex==='male'?'Nam':'Nữ'}, {selected.age} tuổi<button type="button" onClick={()=>{setPatientId('');setComboOpen(true)}} aria-label="Bỏ chọn hồ sơ"><Icon name="close"/></button></span>}
          <input id="patient-search" value={patientSearch} onChange={event=>{setPatientSearch(event.target.value);setComboOpen(true)}} onFocus={()=>setComboOpen(true)} onBlur={()=>window.setTimeout(()=>setComboOpen(false),150)} placeholder={selected?'Tìm hồ sơ khác…':'Mã hồ sơ, email, bệnh lý hoặc thuốc'} autoComplete="off"/>
          {comboOpen && (loading ? <div className={styles.comboList}><div className={styles.inlineLoading}>Đang tìm hồ sơ…</div></div> : patients.length>0 && <ul className={styles.comboList} role="listbox" aria-label="Kết quả hồ sơ">{patients.map(patient=><li key={patient.id} role="option" aria-selected={patient.id===patientId}><button type="button" onMouseDown={event=>event.preventDefault()} onClick={()=>{setPatientId(patient.id);setComboOpen(false);resetDraftContext()}}>ID: {patient.id.slice(0,8).toUpperCase()} · {patient.sex==='male'?'Nam':'Nữ'}, {patient.age} tuổi{patient.conditions.length?` · ${patient.conditions.map(item=>item.code).join(', ')}`:''}</button></li>)}</ul>)}
        </div>
      </div>
      {selected ? <div className={styles.caseSelected}>
        <div className={styles.caseIdentityRow}>
          <div className={styles.caseIdentity}>
            {/* Vòng trạng thái quanh avatar phản ánh "có điều cần chú ý" dựa trên dữ liệu thật
                (dị ứng đã ghi nhận) — KHÔNG phải phán đoán "kiểm soát bệnh tốt/xấu", vì hệ
                thống chưa có field đó và đây là kết luận lâm sàng cần R2 duyệt trước. */}
            <span className={`${styles.avatarRing} ${selected.allergies.length?styles.avatarRingAlert:styles.avatarRingOk}`}>
              <PatientAvatar sex={selected.sex}/>
              {selected.allergies.length>0 && <i className={styles.avatarBadge}><Icon name="warning"/></i>}
            </span>
            <div>
              <strong>{selected.conditions.map(item=>item.code).join(' · ') || 'Chưa ghi nhận bệnh nền'}</strong>
              <p>{selected.sex==='male'?'Nam':'Nữ'} · {selected.age} tuổi · {selected.height_cm} cm · {selected.weight_kg} kg</p>
              <small>MÃ HỒ SƠ {selected.id.slice(0,8).toUpperCase()}</small>
            </div>
          </div>
          <Link className={styles.caseOpenLink} href={`/dietitian/patients/${selected.id}`}>Mở hồ sơ 360<Icon name="arrowRight"/></Link>
        </div>
        <div className={styles.caseFacts}>
          <article><span><Icon name="scale"/></span><div><small>THUỐC</small><strong>{selected.medications.join(', ') || 'Không ghi nhận'}</strong></div></article>
          <article className={selected.allergies.length?styles.factAlert:undefined}><span><Icon name="warning"/></span><div><small>DỊ ỨNG</small><strong>{selected.allergies.join(', ') || 'Không ghi nhận'}</strong></div></article>
          <article><span><Icon name="bowl"/></span><div><small>KHẨU VỊ</small><strong>{selected.region ? `Miền ${selected.region==='north'?'Bắc':selected.region==='central'?'Trung':'Nam'}` : 'Món Việt'}</strong></div></article>
        </div>
      </div> : <div className={styles.noPatient}>Chưa có hồ sơ để lập kế hoạch.</div>}
    </section>

    <div className={styles.workspace}>
      <main className={styles.canvas}>
        <section className={styles.briefCard}>
          <header><div><small>THIẾT LẬP THỰC ĐƠN</small><h2>Thông tin cho lần tạo này</h2></div></header>
          <div className={styles.briefControls}><label>Ngày áp dụng<div><Icon name="calendar"/><input type="date" value={date} onChange={event=>{setDate(event.target.value);resetDraftContext()}}/></div></label><label>Cấu trúc bữa<select value="3+1" disabled><option>3 bữa chính + 1 bữa phụ</option></select></label><label>Ưu tiên khẩu vị<select value={selected?.region ?? 'vn'} disabled><option value="vn">Món Việt Nam</option><option value="north">Miền Bắc</option><option value="central">Miền Trung</option><option value="south">Miền Nam</option></select></label></div>
          <div className={styles.generateRow}><div><strong>Số liệu dinh dưỡng luôn được tính lại chính xác</strong><p>Hệ thống tự tính và kiểm tra ngưỡng cho từng món, không suy đoán hay ước lượng.</p></div><button type="button" onClick={()=>void generate()} disabled={!patientId||generating||Boolean(plan)}><Icon name="sparkles"/>{generating?'Đang tạo & kiểm tra…':plan?'Đã có phương án':'Tạo phương án'}</button></div>
          {generating&&<div className={styles.processing}><span className="spinner"/><div><strong>Tác vụ đang chạy trên backend</strong><p>Đang chọn món, tính dinh dưỡng và kiểm tra an toàn. Không gửi lại yêu cầu trong lúc chờ.</p></div><small>Không giả lập % tiến độ</small></div>}
          {error&&<div className={styles.error} role="alert"><Icon name="warning"/><div><strong>Chưa hoàn tất yêu cầu</strong><p>{error}</p></div>{planId&&<button type="button" onClick={()=>router.push(`/dietitian/reviews/${planId}`)}>Mở bản #{planId.slice(0,8).toUpperCase()}</button>}</div>}
          {conflictPlan&&<div className={styles.conflict}><Icon name="info"/><div><strong>Ngày này đã có một bản đang xử lý</strong><p>#{conflictPlan.id.slice(0,8).toUpperCase()} · {conflictPlan.status}. Không tạo trùng.</p></div><button type="button" onClick={()=>router.push(`/dietitian/reviews/${conflictPlan.id}`)}>Mở bản hiện có</button></div>}
          {notice&&<div className={styles.warningNotice}><Icon name="warning"/>{notice}</div>}
        </section>

        <section className={styles.draftCard}>
          <header><div><small>PHƯƠNG ÁN HIỆN TẠI</small><h2>{plan?`Thực đơn #${plan.id.slice(0,8).toUpperCase()}`:'Bản xem trước thực đơn'}</h2></div></header>
          {!plan&&!generating&&<div className={styles.draftEmpty}><span><Icon name="bowl"/></span><h3>Canvas đang chờ phương án</h3><p>Kiểm tra hồ sơ và planning brief phía trên, sau đó nhấn “Tạo phương án”.</p></div>}
          {generating&&<div className={styles.draftEmpty}><span className="spinner"/><h3>Đang chuẩn bị cấu trúc bữa</h3><p>Kết quả thật sẽ xuất hiện khi backend hoàn thành.</p></div>}
          {plan&&!plan.items.length&&<div className={styles.blocked}><Icon name="warning"/><div><strong>Chưa có món để hiển thị</strong>{blockedReasons.length?<ul>{blockedReasons.map(reason=><li key={reason}>{reason}</li>)}</ul>:<p>Bản nháp đã lưu. Mở màn hình duyệt để xem dữ liệu server đã ghi.</p>}</div></div>}
          {plan&&plan.items.length>0&&<div className={styles.mealGrid}>{SLOT_ORDER.map(slot=><MealSlot key={slot} slot={slot} items={grouped[slot]??[]} onSwap={item=>void openSwap(item)}/>)}</div>}
          {plan&&<footer className={styles.draftFooter}><div><Icon name="info"/><span>Phương án này chưa được phát hành. Chuyên gia có thể đổi từng món và kiểm tra lại trước khi duyệt.</span></div><button type="button" onClick={()=>router.push(`/dietitian/reviews/${plan.id}`)}>Xem toàn bộ căn cứ<Icon name="arrowRight"/></button></footer>}
        </section>
      </main>

      <aside className={styles.evidenceRail}>
        <section className={styles.evidenceCard}>
          <header><small>CLINICAL EVIDENCE RAIL</small><h2>Kiểm tra trước duyệt</h2><p>Mọi trạng thái bên dưới đến từ dữ liệu backend.</p></header>
          <div className={styles.checkList}>{CHECKS.map(([key,label])=>{const verified=Boolean(plan?.review_packet&&Object.keys(plan.review_packet).length&&plan.menu_hash_ready&&plan.nutrition_hash_ready);const warning=Boolean(plan&&(key==='carb'?hasViolation('carb'):key==='allergy'?hasViolation('dị ứng'):false));let detail=verified?'Đã kiểm tra':'Chờ phương án';if(plan&&key==='energy')detail=kcal?`${Math.round(kcal)}${target('kcal')?` / ${Math.round(target('kcal')!)} kcal`:' kcal'}`:'Chưa tính';if(plan&&key==='carb')detail=carb?`${Math.round(carb)}${target('carb_g')?` / ${Math.round(target('carb_g')!)} g`:' g'}`:'Chưa tính';return <article key={key}><span className={warning?styles.stateWarn:verified?styles.stateOk:styles.stateIdle}><Icon name={warning?'warning':verified?'check':'info'}/></span><div><strong>{label}</strong><small>{detail}</small></div><b className={warning?styles.textWarn:verified?styles.textOk:styles.textIdle}>{warning?'Lưu ý':verified?'Đạt':'Chờ'}</b></article>})}</div>
          <div className={styles.drugCheck} role={plan&&plan.violations.some(item=>item.kind?.includes('interaction'))?'alert':undefined}><header><span><Icon name="warning"/></span><div><strong>Thuốc – thực phẩm</strong><small>{plan&&plan.violations.some(item=>item.kind?.includes('interaction'))?'Có điểm cần xem':'Kiểm tra khi có phương án'}</small></div></header><p>{selected?.medications.length?`${selected.medications.join(', ')} sẽ được đối chiếu với món và thời điểm dùng.`:'Hồ sơ chưa ghi nhận thuốc đang dùng.'}</p></div>
          <div className={styles.trace}><Icon name="database"/><div><strong>Có thể truy xuất nguồn</strong><p>Món, gram, dinh dưỡng và quyết định được gắn với đúng phiên bản.</p></div></div>
          <div className={styles.constraintRow}><small>RÀNG BUỘC ĐANG ÁP DỤNG</small><div><span><Icon name="bowl"/>Món Việt</span><span><Icon name="profile"/>Theo hồ sơ</span><span><Icon name="scale"/>Gram chuẩn</span><span><Icon name="shield"/>{selected?.allergies.length?'Tránh dị ứng':'Không dị ứng'}</span></div></div>
        </section>
      </aside>
    </div>

    <footer className={styles.actionBar}><div><span><Icon name="warning"/></span><p><strong>Chưa phát hành cho người bệnh</strong><small>Chỉ phiên bản được duyệt mới xuất hiện ở không gian bệnh nhân.</small></p></div><button type="button" disabled={!planId||generating} onClick={()=>planId&&router.push(`/dietitian/reviews/${planId}`)}>{plan?'Chuyển sang màn hình duyệt':'Mở bản đã lưu'}<Icon name="arrowRight"/></button></footer>

    {swapItem&&<SwapDrawer item={swapItem} candidates={candidates} selected={selectedCandidate} busy={swapping} onSelect={setSelectedCandidate} onClose={()=>!swapping&&setSwapItem(null)} onApply={candidate=>void replaceItem(candidate)}/>}
  </div>
}

function MealSlot({slot,items,onSwap}:{slot:string;items:MealPlanItem[];onSwap:(item:MealPlanItem)=>void}) {
  const grams=items.reduce((sum,item)=>sum+item.grams,0)
  return <section className={`${styles.mealSlot} ${styles[slot]}`}><header><div><span><Icon name={MEAL_ICON[slot]}/></span><div><small>{SLOT_TIME[slot]}</small><h3>{SLOT_LABEL[slot]}</h3></div></div><b>{Math.round(grams)} g</b></header><div>{items.length?items.map(item=><article key={item.id}><div><strong>{item.name_vi}</strong><small title={item.source_ref||undefined}>{Math.round(item.grams)} g · Nguồn: {item.source||'chưa rõ'}</small></div><button type="button" onClick={()=>onSwap(item)}><Icon name="refresh"/>Đổi</button></article>):<p className={styles.noItems}>Không có món ở khung bữa này.</p>}</div></section>
}

function SwapDrawer({item,candidates,selected,busy,onSelect,onClose,onApply}:{item:MealPlanItem;candidates:ReplacementCandidate[];selected:ReplacementCandidate|null;busy:boolean;onSelect:(value:ReplacementCandidate)=>void;onClose:()=>void;onApply:(value:ReplacementCandidate)=>void}) {
  return <div className={styles.swapBackdrop} role="presentation" onMouseDown={onClose}><section className={styles.swapPanel} role="dialog" aria-modal="true" aria-label="Đổi món" onMouseDown={event=>event.stopPropagation()}><header><div><small>ĐỔI MÓN · {SLOT_LABEL[item.slot]}</small><h2>Xem trước thay đổi</h2><p>Chỉ ghi thay đổi sau khi bạn xác nhận. Backend sẽ tính lại dinh dưỡng và an toàn.</p></div><button type="button" onClick={onClose} aria-label="Đóng"><Icon name="close"/></button></header><div className={styles.swapCompare}><article><small>HIỆN TẠI</small><strong>{item.name_vi}</strong><span>{Math.round(item.grams)} g</span></article><Icon name="arrowRight"/><article><small>THAY THẾ</small><strong>{selected?.name_vi||'Chưa chọn món'}</strong><span>{selected?`${Math.round(selected.serving_g)} g`:'Chọn ứng viên bên dưới'}</span></article></div><section className={styles.candidates}><header><h3>Món cùng vai trò trong bữa</h3><span>{candidates.length} ứng viên</span></header>{candidates.length?candidates.map(candidate=><button type="button" className={selected?.dish_id===candidate.dish_id?styles.candidateSelected:undefined} key={candidate.dish_id} disabled={busy} onClick={()=>onSelect(candidate)}><span><strong>{candidate.name_vi}</strong><small>{candidate.region?`Khẩu vị ${candidate.region}`:'Phù hợp toàn quốc'}</small></span><b>{Math.round(candidate.serving_g)} g</b><Icon name="chevronRight"/></button>):<div className={styles.candidateEmpty}><span className="spinner"/>Đang tải hoặc chưa có món phù hợp.</div>}</section><footer><button type="button" onClick={onClose}>Hủy</button><button type="button" disabled={!selected||busy} onClick={()=>selected&&onApply(selected)}>{busy?'Đang tính lại…':'Áp dụng & kiểm tra lại'}<Icon name="arrowRight"/></button></footer></section></div>
}
