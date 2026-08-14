'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'
import { Icon } from '@/components/brand-artwork'
import { ApiError, createApiClient, type FoodLog } from '@/lib/api'
import { getToken } from '@/lib/auth'
import styles from '../secondary.module.css'

type DayData = { iso: string; logs: FoodLog[] }
const SLOT_ORDER = ['breakfast','lunch','snack','dinner']

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

  useEffect(() => {
    const token = getToken()
    if (!token) return
    const api = createApiClient(token)
    api.getMyProfile().then(async me => {
      const result = await Promise.all(daysOfWeek().map(async iso => ({ iso, logs: await api.listFoodLogs(me.id, iso) })))
      setDays(result)
    }).catch(value => setError(value instanceof ApiError ? value.message : 'Không thể tải tổng hợp tuần.')).finally(() => setLoading(false))
  }, [])

  const stats = useMemo(() => {
    const activeDays = days.filter(day => day.logs.length > 0).length
    const slots = days.flatMap(day => [...new Set(day.logs.map(log => log.slot).filter(Boolean))])
    const skipped = days.flatMap(day => day.logs).filter(log => log.free_text_vi?.toLowerCase().startsWith('bỏ ')).length
    const unmatched = days.flatMap(day => day.logs).filter(log => log.match_status === 'unmatched').length
    return { activeDays, slots: slots.length, skipped, unmatched }
  }, [days])

  if (loading) return <div className={styles.page}><div className={styles.skeleton}/></div>

  return <div className={styles.page}>
    <header className={styles.header}><div><small>TỔNG HỢP THEO TUẦN</small><h1>Tuần của bạn</h1><p>Hệ thống tổng hợp nhật ký để làm nổi những điểm đáng chú ý; chuyên gia không cần xem từng bữa riêng lẻ.</p></div><Link href="/patient/diary"><Icon name="diary"/>Ghi bữa hôm nay</Link></header>
    {error&&<div className={styles.error}>{error}</div>}
    <section className={styles.summary}>
      <article><small>TÓM TẮT</small><strong>{stats.activeDays}/7 ngày</strong><p>{stats.activeDays>=5?'Bạn đang ghi nhận khá đều đặn.':'Ghi thêm vài ngày để bản tổng hợp chính xác hơn.'}</p></article>
      <article><small>BỮA ĐÃ GHI</small><strong>{stats.slots}</strong><p>tính theo các khung bữa khác nhau</p></article>
      <article><small>BỎ BỮA</small><strong>{stats.skipped}</strong><p>do bạn chủ động báo cáo</p></article>
      <article><small>CHỜ ĐỐI CHIẾU</small><strong>{stats.unmatched}</strong><p>món chưa đủ dữ liệu để tính</p></article>
    </section>
    <div className={styles.grid}>
      <section className={styles.card}><div className={styles.cardTitle}><div><small>7 NGÀY GẦN NHẤT</small><h2>Mức độ ghi nhận</h2></div><span>{stats.activeDays>=5?'Khá đầy đủ':'Cần thêm dữ liệu'}</span></div><div className={styles.days}>{days.map(day=>{const slots=new Set(day.logs.map(log=>log.slot));const date=new Date(`${day.iso}T00:00:00`);return <article className={`${styles.day}${day.iso===new Date().toISOString().slice(0,10)?` ${styles.today}`:''}`} key={day.iso}><small>{date.toLocaleDateString('vi-VN',{weekday:'short'})}</small><b>{date.getDate()}</b><div className={styles.dots}>{SLOT_ORDER.map(slot=><i key={slot} className={slots.has(slot)?styles.done:undefined}/>)}</div><span>{slots.size}/4 bữa</span></article>})}</div></section>
      <aside>
        <section className={styles.card}><div className={styles.cardTitle}><div><small>ĐIỂM CẦN CHÚ Ý</small><h2>Gợi ý cho tuần này</h2></div></div><div className={styles.insights}><Insight icon="diary" title="Duy trì ghi nhận" text={stats.activeDays<5?'Bạn chưa có đủ 5 ngày dữ liệu. Hãy ghi nhận ngắn gọn, không cần nhớ chính xác mọi gram.':'Dữ liệu đã đủ để tạo một bản tóm tắt có ý nghĩa.'}/><Insight icon="warning" title="Dữ liệu chưa đối chiếu" text={stats.unmatched?`${stats.unmatched} món chưa tra được nên chưa được cộng vào tổng dinh dưỡng.`:'Các món đã ghi hiện không có dòng chờ đối chiếu.'}/><Insight icon="clock" title="Nhịp bữa ăn" text={stats.skipped?`Bạn đã báo bỏ ${stats.skipped} bữa. Chuyên gia sẽ xem xu hướng thay vì đánh giá từng lần.`:'Chưa ghi nhận bữa bị bỏ trong tuần này.'}/></div><div className={styles.coach}><span>PHẢN HỒI CHUYÊN GIA</span><h3>Chưa có nhận xét mới</h3><p>Khi báo cáo tuần được chuyên gia xem, nhận xét sẽ xuất hiện ở đây.</p><Link href="/patient">Quay về thực đơn hôm nay<Icon name="arrowRight"/></Link></div></section>
      </aside>
    </div>
  </div>
}

function Insight({icon,title,text}:{icon:string;title:string;text:string}){return <article><span><Icon name={icon}/></span><div><h3>{title}</h3><p>{text}</p></div></article>}
