'use client'

import Link from 'next/link'
import { Fragment, useCallback, useEffect, useMemo, useState } from 'react'
import { Icon } from '@/components/brand-artwork'
import { ApiError, createApiClient, type FoodLog, type MatchSuggestion, type MealPlan, type MealPlanItem } from '@/lib/api'
import { getToken } from '@/lib/auth'
import styles from '../secondary.module.css'

type DayData = { iso: string; logs: FoodLog[] }
const SLOT_ORDER = ['breakfast','lunch','snack','dinner']
const SLOT_LABEL:Record<string,string> = { breakfast:'Bữa sáng', lunch:'Bữa trưa', snack:'Bữa phụ', dinner:'Bữa tối' }
// Giờ mặc định khi ghi bù cho một ngày đã qua — khớp đúng khung giờ đã dùng ở trang tạo thực
// đơn (dietitian/meal-plans/new) để nhất quán trong toàn app.
const SLOT_TIME:Record<string,string> = { breakfast:'07:00', lunch:'12:00', snack:'15:30', dinner:'18:30' }
const SLOT_ICON:Record<string,string> = { breakfast:'sun', lunch:'bowl', snack:'sparkle', dinner:'moon' }
const SKIPPED_PREFIX = 'bỏ '

function logStatusLabel(log: FoodLog) {
  if ((log.free_text_vi ?? '').trim().toLocaleLowerCase('vi-VN').startsWith(SKIPPED_PREFIX)) return 'Đã báo bỏ bữa'
  if (log.match_status === 'unmatched' || log.match_status === 'no_data') return 'Chờ đối chiếu'
  return 'Đã tính vào tổng'
}

function todayIsoStr() { return new Date().toISOString().slice(0, 10) }
function isFiniteNumber(value: unknown): value is number { return typeof value === 'number' && Number.isFinite(value) }
function shiftDate(iso: string, deltaDays: number) {
  const date = new Date(`${iso}T00:00:00`)
  date.setDate(date.getDate() + deltaDays)
  return date.toISOString().slice(0, 10)
}
// So khớp món đã ghi với món trong thực đơn đã duyệt bằng food_id thật (không đoán theo tên) —
// "Ăn đúng" chỉ khi trùng đúng food_id, "Bỏ bữa" khi có tiền tố tự báo, còn lại là "Ăn khác".
function slotAdherence(logs: FoodLog[], plannedItems: MealPlanItem[]): 'match' | 'different' | 'skipped' {
  if (logs.some(log => (log.free_text_vi ?? '').toLocaleLowerCase('vi-VN').startsWith(SKIPPED_PREFIX))) return 'skipped'
  const allMatch = logs.every(log => log.food_id != null && plannedItems.some(item => item.food_id === log.food_id))
  return allMatch ? 'match' : 'different'
}

// Tuần thật (Thứ 2 → Chủ nhật) chứa ngày mốc — thay cho "7 ngày gần nhất tính đến hôm nay"
// trước đây, để lịch tháng nhỏ có thể điều hướng tới tuần bất kỳ, không chỉ tuần hiện tại.
function mondayOf(iso: string) {
  const date = new Date(`${iso}T00:00:00`)
  const day = date.getDay()
  date.setDate(date.getDate() + (day === 0 ? -6 : 1 - day))
  return date.toISOString().slice(0, 10)
}
function weekDaysFrom(anchorIso: string) {
  const start = new Date(`${mondayOf(anchorIso)}T00:00:00`)
  return Array.from({ length: 7 }, (_, index) => {
    const date = new Date(start)
    date.setDate(start.getDate() + index)
    return date.toISOString().slice(0, 10)
  })
}
function formatWeekRange(weekIsos: string[]) {
  const fmt = (iso: string) => new Date(`${iso}T00:00:00`).toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' })
  return `${fmt(weekIsos[0])} – ${fmt(weekIsos[6])}`
}

export default function PatientWeeklyPage() {
  const todayIso = todayIsoStr()
  const [profileId, setProfileId] = useState('')
  const [weekAnchor, setWeekAnchor] = useState(todayIso)
  const [days, setDays] = useState<DayData[]>([])
  const [weekPlans, setWeekPlans] = useState<Record<string, MealPlan>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeIso, setActiveIso] = useState(todayIso)
  const [popup, setPopup] = useState<{ iso: string; slot: string } | null>(null)

  const weekIsos = useMemo(() => weekDaysFrom(weekAnchor), [weekAnchor])

  useEffect(() => {
    const token = getToken()
    if (!token) return
    createApiClient(token).getMyProfile().then(me => setProfileId(me.id))
      .catch(value => setError(value instanceof ApiError ? value.message : 'Không thể tải hồ sơ.'))
  }, [])

  useEffect(() => {
    if (!profileId) return
    const token = getToken()
    if (!token) return
    const timer = window.setTimeout(() => {
      setLoading(true)
      const api = createApiClient(token)
      Promise.all([
        Promise.all(weekIsos.map(async iso => ({ iso, logs: await api.listFoodLogs(profileId, iso) }))),
        api.listMealPlans(undefined, 'approved'),
      ]).then(([dayResults, planResult]) => {
        setDays(dayResults)
        const byDate: Record<string, MealPlan> = {}
        for (const plan of planResult.items) if (weekIsos.includes(plan.plan_date)) byDate[plan.plan_date] = plan
        setWeekPlans(byDate)
      }).catch(value => setError(value instanceof ApiError ? value.message : 'Không thể tải tổng hợp tuần.'))
        .finally(() => setLoading(false))
    }, 0)
    return () => window.clearTimeout(timer)
  }, [profileId, weekIsos])

  const refreshDay = useCallback(async (iso: string) => {
    const token = getToken()
    if (!token || !profileId) return
    const logs = await createApiClient(token).listFoodLogs(profileId, iso)
    setDays(current => current.map(day => day.iso === iso ? { ...day, logs } : day))
  }, [profileId])

  function pickWeek(iso: string) {
    setWeekAnchor(iso)
    setActiveIso(iso)
  }
  function jumpToday() {
    pickWeek(todayIso)
  }

  const stats = useMemo(() => {
    const activeDays = days.filter(day => day.logs.length > 0).length
    const slots = days.flatMap(day => [...new Set(day.logs.map(log => log.slot).filter(Boolean))])
    const skipped = days.flatMap(day => day.logs).filter(log => log.free_text_vi?.toLowerCase().startsWith('bỏ ')).length
    const unmatched = days.flatMap(day => day.logs).filter(log => log.match_status === 'unmatched').length
    // "Quá hạn": ngày đã qua (không tính hôm nay, chưa xong nên chưa thể coi là bỏ lỡ) mà chưa có ghi nhận nào.
    const overdue = days.filter(day => day.iso < todayIso && day.logs.length === 0).length
    return { activeDays, slots: slots.length, skipped, unmatched, overdue }
  }, [days, todayIso])

  if (loading && days.length === 0) return <div className={styles.page}><div className={styles.skeleton}/></div>

  const activeDay = days.find(day => day.iso === activeIso)
  const isCurrentWeek = weekIsos.includes(todayIso)

  return <div className={styles.page}>
    <header className={styles.header}><div><small>TỔNG HỢP THEO TUẦN</small><h1>Tuần của bạn</h1><p>Hệ thống tổng hợp nhật ký để làm nổi những điểm đáng chú ý; chuyên gia không cần xem từng bữa riêng lẻ.</p></div><Link href="/patient/diary"><Icon name="diary"/>Xem báo cáo dinh dưỡng</Link></header>
    <div className={styles.weekNav}>
      <button type="button" onClick={() => pickWeek(shiftDate(weekAnchor, -7))}><Icon name="arrowLeft"/>Tuần trước</button>
      <span className={styles.weekNavLabel}><Icon name="calendar"/>Tuần: {formatWeekRange(weekIsos)}</span>
      <button type="button" onClick={() => pickWeek(shiftDate(weekAnchor, 7))}>Tuần sau<Icon name="arrowRight"/></button>
      {!isCurrentWeek && <button type="button" className={styles.weekNavReset} onClick={jumpToday}>Về tuần hiện tại</button>}
      <span className={styles.weekNavNote}><Icon name="shield"/>Món có thực đơn đã duyệt sẽ hiện kèm trạng thái ăn đúng/ăn khác</span>
    </div>
    {error&&<div className={styles.error}>{error}</div>}
    <div className={styles.grid}>
      <section className={styles.card}>
        <div className={styles.cardTitle}><div><small>{formatWeekRange(weekIsos)}</small><h2>Thời khoá biểu bữa ăn</h2></div><span>{stats.activeDays>=5?'Khá đầy đủ':'Cần thêm dữ liệu'}</span></div>

        {/* Desktop: lưới 4 buổi × 7 ngày, mỗi ô hiện luôn tên món — ẩn dưới 720px (xem .mobileWeek). */}
        <div className={styles.timetable}>
          <div className={styles.ttCorner}/>
          {days.map(day => {
            const date = new Date(`${day.iso}T00:00:00`)
            const isToday = day.iso === todayIso
            const nutrition = weekPlans[day.iso]?.computed_nutrition
            return <div key={day.iso} className={`${styles.ttDayHead}${isToday?` ${styles.ttToday}`:''}`}>
              <small>{date.toLocaleDateString('vi-VN',{weekday:'short'})}</small><b>{date.getDate()}/{date.getMonth()+1}</b>
              {nutrition && isFiniteNumber(nutrition.kcal) && <span className={styles.ttDayNutri}>{Math.round(nutrition.kcal)} kcal{isFiniteNumber(nutrition.na_mg)?` · ${Math.round(nutrition.na_mg)}mg Na`:''}</span>}
            </div>
          })}
          {SLOT_ORDER.map(slot => <Fragment key={slot}>
            <div className={`${styles.ttSlotHead} ${styles[`s${slot}`]}`}><span className={styles.ttSlotIcon}><Icon name={SLOT_ICON[slot]}/></span><div><small>{SLOT_TIME[slot]}</small><span>{SLOT_LABEL[slot]}</span></div></div>
            {days.map(day => {
              const plannedItems = weekPlans[day.iso]?.items.filter(item => item.slot === slot) ?? []
              const slotLogs = day.logs.filter(log => log.slot === slot)
              const isToday = day.iso === todayIso
              const isFuture = day.iso > todayIso
              const hasContent = plannedItems.length > 0 || slotLogs.length > 0
              return <button type="button" key={`${day.iso}-${slot}`} disabled={isFuture && !hasContent}
                className={`${styles.ttCell} ${styles[`s${slot}`]} ${hasContent?styles.ttCellDone:styles.ttCellEmpty}${isToday?` ${styles.ttToday}`:''}${isFuture?` ${styles.ttCellFuture}`:''}`}
                onClick={() => setPopup({ iso: day.iso, slot })}>
                {plannedItems.length ? (
                  <div className={styles.ttPlanned}>
                    <ul className={styles.ttList}>{plannedItems.map(item => <li key={item.id}>{item.name_vi} <b>{Math.round(item.grams)}g</b></li>)}</ul>
                    {slotLogs.length ? <AdherenceTag status={slotAdherence(slotLogs, plannedItems)}/> : <small className={styles.tagIdle}>Chưa ghi nhận</small>}
                  </div>
                ) : slotLogs.length ? (
                  <div className={styles.ttPlanned}><ul className={styles.ttList}>{slotLogs.map(log => <li key={log.id}>{log.food_name_vi||log.free_text_vi||'—'}{log.grams!=null && <b> {Math.round(log.grams)}g</b>}</li>)}</ul><small className={styles.tagOk}><Icon name="check"/>Đã ghi nhận</small></div>
                ) : (
                  <span className={styles.ttPlus}>{isFuture?'Chưa tới':'Chưa ghi · Thêm món'}</span>
                )}
              </button>
            })}
          </Fragment>)}
        </div>

        {/* Mobile: dải chọn ngày ngang + 4 ô buổi ăn xếp dọc cho đúng 1 ngày — chỉ hiện dưới 720px. */}
        <div className={styles.mobileWeek}>
          <div className={styles.dayStrip}>{days.map(day => {
            const date = new Date(`${day.iso}T00:00:00`)
            const isToday = day.iso === todayIso
            const loggedSlots = new Set(day.logs.map(log => log.slot)).size
            return <button type="button" key={day.iso}
              className={`${styles.dayChip}${day.iso===activeIso?` ${styles.dayChipActive}`:''}${isToday?` ${styles.dayChipToday}`:''}`}
              onClick={() => setActiveIso(day.iso)}>
              <small>{date.toLocaleDateString('vi-VN',{weekday:'short'})}</small><b>{date.getDate()}</b><i>{loggedSlots}/4</i>
            </button>
          })}</div>
          <div className={styles.slotList}>{SLOT_ORDER.map(slot => {
            const plannedItems = weekPlans[activeIso]?.items.filter(item => item.slot === slot) ?? []
            const slotLogs = activeDay?.logs.filter(log => log.slot === slot) ?? []
            const isFuture = activeIso > todayIso
            const hasContent = plannedItems.length > 0 || slotLogs.length > 0
            return <button type="button" key={slot} disabled={isFuture && !hasContent} className={`${styles.slotCard} ${styles[`s${slot}`]}`} onClick={() => setPopup({ iso: activeIso, slot })}>
              <div><small>{SLOT_TIME[slot]}</small><strong>{SLOT_LABEL[slot]}</strong></div>
              {plannedItems.length ? (
                <div className={styles.ttPlanned}>
                  <ul className={styles.ttList}>{plannedItems.map(item => <li key={item.id}>{item.name_vi} <b>{Math.round(item.grams)}g</b></li>)}</ul>
                  {slotLogs.length ? <AdherenceTag status={slotAdherence(slotLogs, plannedItems)}/> : <small className={styles.tagIdle}>Chưa ghi nhận</small>}
                </div>
              ) : slotLogs.length ? (
                <div className={styles.ttPlanned}><ul className={styles.ttList}>{slotLogs.map(log => <li key={log.id}>{log.food_name_vi||log.free_text_vi||'—'}{log.grams!=null && <b> {Math.round(log.grams)}g</b>}</li>)}</ul><small className={styles.tagOk}><Icon name="check"/>Đã ghi nhận</small></div>
              ) : (
                <span className={styles.ttPlus}>{isFuture?'Chưa tới':'Chưa ghi · Thêm món'}</span>
              )}
            </button>
          })}</div>
        </div>
      </section>
      <aside className={styles.weeklyInsights}>
        <section className={styles.card}><div className={styles.cardTitle}><div><small>ĐIỂM CẦN CHÚ Ý</small><h2>Gợi ý cho tuần này</h2></div></div>
        <div className={styles.miniStats}>
          <article><small>TÓM TẮT</small><strong>{stats.activeDays}/7 ngày</strong></article>
          <article><small>BỮA ĐÃ GHI</small><strong>{stats.slots}</strong></article>
          <article><small>BỎ BỮA</small><strong>{stats.skipped}</strong></article>
          <article><small>CHỜ ĐỐI CHIẾU</small><strong>{stats.unmatched}</strong></article>
        </div>
        <div className={styles.insights}>
          {stats.overdue>0 && <Insight icon="warning" title={`${stats.overdue} ngày chưa có ghi nhận nào`} text="Những ngày này đã qua nhưng chưa được ghi lại — hãy bổ sung nếu bạn còn nhớ, hoặc để trống nếu thực sự chưa ăn gì được ghi." urgent/>}
          <Insight icon="diary" title="Duy trì ghi nhận" text={stats.activeDays<5?'Bạn chưa có đủ 5 ngày dữ liệu. Hãy ghi nhận ngắn gọn, không cần nhớ chính xác mọi gram.':'Dữ liệu đã đủ để tạo một bản tóm tắt có ý nghĩa.'}/>
          <Insight icon="warning" title="Dữ liệu chưa đối chiếu" text={stats.unmatched?`${stats.unmatched} món chưa tra được nên chưa được cộng vào tổng dinh dưỡng.`:'Các món đã ghi hiện không có dòng chờ đối chiếu.'}/>
          <Insight icon="clock" title="Nhịp bữa ăn" text={stats.skipped?`Bạn đã báo bỏ ${stats.skipped} bữa. Chuyên gia sẽ xem xu hướng thay vì đánh giá từng lần.`:'Chưa ghi nhận bữa bị bỏ trong tuần này.'}/>
        </div></section>
      </aside>
    </div>
    {popup && <CellPopup iso={popup.iso} slot={popup.slot} profileId={profileId}
      logs={days.find(day => day.iso === popup.iso)?.logs.filter(log => log.slot === popup.slot) ?? []}
      plannedItems={weekPlans[popup.iso]?.items.filter(item => item.slot === popup.slot) ?? []}
      onClose={() => setPopup(null)}
      onSaved={() => void refreshDay(popup.iso)}/>}
  </div>
}

function Insight({icon,title,text,urgent}:{icon:string;title:string;text:string;urgent?:boolean}){return <article className={urgent?styles.insightUrgent:undefined} role={urgent?'alert':undefined}><span><Icon name={icon}/></span><div><h3>{title}</h3><p>{text}</p></div></article>}

function AdherenceTag({status}:{status:'match'|'different'|'skipped'}) {
  if (status === 'match') return <small className={styles.tagOk}><Icon name="check"/>Ăn đúng</small>
  if (status === 'skipped') return <small className={styles.tagWarn}>Bỏ bữa</small>
  return <small className={styles.tagWarn}><Icon name="refresh"/>Ăn khác</small>
}

// Popup theo Ô (ngày + buổi cụ thể), không còn theo cả ngày — khớp đúng cách lưới thời khoá
// biểu chia nhỏ tới từng bữa. Vừa xem món đã ghi, vừa ghi thêm ngay tại đây, kể cả cho ngày đã
// qua (logged_at gửi đúng ngày của ô, không phải "bây giờ").
function CellPopup({iso,slot,logs,plannedItems,profileId,onClose,onSaved}:{iso:string;slot:string;logs:FoodLog[];plannedItems:MealPlanItem[];profileId:string;onClose:()=>void;onSaved:()=>void}) {
  const [text,setText] = useState('')
  const [grams,setGrams] = useState('')
  const [suggestions,setSuggestions] = useState<MatchSuggestion[]>([])
  const [selectedFoodId,setSelectedFoodId] = useState<number|null>(null)
  const [noSuitableMatch,setNoSuitableMatch] = useState(false)
  const [suggesting,setSuggesting] = useState(false)
  const [saving,setSaving] = useState(false)
  const [error,setError] = useState('')
  const [notice,setNotice] = useState('')

  useEffect(() => {
    if (text.trim().length < 2) return
    const token = getToken()
    if (!token) return
    const timer = window.setTimeout(() => {
      setSuggesting(true)
      createApiClient(token).suggestFoods(text.trim()).then(result => setSuggestions(result.suggestions)).catch(() => setSuggestions([])).finally(() => setSuggesting(false))
    }, 300)
    return () => window.clearTimeout(timer)
  }, [text])

  function changeText(value: string) {
    setText(value); setSelectedFoodId(null); setNoSuitableMatch(false)
    if (value.trim().length < 2) setSuggestions([])
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    if (!text.trim() || !profileId) return
    if (suggestions.length && !selectedFoodId && !noSuitableMatch) { setError('Hãy chọn món phù hợp hoặc xác nhận món không có trong danh sách.'); return }
    setSaving(true); setError('')
    try {
      await createApiClient(getToken()!).createFoodLog({
        profile_id: profileId,
        free_text_vi: text.trim(),
        food_id: selectedFoodId,
        grams: grams ? Number(grams) : null,
        slot,
        logged_at: `${iso}T${SLOT_TIME[slot]}:00`,
      })
      setText(''); setGrams(''); setSuggestions([]); setSelectedFoodId(null); setNoSuitableMatch(false)
      setNotice('Đã ghi nhận.')
      onSaved()
      window.setTimeout(() => setNotice(''), 2400)
    } catch (value) {
      setError(value instanceof ApiError ? value.message : 'Không thể lưu nhật ký.')
    } finally {
      setSaving(false)
    }
  }

  const date = new Date(`${iso}T00:00:00`)
  return <div className={styles.modalLayer} role="presentation">
    <button type="button" className={styles.modalScrim} onClick={onClose} aria-label="Đóng ô ghi nhận"/>
    <div className={styles.cellPopup} role="dialog" aria-modal="true" aria-label={`${SLOT_LABEL[slot]} · ${date.toLocaleDateString('vi-VN')}`}>
      <header><div><small>{SLOT_LABEL[slot].toUpperCase()} · {SLOT_TIME[slot]}</small><h3>{date.toLocaleDateString('vi-VN',{weekday:'long',day:'2-digit',month:'2-digit'})}</h3></div><button type="button" onClick={onClose} aria-label="Đóng"><Icon name="close"/></button></header>

      {plannedItems.length>0 && <div className={styles.plannedBlock}><small>THỰC ĐƠN ĐÃ DUYỆT CHO BỮA NÀY</small><ul>{plannedItems.map(item => <li key={item.id}><strong>{item.name_vi}</strong><span>{Math.round(item.grams)} g</span></li>)}</ul></div>}

      {logs.length>0 && <ul className={styles.cellExisting}>{logs.map(log => <li key={log.id}><strong>{log.food_name_vi||log.free_text_vi||'Chưa rõ tên món'}</strong>{log.grams!=null && <span>{Math.round(log.grams)} g</span>}<small>{logStatusLabel(log)}</small></li>)}</ul>}

      {error && <div className={styles.error} role="alert">{error}</div>}
      {notice && <div className={styles.notice} role="status" aria-live="polite">{notice}</div>}

      <form className={styles.cellForm} onSubmit={submit}>
        <label><span>{logs.length?'Ghi thêm món khác':'Tên món'}</span><input value={text} onChange={event => changeText(event.target.value)} placeholder="VD: cơm tẻ, canh rau muống, cá kho…" maxLength={255} autoComplete="off"/></label>
        {(suggesting||suggestions.length>0) && <div className="diary-suggestion-panel" aria-live="polite">
          <div><strong>{suggesting?'Đang tìm món phù hợp…':'Bạn muốn nói đến món nào?'}</strong>{!suggesting && <small>Chọn đúng loại để hệ thống không phải đoán.</small>}</div>
          {!suggesting && <div className="diary-suggestion-list">
            {suggestions.map(item => <button type="button" key={item.food_id} className={selectedFoodId===item.food_id?'selected':undefined} onClick={() => { setSelectedFoodId(item.food_id); setNoSuitableMatch(false) }}><span>{item.name_vi}</span><small>{Math.round(item.score*100)}% phù hợp</small></button>)}
            <button type="button" className={noSuitableMatch?'selected':undefined} onClick={() => { setNoSuitableMatch(true); setSelectedFoodId(null) }}><span>Không có trong danh sách</span><small>Chuyển chuyên gia đối chiếu</small></button>
          </div>}
        </div>}
        <div className={styles.cellFormRow}>
          <label><span>Khẩu phần gram</span><input type="number" value={grams} onChange={event => setGrams(event.target.value)} min="1" max="5000" placeholder="Có thể để trống"/></label>
          <button type="submit" disabled={saving||suggesting||!text.trim()}>{saving?'Đang lưu…':'Ghi vào bữa'}<Icon name="arrowRight"/></button>
        </div>
      </form>

      <details className={styles.handRef}>
        <summary>Gợi ý khẩu phần theo &quot;đơn vị bàn tay&quot;</summary>
        <ul>
          <li><b>Tinh bột</b><span>¾ bát cơm · hoặc 1 bát phở/bún nhỏ · hoặc ½ gói xôi · hoặc 1 củ khoai nhỏ</span></li>
          <li><b>Đạm</b><span>1 lòng bàn tay — cá, gà bỏ da, thịt nạc, tôm, đậu phụ</span></li>
          <li><b>Rau</b><span>ít nhất 2 nắm tay lớn</span></li>
          <li><b>Trái cây</b><span>1 quả nhỏ hoặc 1 nắm tay, ăn nguyên quả — không ép nước</span></li>
          <li><b>Dầu</b><span>1 thìa cà phê mỗi món</span></li>
        </ul>
      </details>

      <button type="button" className={styles.cellPhoto} disabled title="Cần hạ tầng lưu trữ ảnh — chưa triển khai">
        <Icon name="document"/>Thêm ảnh minh hoạ (sắp có)
      </button>
    </div>
  </div>
}
