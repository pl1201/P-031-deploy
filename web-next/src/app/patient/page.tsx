'use client'

import Image from 'next/image'
import { useEffect, useMemo, useState } from 'react'
import { createApiClient, type MealPlan, type MealPlanItem } from '@/lib/api'
import { getToken } from '@/lib/auth'
import styles from './patient.module.css'

const LABELS: Record<string,string> = { breakfast:'Bữa sáng', lunch:'Bữa trưa', dinner:'Bữa tối', snack:'Bữa phụ' }
const PHOTOS: Record<string,string> = { breakfast:'/images/vnutricare-hero-meal.png', lunch:'/images/vnutricare-hero-meal.png', dinner:'/images/vnutricare-hero-meal.png' }

export default function PatientDashboard(){
  const [plans,setPlans]=useState<MealPlan[]>([])
  const [loading,setLoading]=useState(true)
  useEffect(()=>{const token=getToken();if(!token)return;createApiClient(token).listMealPlans(undefined,'approved').then(r=>setPlans(r.items)).finally(()=>setLoading(false))},[])
  const plan=plans[0]
  const groups=useMemo(()=>plan?.items.reduce<Record<string,MealPlanItem[]>>((acc,item)=>{(acc[item.slot]??=[]).push(item);return acc},{})??{},[plan])
  const nutrition=plan?.computed_nutrition
  const slots=['breakfast','lunch','dinner']
  if(loading)return <div className={styles.loading}><span className="spinner"/></div>

  return <div className={styles.page}>
    <header className={styles.heading}><div><h1>Thực đơn của bạn</h1><p>{plan?'Đây là thực đơn đã được chuyên gia phê duyệt.':'Hiện chưa có thực đơn đã phê duyệt.'}</p></div><a href="/patient/diary" className={styles.logButton}>▣ Ghi bữa ăn</a></header>
    <section className={styles.metrics}>
      <article><span>◎</span><div><small>Năng lượng thực đơn</small><strong>{nutrition?Math.round(nutrition.kcal).toLocaleString('vi-VN'):'—'} <i>{nutrition?'kcal':'chưa có dữ liệu'}</i></strong></div></article>
      <article><span>♨</span><div><small>Carbohydrate</small><strong>{nutrition?Math.round(nutrition.carb_g):'—'} <i>{nutrition?'g':'chưa có dữ liệu'}</i></strong></div></article>
      <article><span>♜</span><div><small>Số bữa trong thực đơn</small><strong>{plan?new Set(plan.items.map(item=>item.slot)).size:'—'} <i>{plan?'bữa':'chưa có dữ liệu'}</i></strong></div></article>
      <article><span>✓</span><div><small>Trạng thái</small><b>{plan?'Đã được phê duyệt':'Chờ chuyên gia chuẩn bị'}</b></div></article>
    </section>
    <div className={styles.dashboard}>
      <section className={styles.mealPanel}><div className={styles.sectionTitle}><h2>Thực đơn hôm nay</h2><span>{plan?'Đã phê duyệt':'Chưa có thực đơn'}</span></div>{plan?<div className={styles.mealGrid}>{slots.map((slot,index)=>{const items=groups[slot]??[];if(!items.length)return null;const name=items.map(item=>item.name_vi).join(' • ');const grams=items.reduce((sum,item)=>sum+item.grams,0);return <article className={styles.mealCard} key={slot}><div className={styles.photo}><Image src={PHOTOS[slot]} alt={name} fill sizes="280px" style={{objectPosition:index===0?'22% 22%':index===1?'58% 48%':'78% 70%'}}/></div><small>{LABELS[slot]}</small><h3>{name}</h3><p>{Math.round(grams)} g tổng khẩu phần</p><b>Đã được chuyên gia duyệt</b></article>})}</div>:<div className="empty-state"><div className="empty-title">Chưa có thực đơn được phát hành</div><div className="empty-desc">Bạn chỉ nhìn thấy thực đơn sau khi chuyên gia hoàn tất kiểm tra và phê duyệt.</div></div>}</section>
      <aside className={styles.carb}><h2>Thông tin dinh dưỡng</h2>{nutrition?<ul><li><i/>Năng lượng <b>{Math.round(nutrition.kcal)} kcal</b></li><li><i/>Carbohydrate <b>{Math.round(nutrition.carb_g)} g</b></li><li><i/>Protein <b>{Math.round(nutrition.protein_g)} g</b></li><li><i/>Chất xơ <b>{Math.round(nutrition.fiber_g)} g</b></li></ul>:<p>Chưa có dữ liệu dinh dưỡng.</p>}<p>ⓘ Tổng ngày do backend tính từ dữ liệu thực phẩm có nguồn.</p></aside>
      <section className={styles.diary}><h2>Nhật ký ăn uống</h2><div><span>Dữ liệu nhật ký được quản lý tại trang riêng.</span><a href="/patient/diary">Mở nhật ký →</a></div></section>
      <section className={styles.coach}><span className={styles.coachAvatar}>i</span><div><h2>Lưu ý</h2><p>Thông tin chỉ mang tính hỗ trợ và không thay thế tư vấn trực tiếp của chuyên gia y tế.</p></div></section>
    </div>
  </div>
}
