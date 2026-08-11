'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'
import { createApiClient, type MealPlan, type PatientProfile } from '@/lib/api'
import { getToken } from '@/lib/auth'
import styles from './dashboard.module.css'

export default function DietitianDashboard(){
  const [plans,setPlans]=useState<MealPlan[]>([])
  const [patients,setPatients]=useState<Record<string,PatientProfile>>({})
  const [loading,setLoading]=useState(true)
  useEffect(()=>{const token=getToken();if(!token)return;const api=createApiClient(token);Promise.all([api.listPendingReviews(),api.listPatients(1,100)]).then(([pending,result])=>{setPlans(pending);setPatients(Object.fromEntries(result.items.map(p=>[p.id,p]))) }).finally(()=>setLoading(false))},[])
  const alertCount=useMemo(()=>plans.reduce((sum,p)=>sum+p.violations.length,0),[plans])
  return <div className={styles.page}>
    <header className={styles.heading}><div><h1>Tổng quan chuyên gia</h1><p>Theo dõi hồ sơ và phê duyệt thực đơn an toàn.</p></div><Link href="/dietitian/meal-plans/new" className={styles.create}>⊞ Tạo thực đơn nháp</Link></header>
    <section className={styles.metrics}>{[['▤','Chờ duyệt',loading?'—':plans.length,'thực đơn'],['△','Cảnh báo cần xử lý',loading?'—':alertCount,''],['✓','Đã duyệt hôm nay','—','chưa có API tổng hợp'],['◷','Thời gian duyệt TB','—','chưa có API tổng hợp']].map(([icon,label,value,unit])=><article key={label}><span>{icon}</span><div><small>{label}</small><strong>{value} <i>{unit}</i></strong></div></article>)}</section>
    <div className={styles.grid}>
      <section className={styles.queue}><div className={styles.sectionTitle}><h2>Hàng chờ phê duyệt</h2><Link href="/dietitian/reviews">Xem tất cả →</Link></div><div className={styles.tableHead}><span>Bệnh nhân</span><span>Hồ sơ</span><span>Thực đơn</span><span>Cảnh báo</span><span>Cập nhật</span><span>Thao tác</span></div>{plans.slice(0,3).map((plan,index)=>{const patient=patients[plan.patient_id];const warning=plan.violations[0];return <div className={styles.row} key={plan.id}><span className={styles.patient}><i>{patient?.sex==='female'?'N':'B'}</i><b>{patient?`${patient.sex==='male'?'Nam':'Nữ'}, ${patient.age} tuổi`:`Hồ sơ #${plan.patient_id.slice(0,8)}`}</b></span><span>{patient?.conditions.map(c=>c.code).join(' • ')||'Chưa có thông tin bệnh nền'}</span><span>Thực đơn {plan.plan_date.slice(5).split('-').reverse().join('/')}</span><span className={warning?styles.warn:styles.safe}>{warning?'△ '+warning.message_vi:plan.review_packet?.can_approve?'✓ Đã kiểm tra':'○ Chờ kiểm tra'}</span><span>{new Date(plan.created_at).toLocaleString('vi-VN')}</span><Link href={`/dietitian/reviews/${plan.id}`}>Xem xét</Link></div>})}{!loading&&!plans.length&&<div className="empty-state"><div className="empty-title">Không có thực đơn chờ duyệt</div><div className="empty-desc">Các bản nháp đã qua bước sinh và kiểm tra sẽ xuất hiện tại đây.</div></div>}</section>
      <aside className={styles.alerts}><h2>Cảnh báo lâm sàng</h2>{plans.flatMap(plan=>plan.violations.map(violation=>({plan,violation}))).slice(0,3).map(({plan,violation})=><article key={`${plan.id}-${violation.nutrient}-${violation.kind}`}><span>△</span><div><b>{violation.message_vi}</b><small>Thực đơn #{plan.id.slice(0,8)}</small></div><Link href={`/dietitian/reviews/${plan.id}`}>Kiểm tra ngay →</Link></article>)}{!loading&&alertCount===0&&<div className="empty-state"><div className="empty-title">Không có cảnh báo đang chờ</div></div>}</aside>
      <section className={styles.activity}><h2>Hoạt động gần đây</h2><p><span>Chưa có API tổng hợp hoạt động theo chuyên gia.</span><b>—</b></p></section>
      <section className={styles.release}><h2>Kiểm soát phát hành</h2><div><span>◇</span><p>Không có thực đơn chưa duyệt nào được gửi đến người bệnh.<b>Hoạt động bình thường</b></p></div></section>
    </div>
  </div>
}
