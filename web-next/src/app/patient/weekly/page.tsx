'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'
import { Icon } from '@/components/brand-artwork'
import { ApiError, createApiClient, type FoodLog } from '@/lib/api'
import { getToken } from '@/lib/auth'
import styles from '../secondary.module.css'

type DayData = { iso: string; logs: FoodLog[] }
const SLOT_ORDER = ['breakfast','lunch','snack','dinner']
const SLOT_LABEL:Record<string,string> = { breakfast:'Bữa sáng', lunch:'Bữa trưa', snack:'Bữa phụ', dinner:'Bữa tối' }
const SKIPPED_PREFIX = 'bỏ '

// FE-12 (tầng 2, theo yêu cầu hiển thị món ăn trực tiếp): lưới 7 ngày chỉ trả lời "tuần này
// ghi đều không" — không nhồi tên món vào đó. Tên món chỉ hiện khi bấm vào 1 ngày, mở panel
// chi tiết bên dưới cho đúng ngày đó. Không tự động mở sẵn ngày nào để tránh lặp lại lỗi
// "hôm nay 0/4 bữa vẫn được nhấn mạnh hơn ngày có dữ liệu thật" đã ghi trong kế hoạch.
function logStatusLabel(log: FoodLog) {
  if ((log.free_text_vi ?? '').trim().toLocaleLowerCase('vi-VN').startsWith(SKIPPED_PREFIX)) return 'Đã báo bỏ bữa'
  if (log.match_status === 'unmatched' || log.match_status === 'no_data') return 'Chờ đối chiếu'
  return 'Đã tính vào tổng'
}

function daysOfWeek() {
  const today = new Date()
  return Array.from({ length: 7 }, (_, index) => {
    const date = new Date(today)
    date.setDate(today.getDate() - (6 - index))
    return date.toISOString().slice(0, 10)
  })
}

export default function PatientWeeklyPage() {
  const [days, setDays] = useState<DayData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [expandedIso, setExpandedIso] = useState<string | null>(null)

  useEffect(() => {
    const token = getToken()
    if (!token) return
    const api = createApiClient(token)
    api.getMyProfile().then(async me => {
      const result = await Promise.all(daysOfWeek().map(async iso => ({ iso, logs: await api.listFoodLogs(me.id, iso) })))
      setDays(result)
    }).catch(value => setError(value instanceof ApiError ? value.message : 'Không thể tải tổng hợp tuần.')).finally(() => setLoading(false))
  }, [])

  const todayIso = new Date().toISOString().slice(0, 10)
  const stats = useMemo(() => {
    const activeDays = days.filter(day => day.logs.length > 0).length
    const slots = days.flatMap(day => [...new Set(day.logs.map(log => log.slot).filter(Boolean))])
    const skipped = days.flatMap(day => day.logs).filter(log => log.free_text_vi?.toLowerCase().startsWith('bỏ ')).length
    const unmatched = days.flatMap(day => day.logs).filter(log => log.match_status === 'unmatched').length
    // "Quá hạn": ngày đã qua (không tính hôm nay, chưa xong nên chưa thể coi là bỏ lỡ) mà chưa có ghi nhận nào.
    const overdue = days.filter(day => day.iso < todayIso && day.logs.length === 0).length
    return { activeDays, slots: slots.length, skipped, unmatched, overdue }
  }, [days, todayIso])

  if (loading) return <div className={styles.page}><div className={styles.skeleton}/></div>

  return <div className={styles.page}>
    <header className={styles.header}><div><small>TỔNG HỢP THEO TUẦN</small><h1>Tuần của bạn</h1><p>Hệ thống tổng hợp nhật ký để làm nổi những điểm đáng chú ý; chuyên gia không cần xem từng bữa riêng lẻ.</p></div><Link href="/patient/diary"><Icon name="diary"/>Ghi bữa hôm nay</Link></header>
    {error&&<div className={styles.error}>{error}</div>}
    {stats.overdue>0&&<div className={styles.overdueBanner} role="alert"><Icon name="warning"/><div><strong>{stats.overdue} ngày chưa có ghi nhận nào</strong><p>Những ngày này đã qua nhưng chưa được ghi lại — hãy bổ sung nếu bạn còn nhớ, hoặc để trống nếu thực sự chưa ăn gì được ghi.</p></div></div>}
    <section className={styles.summary}>
      <article><small>TÓM TẮT</small><strong>{stats.activeDays}/7 ngày</strong><p>{stats.activeDays>=5?'Bạn đang ghi nhận khá đều đặn.':'Ghi thêm vài ngày để bản tổng hợp chính xác hơn.'}</p></article>
      <article><small>BỮA ĐÃ GHI</small><strong>{stats.slots}</strong><p>tính theo các khung bữa khác nhau</p></article>
      <article><small>BỎ BỮA</small><strong>{stats.skipped}</strong><p>do bạn chủ động báo cáo</p></article>
      <article><small>CHỜ ĐỐI CHIẾU</small><strong>{stats.unmatched}</strong><p>món chưa đủ dữ liệu để tính</p></article>
    </section>
    <div className={styles.grid}>
      <section className={styles.card}>
        <div className={styles.cardTitle}><div><small>7 NGÀY GẦN NHẤT</small><h2>Mức độ ghi nhận</h2></div><span>{stats.activeDays>=5?'Khá đầy đủ':'Cần thêm dữ liệu'}</span></div>
        <div className={styles.calendar}>{days.map(day=>{
          const slots=new Set(day.logs.map(log=>log.slot))
          const date=new Date(`${day.iso}T00:00:00`)
          const isToday=day.iso===todayIso
          const isOverdue=day.iso<todayIso&&day.logs.length===0
          return <button type="button" className={`${styles.day}${isToday?` ${styles.today}`:''}${isOverdue?` ${styles.dayOverdue}`:''}`} key={day.iso} aria-haspopup="dialog" onClick={()=>setExpandedIso(day.iso)}>
            {isOverdue&&<i className={styles.overdueMark}><Icon name="warning"/></i>}
            <small>{date.toLocaleDateString('vi-VN',{weekday:'short'})}</small><b>{date.getDate()}</b>
            <div className={styles.dots}>{SLOT_ORDER.map(slot=><i key={slot} className={slots.has(slot)?styles.done:undefined}/>)}</div>
            <span>{slots.size}/4 bữa</span>
          </button>
        })}</div>
      </section>
      <aside>
        <section className={styles.card}><div className={styles.cardTitle}><div><small>ĐIỂM CẦN CHÚ Ý</small><h2>Gợi ý cho tuần này</h2></div></div><div className={styles.insights}><Insight icon="diary" title="Duy trì ghi nhận" text={stats.activeDays<5?'Bạn chưa có đủ 5 ngày dữ liệu. Hãy ghi nhận ngắn gọn, không cần nhớ chính xác mọi gram.':'Dữ liệu đã đủ để tạo một bản tóm tắt có ý nghĩa.'}/><Insight icon="warning" title="Dữ liệu chưa đối chiếu" text={stats.unmatched?`${stats.unmatched} món chưa tra được nên chưa được cộng vào tổng dinh dưỡng.`:'Các món đã ghi hiện không có dòng chờ đối chiếu.'}/><Insight icon="clock" title="Nhịp bữa ăn" text={stats.skipped?`Bạn đã báo bỏ ${stats.skipped} bữa. Chuyên gia sẽ xem xu hướng thay vì đánh giá từng lần.`:'Chưa ghi nhận bữa bị bỏ trong tuần này.'}/></div><div className={styles.coach}><span>PHẢN HỒI CHUYÊN GIA</span><h3>Chưa có nhận xét mới</h3><p>Khi báo cáo tuần được chuyên gia xem, nhận xét sẽ xuất hiện ở đây.</p><Link href="/patient">Quay về thực đơn hôm nay<Icon name="arrowRight"/></Link></div></section>
      </aside>
    </div>
    {expandedIso&&<DayDetailModal iso={expandedIso} logs={days.find(day=>day.iso===expandedIso)?.logs??[]} isOverdue={expandedIso<todayIso&&(days.find(day=>day.iso===expandedIso)?.logs.length??0)===0} onClose={()=>setExpandedIso(null)}/>}
  </div>
}

function Insight({icon,title,text}:{icon:string;title:string;text:string}){return <article><span><Icon name={icon}/></span><div><h3>{title}</h3><p>{text}</p></div></article>}

// Theo yêu cầu: thay panel mở-ngay-dưới bằng popup thật (backdrop + hộp thoại nổi giữa màn
// hình), giữ nguyên nội dung 4 bữa/tên món/gram/trạng thái đã có từ trước.
function DayDetailModal({iso,logs,isOverdue,onClose}:{iso:string;logs:FoodLog[];isOverdue:boolean;onClose:()=>void}){
  const date=new Date(`${iso}T00:00:00`)
  const bySlot=new Map<string,FoodLog[]>()
  for(const log of logs){const key=log.slot??'';if(!bySlot.has(key))bySlot.set(key,[]);bySlot.get(key)!.push(log)}
  return <div className={styles.modalLayer} role="presentation">
    <button type="button" className={styles.modalScrim} onClick={onClose} aria-label="Đóng chi tiết ngày"/>
    <div className={styles.dayDetail} id="weekly-day-detail" role="dialog" aria-modal="true" aria-label={`Chi tiết ${date.toLocaleDateString('vi-VN',{weekday:'long',day:'2-digit',month:'2-digit'})}`}>
      <header><div><small>CHI TIẾT NGÀY</small><h3>{date.toLocaleDateString('vi-VN',{weekday:'long',day:'2-digit',month:'2-digit'})}</h3></div><button type="button" onClick={onClose} aria-label="Đóng chi tiết ngày"><Icon name="close"/></button></header>
      {isOverdue&&<div className={styles.dayDetailWarning}><Icon name="warning"/>Ngày này chưa có ghi nhận nào và đã qua — bổ sung nếu bạn còn nhớ đã ăn gì.</div>}
      <div className={styles.dayDetailMeals}>{SLOT_ORDER.map(slot=>{
        const slotLogs=bySlot.get(slot)??[]
        return <article key={slot}>
          <small>{SLOT_LABEL[slot]}</small>
          {slotLogs.length
            ? <ul>{slotLogs.map(log=><li key={log.id}><strong>{log.food_name_vi||log.free_text_vi||'Chưa rõ tên món'}</strong>{log.grams!=null&&<span>{Math.round(log.grams)} g</span>}<small>{logStatusLabel(log)}</small></li>)}</ul>
            : <p className={styles.dayDetailEmpty}>Chưa ghi nhận</p>}
        </article>
      })}</div>
    </div>
  </div>
}
