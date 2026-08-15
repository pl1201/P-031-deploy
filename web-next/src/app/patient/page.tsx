'use client'

import Link from 'next/link'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { GuidedTour, type TourStep } from '@/components/guided-tour'
import { Icon } from '@/components/brand-artwork'
import { ApiError, createApiClient, type FoodLog, type MealPlan, type MealPlanItem, type PatientProfile } from '@/lib/api'
import { getToken } from '@/lib/auth'
import styles from './patient.module.css'

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
  { selector: '[data-tour="log-action"]', eyebrow: 'Bước 3/4', title: 'Xác nhận bữa theo kế hoạch', description: 'Báo đã ăn đủ, ăn một phần, ăn món khác hoặc bỏ bữa. Món ăn thêm được ghi tại mục Món đã ăn.' },
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

  async function submitMeal(mode: LogMode, ratio: number, differentFood: string) {
    if (!profile || !plan || !logSlot) return
    const token = getToken()
    if (!token) return
    setSaving(true)
    setError('')
    try {
      const api = createApiClient(token)
      const items = groups[logSlot] ?? []
      if (mode === 'different') {
        await api.createFoodLog({ profile_id: profile.id, free_text_vi: differentFood.trim(), slot: logSlot, note_vi: `Món ăn khác với thực đơn #${plan.id.slice(0, 8)}` })
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
      setLogs(await api.listFoodLogs(profile.id, todayISO()))
      setLogSlot(null)
      setNotice(`Đã ghi nhận ${SLOT_META[logSlot].label.toLowerCase()}.`)
      window.setTimeout(() => setNotice(''), 3200)
    } catch (value) {
      setError(value instanceof ApiError ? value.message : 'Không thể lưu ghi nhận.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <PatientSkeleton />

  return (
    <div className={styles.page}>
      <header className={styles.header} data-tour="today-plan">
        <div>
          <span className={styles.kicker}>KHÔNG GIAN CHĂM SÓC</span>
          <h1>{profile ? `Chào ${profile.sex === 'male' ? 'anh' : 'chị'} trở lại` : 'Thực đơn hôm nay'}</h1>
          <p>{formatDate(todayISO())}</p>
        </div>
        {plan && <button className={styles.primary} type="button" data-tour="log-action" onClick={() => setLogSlot(currentSlot)}><Icon name="diary" />Xác nhận bữa theo kế hoạch</button>}
      </header>

      {error && <div className={styles.error} role="alert"><Icon name="warning" /><div><strong>Chưa thể tải đầy đủ dữ liệu</strong><p>{error}</p></div><button type="button" onClick={() => void load()}>Thử lại</button></div>}
      {notice && <div className={styles.toast} role="status"><Icon name="check" />{notice}</div>}
      {plan && (groups[currentSlot] ?? []).length > 0 && !loggedSlots.has(currentSlot) && (
        <ReminderBanner slot={currentSlot} onLog={() => setLogSlot(currentSlot)} />
      )}

      {!plan ? (
        <section className={styles.empty}>
          <span><Icon name="bowl" /></span>
          <h2>Chưa có thực đơn được phát hành</h2>
          <p>Bạn chỉ nhìn thấy thực đơn sau khi hệ thống hoàn tất kiểm tra và đáp ứng policy phê duyệt.</p>
          <Link href="/patient/diary">Mở nhật ký ăn uống</Link>
        </section>
      ) : (
        <>
          <section className={styles.planStatus}>
            <div className={styles.approvalMark}><Icon name="check" /></div>
            <div><small>THỰC ĐƠN ĐANG ÁP DỤNG</small><strong>Đã kiểm tra và phát hành</strong><p>Ngày áp dụng {new Date(`${plan.plan_date}T00:00:00`).toLocaleDateString('vi-VN')} · Phiên bản {plan.menu_version}</p></div>
            <span>#{plan.id.slice(0, 8)}</span>
          </section>

          <div className={styles.layout}>
            <main className={styles.mainColumn}>
              <section className={styles.meals} data-tour="meal-timeline">
                <div className={styles.sectionHeading}><div><small>KẾ HOẠCH TRONG NGÀY</small><h2>Hôm nay bạn ăn gì?</h2></div><span>{completed}/{SLOTS.filter(slot => (groups[slot] ?? []).length).length} bữa đã ghi nhận</span></div>
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
              </section>

              <section className={styles.why}>
                <div className={styles.sectionHeading}><div><small>GIẢI THÍCH CÁ NHÂN HÓA</small><h2>Vì sao phù hợp với bạn?</h2></div><Icon name="shield" /></div>
                <div className={styles.reasonGrid}>
                  <Reason icon="chart" title="Theo mục tiêu dinh dưỡng" text="Năng lượng và carbohydrate được backend tính lại từ dữ liệu thực phẩm có nguồn." />
                  <Reason icon="shield" title="Đã kiểm tra hồ sơ" text={profile?.allergies.length ? `Đã đối chiếu ${profile.allergies.length} dị ứng đang ghi nhận.` : 'Hồ sơ hiện chưa ghi nhận dị ứng thực phẩm.'} />
                  <Reason icon="heart" title="Gần thói quen ăn uống" text={profile?.region ? `Ưu tiên khẩu vị vùng ${profile.region === 'north' ? 'Bắc' : profile.region === 'central' ? 'Trung' : 'Nam'}.` : 'Sử dụng cấu trúc bữa ăn Việt Nam quen thuộc.'} />
                </div>
              </section>
            </main>

            <aside className={styles.sideColumn}>
              <section className={styles.nutrition}>
                <div className={styles.sectionHeading}><div><small>TỔNG NGÀY</small><h2>Dinh dưỡng kế hoạch</h2></div><Icon name="chart" /></div>
                {plan.computed_nutrition && isNumber(plan.computed_nutrition.kcal) ? (
                  <>
                    <div className={styles.energy}><strong>{Math.round(plan.computed_nutrition.kcal).toLocaleString('vi-VN')}</strong><span>kcal</span></div>
                    <MacroChart carbG={plan.computed_nutrition.carb_g} proteinG={plan.computed_nutrition.protein_g} fatG={plan.computed_nutrition.fat_g} fiberG={plan.computed_nutrition.fiber_g} />
                    <p><Icon name="database" />Số liệu do backend tính từ nguồn dinh dưỡng đã lưu.</p>
                  </>
                ) : <div className={styles.compactEmpty}>Chưa đủ dữ liệu để hiển thị tổng dinh dưỡng.</div>}
              </section>

              <section className={styles.week} data-tour="weekly-progress">
                <div className={styles.sectionHeading}><div><small>TIẾN ĐỘ HÔM NAY</small><h2>{completed}/{Math.max(1, SLOTS.filter(slot => (groups[slot] ?? []).length).length)} bữa</h2></div><span>{Math.round(completed / Math.max(1, SLOTS.filter(slot => (groups[slot] ?? []).length).length) * 100)}%</span></div>
                <div className={styles.progress}><i style={{ width: `${completed / Math.max(1, SLOTS.filter(slot => (groups[slot] ?? []).length).length) * 100}%` }} /></div>
                <p>Ghi nhận trung thực giúp chuyên gia hiểu điều gì phù hợp với sinh hoạt thực tế của bạn.</p>
                <Link href="/patient/weekly">Xem tổng hợp tuần <Icon name="arrowRight" /></Link>
              </section>

              <section className={styles.note}>
                <span><Icon name="message" /></span><div><small>ĐỒNG HÀNH CÙNG CHUYÊN GIA</small><h2>Không cần báo cáo từng bữa riêng</h2><p>Hệ thống sẽ tổng hợp theo tuần và làm nổi các điểm cần chuyên gia chú ý.</p></div>
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

const SLOT_ICON: Record<Slot, string> = { breakfast: 'sun', lunch: 'bowl', snack: 'sparkle', dinner: 'moon' }

function ReminderBanner({ slot, onLog }: { slot: Slot; onLog: () => void }) {
  return (
    <div className={styles.reminder} role="status">
      <span><Icon name={SLOT_ICON[slot]} /></span>
      <div><strong>Đến giờ {SLOT_META[slot].label.toLowerCase()} rồi!</strong><p>Ghi lại ngay để giữ chuỗi ngày theo dõi liên tục — chỉ mất chưa đến 20 giây.</p></div>
      <button type="button" onClick={onLog}>Ghi nhận ngay<Icon name="arrowRight" /></button>
    </div>
  )
}

// FE: thay bảng số liệu dinh dưỡng (Carbohydrate/Protein/Chất béo dạng chữ) bằng biểu đồ
// thanh xếp chồng theo tỉ lệ calo — dễ đọc lướt hơn 1 danh sách 4 con số cùng cỡ chữ.
// Chất xơ không tính calo theo cùng cách nên tách thành nhãn phụ, không gộp vào thanh.
function MacroChart({ carbG, proteinG, fatG, fiberG }: { carbG: number; proteinG: number; fatG: number; fiberG: number }) {
  const carbKcal = isNumber(carbG) ? carbG * 4 : 0
  const proteinKcal = isNumber(proteinG) ? proteinG * 4 : 0
  const fatKcal = isNumber(fatG) ? fatG * 9 : 0
  const total = carbKcal + proteinKcal + fatKcal
  const parts = [
    { key: 'carb', label: 'Carb', grams: carbG, kcal: carbKcal, className: styles.macroCarb },
    { key: 'protein', label: 'Đạm', grams: proteinG, kcal: proteinKcal, className: styles.macroProtein },
    { key: 'fat', label: 'Béo', grams: fatG, kcal: fatKcal, className: styles.macroFat },
  ]
  return (
    <div className={styles.macroChart}>
      {total > 0 && <div className={styles.macroBar}>{parts.map(part => part.kcal > 0 && <i key={part.key} className={part.className} style={{ width: `${(part.kcal / total) * 100}%` }} />)}</div>}
      <div className={styles.macroLegend}>
        {parts.map(part => (
          <div key={part.key}><i className={part.className} /><small>{part.label}</small><strong>{isNumber(part.grams) ? Math.round(part.grams) : '—'} g</strong><span>{total > 0 ? `${Math.round((part.kcal / total) * 100)}%` : ''}</span></div>
        ))}
        <div><i className={styles.macroFiber} /><small>Xơ</small><strong>{isNumber(fiberG) ? Math.round(fiberG) : '—'} g</strong><span /></div>
      </div>
    </div>
  )
}

function MealDrawer({ slot, items, plan, onClose, onLog }: { slot: Slot; items: MealPlanItem[]; plan: MealPlan; onClose: () => void; onLog: () => void }) {
  return <div className={styles.modalLayer} role="dialog" aria-modal="true" aria-label={`Chi tiết ${SLOT_META[slot].label}`}><button className={styles.modalScrim} type="button" onClick={onClose} aria-label="Đóng" /><aside className={styles.drawer}><header><div><small>{SLOT_META[slot].time} · KẾ HOẠCH ĐÃ PHÁT HÀNH</small><h2>{SLOT_META[slot].label}</h2></div><button type="button" onClick={onClose} aria-label="Đóng"><Icon name="close" /></button></header><div className={`${styles.mealArtwork} ${styles[SLOT_META[slot].tone]}`}><Icon name="bowl" /><span>{items.length} thành phần</span></div><section><h3>Khẩu phần đề xuất</h3>{items.map(item=><article className={styles.drawerItem} key={item.id}><span><Icon name="bowl" /></span><div><strong>{item.name_vi}</strong><small>{Math.round(item.grams)} g{item.ingredients.length ? ` · ${item.ingredients.length} nguyên liệu` : ''}</small></div><span title={item.source_ref || item.source || 'Nguồn dữ liệu món ăn'}><Icon name="database" /></span></article>)}</section><details><summary>Vì sao bữa này được chọn?<Icon name="chevronDown" /></summary><p>{plan.explanation_vi || 'Bữa ăn nằm trong phương án đã được tính dinh dưỡng và kiểm tra an toàn trước khi phát hành.'}</p></details><details><summary>Nguồn dữ liệu món ăn<Icon name="chevronDown" /></summary><ul>{items.map(item=><li key={item.id}><strong>{item.name_vi}</strong><span>{item.source_ref || item.source}</span></li>)}</ul></details><footer><button type="button" className={styles.secondary} onClick={onClose}>Đóng</button><button type="button" className={styles.primary} onClick={onLog}><Icon name="diary" />Ghi nhận bữa ăn</button></footer></aside></div>
}

function LogMealModal({ slot, items, saving, onClose, onSubmit }: { slot: Slot; items: MealPlanItem[]; saving: boolean; onClose: () => void; onSubmit: (mode: LogMode, ratio: number, differentFood: string) => Promise<void> }) {
  const [mode, setMode] = useState<LogMode>('full')
  const [ratio, setRatio] = useState(.5)
  const [different, setDifferent] = useState('')
  const valid = mode !== 'different' || different.trim().length > 1
  return <div className={styles.modalLayer} role="dialog" aria-modal="true" aria-label="Ghi nhận bữa ăn"><button className={styles.modalScrim} type="button" onClick={onClose} aria-label="Đóng" /><section className={styles.logModal}><header><div><small>NHẬT KÝ HÔM NAY</small><h2>Ghi nhận {SLOT_META[slot].label.toLowerCase()}</h2><p>{items.map(item=>item.name_vi).join(' · ')}</p></div><button type="button" onClick={onClose} aria-label="Đóng"><Icon name="close" /></button></header><div className={styles.modeGrid}>{[
    ['full','check','Ăn đủ','Theo đúng thực đơn'],['partial','chart','Ăn một phần','Ước lượng khẩu phần'],['different','refresh','Ăn món khác','Ghi món thực tế'],['skipped','clock','Bỏ bữa','Chưa ăn bữa này'],
  ].map(([value,icon,title,desc])=><button type="button" key={value} className={mode===value?styles.selected:undefined} onClick={()=>setMode(value as LogMode)}><Icon name={icon}/><strong>{title}</strong><small>{desc}</small></button>)}</div>{mode==='partial'&&<div className={styles.ratio}><label>Bạn đã ăn khoảng bao nhiêu?</label><div>{[[.25,'1/4'],[.5,'1/2'],[.75,'3/4']].map(([value,label])=><button type="button" key={String(value)} className={ratio===value?styles.selected:undefined} onClick={()=>setRatio(value as number)}>{label}</button>)}</div></div>}{mode==='different'&&<label className={styles.different}>Bạn thực tế đã ăn món gì?<input value={different} onChange={event=>setDifferent(event.target.value)} placeholder="VD: bún cá, 1 tô nhỏ" maxLength={255}/><small>Nếu chưa tra được món, hệ thống sẽ chuyển chuyên gia đối chiếu và không tự bịa số.</small></label>}{mode==='skipped'&&<p className={styles.skipNote}><Icon name="info"/>Bỏ bữa được ghi nhận để chuyên gia hiểu thói quen thực tế; đây không phải lỗi của bạn.</p>}<footer><button type="button" className={styles.secondary} onClick={onClose}>Hủy</button><button type="button" className={styles.primary} disabled={saving||!valid} onClick={()=>void onSubmit(mode,mode==='full'?1:ratio,different)}>{saving?'Đang lưu…':'Lưu ghi nhận'}<Icon name="arrowRight"/></button></footer></section></div>
}

function PatientSkeleton() {
  return <div className={styles.page}><div className={styles.skeletonHeader}><i/><i/></div><div className={styles.skeletonStatus}/><div className={styles.skeletonGrid}><section><i/><i/><i/><i/></section><aside><i/><i/></aside></div></div>
}
