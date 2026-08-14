'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'
import { Icon } from '@/components/brand-artwork'
import { GuidedTour, type TourStep } from '@/components/guided-tour'
import { ApiError, createApiClient, type FoodLog, type MealPlan, type PatientProfile } from '@/lib/api'
import { getToken } from '@/lib/auth'
import styles from './dashboard.module.css'

const TOUR:TourStep[]=[
  {selector:'[data-tour="action-metrics"]',eyebrow:'Bước 1/5',title:'Bắt đầu từ việc cần xử lý',description:'Mỗi chỉ số mở đúng danh sách đã lọc, không chỉ là số liệu trang trí.'},
  {selector:'[data-tour="priority-queue"]',eyebrow:'Bước 2/5',title:'Ca nghiêm trọng lên trước',description:'Rủi ro, thời gian chờ và khả năng phê duyệt quyết định thứ tự hiển thị.'},
  {selector:'[data-tour="weekly-attention"]',eyebrow:'Bước 3/5',title:'Theo dõi theo ngoại lệ',description:'Những món chưa đối chiếu và bệnh nhân cần chú ý được tổng hợp thay vì báo từng bữa.'},
  {selector:'[data-tour="create-plan"]',eyebrow:'Bước 4/5',title:'Tạo phương án từ đúng hồ sơ',description:'Luồng tạo giữ bệnh nhân đã chọn và tính lại dữ liệu trên backend.'},
  {selector:'[data-tour="release-control"]',eyebrow:'Bước 5/5',title:'Kiểm soát phát hành',description:'Người bệnh không nhìn thấy bản drafting, pending hoặc manual review.'},
]

const riskLabel:Record<string,string>={P0:'Chặn phát hành',P1:'Cần xác nhận',P2:'Thông tin lưu ý',none:'Đã qua kiểm tra'}

export default function DietitianDashboard(){
  const [plans,setPlans]=useState<MealPlan[]>([])
  const [approved,setApproved]=useState<MealPlan[]>([])
  const [unresolved,setUnresolved]=useState<FoodLog[]>([])
  const [patients,setPatients]=useState<Record<string,PatientProfile>>({})
  const [loading,setLoading]=useState(true)
  const [error,setError]=useState('')
  const [referenceTime]=useState(()=>Date.now())

  useEffect(()=>{
    const token=getToken();if(!token)return
    const api=createApiClient(token)
    Promise.all([api.listPendingReviews(),api.listMealPlans(undefined,'approved'),api.listPatients(1,100),api.listUnresolvedLogs()])
      .then(([pending,released,result,logs])=>{setPlans(pending);setApproved(released.items);setPatients(Object.fromEntries(result.items.map(patient=>[patient.id,patient])));setUnresolved(logs)})
      .catch(value=>setError(value instanceof ApiError?value.message:'Không thể tải trung tâm công việc.'))
      .finally(()=>setLoading(false))
  },[])

  const metrics=useMemo(()=>{
    const blocking=plans.filter(plan=>plan.highest_risk==='P0'||plan.status==='manual_review_required').length
    const overdue=plans.filter(plan=>referenceTime-new Date(plan.created_at).getTime()>24*60*60*1000).length
    const quick=plans.filter(plan=>plan.review_packet?.can_approve&&plan.highest_risk!=='P0').length
    const attention=new Set(unresolved.map(log=>log.profile_id)).size
    return {blocking,overdue,quick,attention}
  },[plans,unresolved,referenceTime])

  const releasedToday=approved.filter(plan=>plan.created_at.slice(0,10)===new Date().toISOString().slice(0,10)).length
  const attentionProfiles=useMemo(()=>Object.entries(unresolved.reduce<Record<string,number>>((acc,log)=>{acc[log.profile_id]=(acc[log.profile_id]||0)+1;return acc},{})).sort((a,b)=>b[1]-a[1]).slice(0,4),[unresolved])

  return <div className={styles.page}>
    <header className={styles.heading}><div><span>CLINICAL WORKSPACE</span><h1>Cần xử lý hôm nay</h1><p>Ưu tiên ngoại lệ và quyết định; các ca ổn định tiếp tục theo policy đã định.</p></div><Link href="/dietitian/meal-plans/new" className={styles.create} data-tour="create-plan"><Icon name="sparkles"/>Tạo phương án thực đơn</Link></header>
    {error&&<div className={styles.error}><Icon name="warning"/><span>{error}</span><button type="button" onClick={()=>window.location.reload()}>Tải lại</button></div>}
    <section className={styles.metrics} data-tour="action-metrics">
      <Metric loading={loading} icon="warning" label="Cần xử lý ngay" value={metrics.blocking} tone="danger" href="/dietitian/reviews?priority=blocking" />
      <Metric loading={loading} icon="clock" label="Quá 24 giờ" value={metrics.overdue} tone="warning" href="/dietitian/reviews?age=overdue" />
      <Metric loading={loading} icon="check" label="Có thể duyệt nhanh" value={metrics.quick} tone="success" href="/dietitian/reviews?eligibility=quick" />
      <Metric loading={loading} icon="trend" label="Cần theo dõi tuần" value={metrics.attention} tone="neutral" href="/dietitian/food-logs" />
    </section>

    <div className={styles.grid}>
      <section className={styles.queue} data-tour="priority-queue">
        <div className={styles.sectionTitle}><div><small>HÀNG CHỜ THEO RỦI RO</small><h2>Ca cần quyết định</h2></div><Link href="/dietitian/reviews">Xem toàn bộ <Icon name="arrowRight"/></Link></div>
        {loading?<QueueSkeleton/>:plans.length?plans.slice(0,5).map(plan=><QueueRow key={plan.id} plan={plan} patient={patients[plan.patient_id]} referenceTime={referenceTime}/>):<div className={styles.empty}><Icon name="check"/><h3>Không có ca đang chờ</h3><p>Các bản mới sẽ xuất hiện sau khi hoàn tất bước sinh và kiểm tra.</p></div>}
      </section>

      <aside className={styles.side}>
        <section className={styles.attention} data-tour="weekly-attention"><div className={styles.sectionTitle}><div><small>THEO DÕI THEO NGOẠI LỆ</small><h2>Cần chú ý tuần này</h2></div><span>{metrics.attention}</span></div>{attentionProfiles.length?attentionProfiles.map(([profileId,count])=>{const patient=patients[profileId];return <Link key={profileId} href="/dietitian/food-logs"><span>{patient?.sex==='female'?'Nữ':'N'}</span><div><strong>{patient?`${patient.sex==='male'?'Nam':'Nữ'}, ${patient.age} tuổi`:`Hồ sơ #${profileId.slice(0,8)}`}</strong><small>{count} món chưa được đối chiếu</small></div><Icon name="chevronRight"/></Link>}):<p className={styles.compactEmpty}>Không có nhật ký chưa đối chiếu.</p>}</section>
        <section className={styles.release} data-tour="release-control"><div className={styles.releaseIcon}><Icon name="shield"/></div><div><small>KIỂM SOÁT PHÁT HÀNH</small><h2>Chỉ bản approved được gửi đi</h2><p>{releasedToday} thực đơn được phát hành hôm nay. Bản nháp và bản chờ duyệt không xuất hiện phía người bệnh.</p></div></section>
        <section className={styles.quickLinks}><h2>Đi nhanh tới công việc</h2><Link href="/dietitian/patients"><Icon name="user"/><span><strong>Mở hồ sơ bệnh nhân</strong><small>Xem lâm sàng, thực đơn và lịch sử</small></span><Icon name="chevronRight"/></Link><Link href="/dietitian/food-logs"><Icon name="diary"/><span><strong>Đối chiếu nhật ký</strong><small>{unresolved.length} dòng đang chờ</small></span><Icon name="chevronRight"/></Link></section>
      </aside>
    </div>
    <GuidedTour id="dietitian-dashboard-v2" steps={TOUR}/>
  </div>
}

function Metric({loading,icon,label,value,tone,href}:{loading:boolean;icon:string;label:string;value:number;tone:string;href:string}){return <Link href={href} className={styles.metric} data-tone={tone}><span><Icon name={icon}/></span><div><small>{label}</small><strong>{loading?'':value}</strong>{loading&&<i/>}</div><Icon name="chevronRight"/></Link>}

function QueueRow({plan,patient,referenceTime}:{plan:MealPlan;patient?:PatientProfile;referenceTime:number}){
  const ageMs=referenceTime-new Date(plan.created_at).getTime();const hours=Math.max(0,Math.floor(ageMs/3600000));const finding=plan.safety_findings?.[0]?.message_vi||plan.violations?.[0]?.message_vi||plan.review_packet?.summary||'Đã chuẩn bị đủ dữ liệu kiểm tra.'
  return <article className={styles.row} data-risk={plan.highest_risk}><span className={styles.riskBar}/><div className={styles.patient}><i>{patient?.sex==='female'?'Nữ':'N'}</i><div><strong>{patient?`${patient.sex==='male'?'Nam':'Nữ'}, ${patient.age} tuổi`:`Hồ sơ #${plan.patient_id.slice(0,8)}`}</strong><small>{patient?.conditions.map(item=>item.code).join(' · ')||'Chưa có chẩn đoán được hiển thị'}</small></div></div><div className={styles.finding}><span>{riskLabel[plan.highest_risk]||'Cần xem'}</span><strong>{finding}</strong></div><div className={styles.plan}><small>NGÀY ÁP DỤNG</small><strong>{new Date(`${plan.plan_date}T00:00:00`).toLocaleDateString('vi-VN')}</strong><span>Đã chờ {hours<1?'dưới 1 giờ':`${hours} giờ`}</span></div><Link href={`/dietitian/reviews/${plan.id}`}>Xem và quyết định<Icon name="arrowRight"/></Link></article>
}

function QueueSkeleton(){return <div className={styles.skeleton}><i/><i/><i/></div>}
