'use client'

import Link from 'next/link'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { GuidedTour, type TourStep } from '@/components/guided-tour'
import { Icon } from '@/components/brand-artwork'
import { CalorieRing } from '@/components/calorie-ring'
import { MacroTrio } from '@/components/macro-trio'
import { ApiError, createApiClient, type DaySummary, type FoodLog, type MatchSuggestion, type MealPlan, type MealPlanItem, type PatientProfile } from '@/lib/api'
import { getToken } from '@/lib/auth'
import styles from './patient.module.css'
import simple from './patient-simple.module.css'

const STREAK_WINDOW_DAYS = 14

const SLOTS = ['breakfast', 'lunch', 'snack', 'dinner'] as const
type Slot = typeof SLOTS[number]
type LogMode = 'full' | 'partial' | 'different' | 'skipped'

const SLOT_META: Record<Slot, { label: string; time: string; tone: string }> = {
  breakfast: { label: 'Bữa sáng', time: '07:00', tone: 'sunrise' },
  lunch: { label: 'Bữa trưa', time: '12:00', tone: 'day' },
  snack: { label: 'Bữa phụ', time: '15:30', tone: 'snack' },
  dinner: { label: 'Bữa tối', time: '18:30', tone: 'night' },
}

const TOUR: TourStep[] = [
  { selector: '[data-tour="today-plan"]', eyebrow: 'Bước 1/4', title: 'Đây là thực đơn hôm nay', description: 'Chỉ thực đơn đã được phát hành mới xuất hiện trong không gian người bệnh.' },
  { selector: '[data-tour="meal-timeline"]', eyebrow: 'Bước 2/4', title: 'Mở một bữa để xem khẩu phần', description: 'Mỗi bữa cho biết món, gram và nguồn dữ liệu. Nhấn vào card để mở chi tiết.' },
  { selector: '[data-tour="log-action"]', eyebrow: 'Bước 3/4', title: 'Xác nhận bữa theo kế hoạch', description: 'Báo đã ăn đủ, ăn một phần, ăn món khác hoặc bỏ bữa. Muốn ghi cho ngày khác, mở mục Tuần của tôi.' },
  { selector: '[data-tour="weekly-progress"]', eyebrow: 'Bước 4/4', title: 'Theo dõi theo tuần', description: 'Các ghi nhận được tổng hợp để chuyên gia chỉ chú ý khi có vấn đề đáng quan tâm.' },
]

function todayISO() { return new Date().toISOString().slice(0, 10) }
function formatDate(value: string) { return new Date(`${value}T00:00:00`).toLocaleDateString('vi-VN', { weekday: 'long', day: '2-digit', month: '2-digit', year: 'numeric' }) }
function isNumber(value: unknown): value is number { return typeof value === 'number' && Number.isFinite(value) }

export default function PatientDashboard() {
  const [profile, setProfile] = useState<PatientProfile | null>(null)
  const [plan, setPlan] = useState<MealPlan | null>(null)
  const [logs, setLogs] = useState<FoodLog[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedSlot, setSelectedSlot] = useState<Slot | null>(null)
  const [logSlot, setLogSlot] = useState<Slot | null>(null)
  const [saving, setSaving] = useState(false)
  const [notice, setNotice] = useState('')
  const [streak, setStreak] = useState<number | null>(null)
  const [todaySummary, setTodaySummary] = useState<DaySummary | null>(null)

  const load = useCallback(async () => {
    const token = getToken()
    if (!token) return
    try {
      const api = createApiClient(token)
      const [me, plans] = await Promise.all([api.getMyProfile(), api.listMealPlans(undefined, 'approved')])
      const today = todayISO()
      const approved = [...plans.items]
        .filter(item => item.plan_date <= today)
        .sort((a, b) => b.plan_date.localeCompare(a.plan_date))[0] ?? null
      setProfile(me)
      setPlan(approved)
      setLogs(await api.listFoodLogs(me.id, todayISO()))

      // Streak kiểu MyFitnessPal: số ngày liên tục (tính từ hôm nay lùi lại) có ít
      // nhất 1 lần ghi nhận. Chỉ soi trong 1 cửa sổ cố định (không quét vô hạn) —
      // cùng cách tiếp cận diary/page.tsx đã dùng cho biểu đồ 7 ngày.
      const windowIsos = Array.from({ length: STREAK_WINDOW_DAYS }, (_, i) => {
        const d = new Date(); d.setDate(d.getDate() - i); return d.toISOString().slice(0, 10)
      })
      const summaries = await Promise.all(windowIsos.map(iso => api.getDaySummary(me.id, iso).catch(() => null)))
      setTodaySummary(summaries[0] ?? null)
      let count = 0
      for (const summary of summaries) {
        if (summary && summary.matched_count + summary.unmatched_count > 0) count++
        else break
      }
      setStreak(count)
    } catch (value) {
      setError(value instanceof ApiError ? value.message : 'Không thể tải không gian chăm sóc.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { const timer=window.setTimeout(()=>void load(),0);return()=>window.clearTimeout(timer) }, [load])

  const groups = useMemo(() => {
    return plan?.items.reduce<Record<string, MealPlanItem[]>>((acc, item) => {
      ;(acc[item.slot] ??= []).push(item)
      return acc
    }, {}) ?? {}
  }, [plan])

  const loggedSlots = useMemo(() => new Set(logs.map(log => log.slot).filter(Boolean)), [logs])
  const completed = SLOTS.filter(slot => loggedSlots.has(slot)).length
  const currentSlot = useMemo<Slot>(() => {
    const hour = new Date().getHours()
    if (hour < 10) return 'breakfast'
    if (hour < 14) return 'lunch'
    if (hour < 17) return 'snack'
    return 'dinner'
  }, [])
  const plannedSlots = useMemo(() => SLOTS.filter(slot => (groups[slot] ?? []).length > 0), [groups])
  const nextSlot = useMemo<Slot | null>(() => {
    const currentIndex = SLOTS.indexOf(currentSlot)
    return plannedSlots.find(slot => SLOTS.indexOf(slot) >= currentIndex && !loggedSlots.has(slot))
      ?? plannedSlots.find(slot => !loggedSlots.has(slot))
      ?? null
  }, [currentSlot, loggedSlots, plannedSlots])
  const plannedCompleted = plannedSlots.filter(slot => loggedSlots.has(slot)).length
  const progressPercent = plannedSlots.length ? Math.round((plannedCompleted / plannedSlots.length) * 100) : 0

  async function submitMeal(mode: LogMode, ratio: number, differentFood: string, differentFoodId: number | null, differentGrams: number | null) {
    if (!profile || !plan || !logSlot) return
    const token = getToken()
    if (!token) return
    setSaving(true)
    setError('')
    try {
      const api = createApiClient(token)
      const items = groups[logSlot] ?? []
      if (mode === 'different') {
        await api.createFoodLog({ profile_id: profile.id, free_text_vi: differentFood.trim(), food_id: differentFoodId, grams: differentGrams, slot: logSlot, note_vi: `Món ăn khác với thực đơn #${plan.id.slice(0, 8)}` })
      } else if (mode === 'skipped') {
        await api.createFoodLog({ profile_id: profile.id, free_text_vi: `Bỏ ${SLOT_META[logSlot].label.toLowerCase()}`, slot: logSlot, note_vi: `Người bệnh báo bỏ bữa; plan_id=${plan.id}` })
      } else {
        await Promise.all(items.map(item => api.createFoodLog({
          profile_id: profile.id,
          free_text_vi: item.name_vi,
          grams: Math.max(1, Math.round(item.grams * ratio)),
          slot: logSlot,
          note_vi: `${mode === 'full' ? 'Ăn đủ' : `Ước lượng ${Math.round(ratio * 100)}%`} theo thực đơn #${plan.id.slice(0, 8)}`,
        })))
      }
      const [updatedLogs, updatedSummary] = await Promise.all([
        api.listFoodLogs(profile.id, todayISO()),
        api.getDaySummary(profile.id, todayISO()),
      ])
      setLogs(updatedLogs)
      setTodaySummary(updatedSummary)
      setStreak(current => Math.max(1, current ?? 0))
      setLogSlot(null)
      setNotice(`Đã ghi nhận ${SLOT_META[logSlot].label.toLowerCase()}.`)
      window.setTimeout(() => setNotice(''), 3200)
    } catch (value) {
      setError(value instanceof ApiError ? value.message : 'Không thể lưu ghi nhận.')
    } finally {
      setSaving(false)
    }
  }

  const kcalVerdict = todaySummary?.verdicts.find(v => v.nutrient === 'kcal') ?? null
  const consumedKcal = kcalVerdict?.counted ?? 0
  const targetKcal = kcalVerdict?.max_value ?? plan?.targets.targets.kcal?.max_value ?? null
  const welcomeMessage = currentSlot === 'breakfast'
    ? 'Bắt đầu ngày mới bằng một bữa ăn phù hợp với bạn.'
    : currentSlot === 'lunch'
      ? 'Một ghi nhận nhỏ sau bữa trưa sẽ giúp kế hoạch sát với bạn hơn.'
      : currentSlot === 'snack'
        ? 'Chiều nay bạn chỉ cần ghi đúng những gì mình đã ăn.'
        : 'Khép lại hôm nay bằng một ghi nhận thật đơn giản.'

  if (loading) return <PatientSkeleton />

  return (
    <div className={styles.page}>
      <header className={`${styles.header} ${simple.welcomeCard}`} data-tour="today-plan">
        <span className={simple.welcomeGlow} aria-hidden="true" />
        <div>
          <span className={styles.kicker}>HÔM NAY CỦA BẠN</span>
          <h1>{welcomeMessage}</h1>
          <p>{formatDate(todayISO())} · Mỗi ghi nhận đều giúp chuyên gia hiểu bạn hơn.</p>
        </div>
      </header>

      {error && <div className={styles.error} role="alert"><Icon name="warning" /><div><strong>Chưa thể tải đầy đủ dữ liệu</strong><p>{error}</p></div><button type="button" onClick={() => void load()}>Thử lại</button></div>}
      {notice && <div className={styles.toast} role="status"><Icon name="check" />{notice}</div>}

      {!plan ? (
        <section className={styles.empty}>
          <span><Icon name="bowl" /></span>
          <h2>Chưa có thực đơn được phát hành</h2>
          <p>Bạn chỉ nhìn thấy thực đơn sau khi hệ thống hoàn tất kiểm tra và đáp ứng policy phê duyệt.</p>
          <Link href="/patient/weekly">Ghi món đã ăn</Link>
        </section>
      ) : (
        <>
          <div className={styles.layout}>
            <main className={styles.mainColumn}>
              <section className={styles.meals} data-tour="meal-timeline">
                <div className={styles.sectionHeading}><div><small>KẾ HOẠCH TRONG NGÀY</small><h2>Hôm nay bạn ăn gì?</h2></div><span>{completed}/{SLOTS.filter(slot => (groups[slot] ?? []).length).length} bữa đã ghi nhận</span></div>
                <div className={`${styles.todayHero} ${simple.todayHero}`} data-tour="today-hero">
                  <CalorieRing consumedKcal={consumedKcal} targetKcal={targetKcal} />
                  <div className={simple.planNutrition}>
                    <div className={simple.planNutritionHeading}>
                      <div><small>KẾ HOẠCH HÔM NAY</small><strong>{plan.computed_nutrition && isNumber(plan.computed_nutrition.kcal) ? Math.round(plan.computed_nutrition.kcal).toLocaleString('vi-VN') : '—'} <span>kcal</span></strong></div>
                      {streak != null && streak > 0 && <span><Icon name="sparkle" />{streak} ngày liên tục</span>}
                    </div>
                    {plan.computed_nutrition && isNumber(plan.computed_nutrition.kcal) ? <MacroTrio carbG={plan.computed_nutrition.carb_g} proteinG={plan.computed_nutrition.protein_g} fatG={plan.computed_nutrition.fat_g} fiberG={plan.computed_nutrition.fiber_g} /> : <p className={styles.heroNote}>Chưa đủ dữ liệu để hiển thị dinh dưỡng kế hoạch.</p>}
                  </div>
                </div>
                <div className={styles.timeline}>
                  {SLOTS.map(slot => {
                    const items = groups[slot] ?? []
                    if (!items.length) return null
                    const meta = SLOT_META[slot]
                    const done = loggedSlots.has(slot)
                    return (
                      <article key={slot} className={`${styles.meal} ${styles[meta.tone]}${slot === currentSlot ? ` ${styles.current}` : ''}`}>
                        <div className={styles.time}><strong>{meta.time}</strong><span>{done ? <Icon name="check" /> : <i />}</span></div>
                        <button type="button" className={styles.mealBody} onClick={() => setSelectedSlot(slot)}>
                          <small>{meta.label}{slot === currentSlot ? ' · Bữa hiện tại' : ''}</small>
                          <h3>{items.map(item => item.name_vi).join(' · ')}</h3>
                          <p>{Math.round(items.reduce((sum, item) => sum + item.grams, 0))} g tổng khẩu phần · {items.length} thành phần</p>
                        </button>
                        <div className={styles.mealActions}>
                          <span className={done ? styles.done : styles.pending}>{done ? 'Đã ghi nhận' : 'Chưa ghi nhận'}</span>
                          <button type="button" onClick={() => setLogSlot(slot)}>{done ? 'Ghi thêm' : 'Ghi nhận'}<Icon name="chevronRight" /></button>
                        </div>
                      </article>
                    )
                  })}
                </div>
                <div className={simple.honestLog} data-tour="log-action">
                  <span><Icon name="message" /></span>
                  <div><strong>Bạn ăn món khác hoặc bỏ bữa?</strong><p>Hãy cho chúng tôi biết. Ghi đúng thực tế sẽ giúp chuyên gia hỗ trợ bạn tốt hơn.</p></div>
                  <button type="button" onClick={() => setLogSlot(currentSlot)}>Cho chúng tôi biết</button>
                </div>
              </section>

              <section className={styles.why}>
                <div className={styles.sectionHeading}><div><small>GIẢI THÍCH CÁ NHÂN HÓA</small><h2>Vì sao phù hợp với bạn?</h2></div><Icon name="shield" /></div>
                <div className={styles.reasonGrid}>
                  <Reason icon="chart" title="Theo mục tiêu dinh dưỡng" text="Lượng calo và tinh bột được tính đúng từ dữ liệu thực phẩm có nguồn gốc rõ ràng, không phải ước lượng." />
                  <Reason icon="shield" title="Đã kiểm tra hồ sơ" text={profile?.allergies.length ? `Đã đối chiếu ${profile.allergies.length} dị ứng đang ghi nhận.` : 'Hồ sơ hiện chưa ghi nhận dị ứng thực phẩm.'} />
                  <Reason icon="heart" title="Gần thói quen ăn uống" text={profile?.region ? `Ưu tiên khẩu vị vùng ${profile.region === 'north' ? 'Bắc' : profile.region === 'central' ? 'Trung' : 'Nam'}.` : 'Sử dụng cấu trúc bữa ăn Việt Nam quen thuộc.'} />
                </div>
              </section>
            </main>

            <aside className={styles.sideColumn}>
              <section className={simple.nextAction} aria-labelledby="next-action-title">
                <div className={simple.nextActionTopline}>
                  <span className={simple.nextActionIcon}><Icon name={nextSlot ? 'diary' : 'check'} /></span>
                  <span>{progressPercent}% hôm nay</span>
                </div>
                <small>{nextSlot ? 'VIỆC TIẾP THEO' : 'HÔM NAY ĐÃ XONG'}</small>
                <h2 id="next-action-title">{nextSlot ? `Ghi lại ${SLOT_META[nextSlot].label.toLowerCase()}` : 'Bạn đã ghi đủ các bữa'}</h2>
                <p>{nextSlot
                  ? `${SLOT_META[nextSlot].time} · ${(groups[nextSlot] ?? []).map(item => item.name_vi).join(' · ')}`
                  : 'Cảm ơn bạn đã ghi đúng những gì mình ăn. Chuyên gia sẽ dựa vào dữ liệu này để đồng hành cùng bạn.'}</p>
                <div className={simple.nextProgress} aria-label={`Đã ghi ${plannedCompleted} trên ${plannedSlots.length} bữa`}>
                  <i style={{ width: `${progressPercent}%` }} />
                </div>
                {nextSlot ? (
                  <button type="button" onClick={() => setLogSlot(nextSlot)}>Ghi bữa này<Icon name="arrowRight" /></button>
                ) : (
                  <Link href="/patient/weekly">Xem lại hôm nay<Icon name="arrowRight" /></Link>
                )}
                <span className={simple.nextActionHint}>{nextSlot ? 'Bạn vẫn có thể báo ăn một phần, món khác hoặc bỏ bữa.' : `${plannedCompleted}/${plannedSlots.length} bữa đã được ghi nhận.`}</span>
              </section>
              <section className={simple.careNews} data-tour="weekly-progress">
                <header><div><small>BẢN TIN CHĂM SÓC</small><h2>Dành cho bạn</h2></div><span>{new Date().toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' })}</span></header>
                <Link href="/patient/weekly" className={simple.leadStory}>
                  <span><Icon name="trend" /></span>
                  <div><small>BÁO CÁO CỦA BẠN</small><strong>Nhìn lại một tuần ăn uống</strong><p>Xem những ngày đã ghi nhận và các bữa còn thiếu thông tin.</p></div>
                  <Icon name="arrowRight" />
                </Link>
                <div className={simple.newsList}>
                  <Link href="/patient/diary"><span><Icon name="chart" /></span><div><small>DINH DƯỠNG HÔM NAY</small><strong>{Math.round(consumedKcal).toLocaleString('vi-VN')} kcal đã ghi nhận</strong></div><Icon name="chevronRight" /></Link>
                  <Link href="/patient/activity"><span><Icon name="heart" /></span><div><small>GÓC KIẾN THỨC</small><strong>Hiểu đúng dữ liệu từ thiết bị sức khỏe</strong></div><Icon name="chevronRight" /></Link>
                </div>
                <footer><span>{completed} bữa đã ghi hôm nay</span><span>Nội dung từ dữ liệu của bạn</span></footer>
              </section>
            </aside>
          </div>
        </>
      )}

      {selectedSlot && plan && <MealDrawer slot={selectedSlot} items={groups[selectedSlot] ?? []} plan={plan} onClose={() => setSelectedSlot(null)} onLog={() => { setLogSlot(selectedSlot); setSelectedSlot(null) }} />}
      {logSlot && plan && <LogMealModal slot={logSlot} items={groups[logSlot] ?? []} saving={saving} onClose={() => !saving && setLogSlot(null)} onSubmit={submitMeal} />}
      <GuidedTour id="patient-dashboard-v2" steps={TOUR} />
    </div>
  )
}

function Reason({ icon, title, text }: { icon: string; title: string; text: string }) {
  return <article><span><Icon name={icon} /></span><div><h3>{title}</h3><p>{text}</p></div></article>
}

function MealDrawer({ slot, items, plan, onClose, onLog }: { slot: Slot; items: MealPlanItem[]; plan: MealPlan; onClose: () => void; onLog: () => void }) {
  return <div className={styles.modalLayer} role="dialog" aria-modal="true" aria-label={`Chi tiết ${SLOT_META[slot].label}`}><button className={styles.modalScrim} type="button" onClick={onClose} aria-label="Đóng" /><aside className={styles.drawer}><header><div><small>{SLOT_META[slot].time} · KẾ HOẠCH ĐÃ PHÁT HÀNH</small><h2>{SLOT_META[slot].label}</h2></div><button type="button" onClick={onClose} aria-label="Đóng"><Icon name="close" /></button></header><div className={`${styles.mealArtwork} ${styles[SLOT_META[slot].tone]}`}><Icon name="bowl" /><span>{items.length} món</span></div><section><h3>Khẩu phần đề xuất</h3>{items.map(item=><article className={styles.drawerItem} key={item.id}><span><Icon name="bowl" /></span><div><strong>{item.name_vi}</strong><small>{item.khau_phan_mo_ta ? `${item.khau_phan_mo_ta} · ` : ''}{Math.round(item.grams)} g{item.kcal != null ? ` · ${Math.round(item.kcal)} kcal` : ''}</small>{item.ingredients.length > 0 && <ul>{item.ingredients.map(ingredient=><li key={`${item.id}-${ingredient.food_id}`}><span>{ingredient.name_vi}</span><b>{Math.round(ingredient.grams)} g</b></li>)}</ul>}{!item.sugar_is_complete && <em role="status">Đường: chưa đủ số liệu để kết luận</em>}</div><span title={item.source_ref || item.source || 'Nguồn dữ liệu món ăn'}><Icon name="database" /></span></article>)}</section><details><summary>Vì sao bữa này được chọn?<Icon name="chevronDown" /></summary><p>{plan.explanation_vi || 'Bữa ăn nằm trong phương án đã được tính dinh dưỡng và kiểm tra an toàn trước khi phát hành.'}</p></details><details><summary>Nguồn dữ liệu món ăn<Icon name="chevronDown" /></summary><ul>{items.map(item=><li key={item.id}><strong>{item.name_vi}</strong><span>{item.source_ref || item.source}</span></li>)}</ul></details><footer><button type="button" className={styles.secondary} onClick={onClose}>Đóng</button><button type="button" className={styles.primary} onClick={onLog}><Icon name="diary" />Ghi nhận bữa ăn</button></footer></aside></div>
}

function LogMealModal({ slot, items, saving, onClose, onSubmit }: { slot: Slot; items: MealPlanItem[]; saving: boolean; onClose: () => void; onSubmit: (mode: LogMode, ratio: number, differentFood: string, differentFoodId: number | null, differentGrams: number | null) => Promise<void> }) {
  const [mode, setMode] = useState<LogMode>('full')
  const [ratio, setRatio] = useState(.5)
  const [different, setDifferent] = useState('')
  const [selectedFood, setSelectedFood] = useState<MatchSuggestion | null>(null)
  const [suggestions, setSuggestions] = useState<MatchSuggestion[]>([])
  const [searching, setSearching] = useState(false)
  const [grams, setGrams] = useState('150')
  const valid = mode !== 'different' || different.trim().length > 1

  // FE-23: flow tìm-chọn kiểu MyFitnessPal thay ô chữ tự do — gõ-lọc trong CSDL
  // món ăn (RULE-2: chỉ món có nguồn), vẫn giữ chữ tự do làm phương án cuối khi
  // không tìm thấy (RULE-2 "không biết thì nói không biết", không ép chọn bừa).
  useEffect(() => {
    // selectedFood/mode guard chỉ đọc, không setState ở đây — danh sách gợi ý cũ
    // (nếu còn) đã bị JSX ẩn qua điều kiện `!selectedFood` khi render, không cần
    // dọn tay để tránh cascading render trong effect.
    if (mode !== 'different' || selectedFood || different.trim().length < 2) return
    const token = getToken()
    if (!token) return
    const timer = window.setTimeout(() => {
      setSearching(true)
      createApiClient(token).suggestFoods(different.trim(), 6)
        .then(result => setSuggestions(result.suggestions))
        .catch(() => setSuggestions([]))
        .finally(() => setSearching(false))
    }, 300)
    return () => window.clearTimeout(timer)
  }, [different, mode, selectedFood])

  return <div className={styles.modalLayer} role="dialog" aria-modal="true" aria-label="Ghi nhận bữa ăn"><button className={styles.modalScrim} type="button" onClick={onClose} aria-label="Đóng" /><section className={styles.logModal}><header><div><small>NHẬT KÝ HÔM NAY</small><h2>Ghi nhận {SLOT_META[slot].label.toLowerCase()}</h2><p>{items.map(item=>item.name_vi).join(' · ')}</p></div><button type="button" onClick={onClose} aria-label="Đóng"><Icon name="close" /></button></header><div className={styles.modeGrid}>{[
    ['full','check','Ăn đủ','Theo đúng thực đơn'],['partial','chart','Ăn một phần','Ước lượng khẩu phần'],['different','refresh','Ăn món khác','Ghi món thực tế'],['skipped','clock','Bỏ bữa','Chưa ăn bữa này'],
  ].map(([value,icon,title,desc])=><button type="button" key={value} className={mode===value?styles.selected:undefined} onClick={()=>setMode(value as LogMode)}><Icon name={icon}/><strong>{title}</strong><small>{desc}</small></button>)}</div>{mode==='partial'&&<div className={styles.ratio}><label>Bạn đã ăn khoảng bao nhiêu?</label><div>{[[.25,'Ăn một chút'],[.5,'Ăn một nửa'],[.75,'Ăn gần hết']].map(([value,label])=><button type="button" key={String(value)} className={ratio===value?styles.selected:undefined} onClick={()=>setRatio(value as number)}>{label}</button>)}</div></div>}{mode==='different'&&<label className={styles.different}>Bạn thực tế đã ăn món gì?<input value={different} onChange={event=>{setDifferent(event.target.value);setSelectedFood(null)}} placeholder="Gõ để tìm món, VD: bún cá" maxLength={255}/>{searching&&<small>Đang tìm…</small>}{!selectedFood&&suggestions.length>0&&<ul className={styles.foodSuggestions}>{suggestions.map(item=><li key={item.food_id}><button type="button" onClick={()=>{setSelectedFood(item);setDifferent(item.name_vi);setSuggestions([])}}>{item.name_vi}</button></li>)}</ul>}{selectedFood&&<label className={styles.gramsInput}>Khẩu phần (gram)<input type="number" min={1} max={2000} value={grams} onChange={event=>setGrams(event.target.value)}/></label>}<small>{selectedFood?`Đã chọn từ CSDL món ăn có nguồn — nhập đúng gram để tính dinh dưỡng.`:'Nếu chưa tra được món, hệ thống sẽ chuyển chuyên gia đối chiếu và không tự bịa số.'}</small></label>}{mode==='skipped'&&<p className={styles.skipNote}><Icon name="info"/>Bỏ bữa được ghi nhận để chuyên gia hiểu thói quen thực tế; đây không phải lỗi của bạn.</p>}<footer><button type="button" className={styles.secondary} onClick={onClose}>Hủy</button><button type="button" className={styles.primary} disabled={saving||!valid} onClick={()=>void onSubmit(mode,mode==='full'?1:ratio,different,selectedFood?.food_id??null,selectedFood?Math.max(1,Math.round(Number(grams)||0)):null)}>{saving?'Đang lưu…':'Lưu ghi nhận'}<Icon name="arrowRight"/></button></footer></section></div>
}

function PatientSkeleton() {
  return <div className={styles.page}><div className={styles.skeletonHeader}><i/><i/></div><div className={styles.skeletonStatus}/><div className={styles.skeletonGrid}><section><i/><i/><i/><i/></section><aside><i/><i/></aside></div></div>
}
