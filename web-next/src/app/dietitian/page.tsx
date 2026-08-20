'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'
import { Icon } from '@/components/brand-artwork'
import { PatientAvatar } from '@/components/patient-avatar'
import { GuidedTour, type TourStep } from '@/components/guided-tour'
import { ApiError, createApiClient, type FoodLog, type MealPlan, type PatientProfile } from '@/lib/api'
import { getToken } from '@/lib/auth'

const TOUR:TourStep[]=[
  {selector:'[data-tour="action-metrics"]',eyebrow:'Bước 1/5',title:'Bắt đầu từ việc cần xử lý',description:'Mỗi chỉ số mở đúng danh sách đã lọc, không chỉ là số liệu trang trí.'},
  {selector:'[data-tour="priority-queue"]',eyebrow:'Bước 2/5',title:'Ca nghiêm trọng lên trước',description:'Rủi ro, thời gian chờ và khả năng phê duyệt quyết định thứ tự hiển thị.'},
  {selector:'[data-tour="weekly-attention"]',eyebrow:'Bước 3/5',title:'Theo dõi theo ngoại lệ',description:'Những món chưa đối chiếu và bệnh nhân cần chú ý được tổng hợp thay vì báo từng bữa.'},
  {selector:'[data-tour="create-plan"]',eyebrow:'Bước 4/5',title:'Tạo phương án từ đúng hồ sơ',description:'Luồng tạo giữ bệnh nhân đã chọn và tính lại dữ liệu trên backend.'},
  {selector:'[data-tour="release-control"]',eyebrow:'Bước 5/5',title:'Kiểm soát phát hành',description:'Người bệnh không nhìn thấy bản đang tạo, chờ duyệt hoặc cần rà soát thủ công.'},
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

  return <div data-page="dietitian-dashboard" className="min-h-screen px-[28px] pt-[20px] pb-10 text-[var(--c-ink)] max-[780px]:px-[15px] max-[780px]:pt-[58px] max-[780px]:pb-[30px]">
    <header className="mb-3.5 flex items-start justify-between gap-5 max-[780px]:grid">
      <div>
        <span className="text-[9px] font-extrabold tracking-[.13em] text-[var(--c-green)]">TRUNG TÂM CÔNG VIỆC</span>
        <h1 className="mt-1 font-[family-name:var(--f-serif)] text-[20px] font-semibold tracking-[-.01em] max-[780px]:text-[18px]">Tổng quan hôm nay</h1>
        <p className="mt-1 text-[10px] text-[var(--c-muted)]">Các ca cần quyết định được đưa lên trước; ca ổn định không tạo thêm thao tác.</p>
      </div>
      <Link href="/dietitian/meal-plans/new" className="flex min-h-[38px] items-center gap-2 rounded-[10px] bg-[linear-gradient(100deg,var(--c-green),var(--c-green3))] px-3.5 text-[10px] font-bold text-white shadow-[0_10px_25px_rgba(0,114,188,.18)] max-[780px]:w-fit" data-tour="create-plan"><Icon name="sparkles" className="w-4"/>Tạo thực đơn</Link>
    </header>
    {error&&<div className="mb-2.5 flex items-center gap-[9px] rounded-xl border border-[#efb4a4] bg-[#fff5f1] p-2.5 text-[9px] text-[#8b3d2b]"><Icon name="warning" className="w-4"/><span className="flex-1">{error}</span><button type="button" className="rounded-lg border border-[#e5aa99] px-2 py-1.5 font-bold" onClick={()=>window.location.reload()}>Tải lại</button></div>}
    <section className="mb-3.5 grid grid-cols-4 gap-2.5 max-[780px]:grid-cols-2 max-[480px]:grid-cols-1" data-tour="action-metrics">
      <Metric loading={loading} icon="warning" label="Cần xử lý ngay" value={metrics.blocking} tone="danger" href="/dietitian/reviews?priority=blocking" />
      <Metric loading={loading} icon="clock" label="Quá 24 giờ" value={metrics.overdue} tone="warning" href="/dietitian/reviews?age=overdue" />
      <Metric loading={loading} icon="check" label="Có thể duyệt nhanh" value={metrics.quick} tone="success" href="/dietitian/reviews?eligibility=quick" />
      <Metric loading={loading} icon="trend" label="Cần theo dõi tuần" value={metrics.attention} tone="neutral" href="/dietitian/food-logs" />
    </section>

    <div className="grid grid-cols-[minmax(0,1.45fr)_minmax(310px,.55fr)] gap-2.5 max-[1150px]:grid-cols-1">
      <section className="overflow-hidden rounded-xl border border-[var(--c-border)] bg-[var(--c-card)] shadow-[var(--shadow-sm)]" data-tour="priority-queue">
        <div className="flex min-h-[52px] items-center justify-between gap-2.5 border-b border-[var(--c-border)] px-3.5 py-2.5"><div><small className="text-[9px] font-extrabold tracking-[.13em] text-[var(--c-green)]">HÀNG CHỜ THEO RỦI RO</small><h2 className="mt-[3px] font-[family-name:var(--f-serif)] text-[13.5px] font-semibold">Ca cần quyết định</h2></div><Link className="flex items-center gap-[5px] text-[9px] font-bold text-[var(--c-green2)]" href="/dietitian/reviews">Xem toàn bộ <Icon name="arrowRight" className="w-[15px]"/></Link></div>
        {loading?<QueueSkeleton/>:plans.length?plans.slice(0,5).map(plan=><QueueRow key={plan.id} plan={plan} patient={patients[plan.patient_id]} referenceTime={referenceTime}/>):<div className="grid min-h-[240px] content-center place-items-center p-9 text-center"><Icon name="check" className="w-9 rounded-xl bg-[var(--c-lime)] p-2 text-[var(--c-green2)]"/><h3 className="mt-2.5 font-[family-name:var(--f-serif)] text-[15px]">Không có ca đang chờ</h3><p className="mt-1.5 text-[9px] text-[#6a7c7c]">Các bản mới sẽ xuất hiện sau khi hoàn tất bước sinh và kiểm tra.</p></div>}
      </section>

      <aside className="grid content-start gap-2.5 max-[1150px]:grid-cols-2 max-[780px]:grid-cols-1">
        <section className="overflow-hidden rounded-xl border border-[var(--c-border)] bg-[var(--c-card)] shadow-[var(--shadow-sm)]" data-tour="weekly-attention">
          <div className="flex min-h-[52px] items-center justify-between gap-2.5 border-b border-[var(--c-border)] px-3.5 py-2.5"><div><small className="text-[9px] font-extrabold tracking-[.13em] text-[var(--c-green)]">THEO DÕI THEO NGOẠI LỆ</small><h2 className="mt-[3px] font-[family-name:var(--f-serif)] text-[13.5px] font-semibold">Cần chú ý tuần này</h2></div><span className="grid h-[24px] min-w-[24px] place-items-center rounded-full bg-[var(--c-lime)] text-[9px] font-extrabold text-[var(--c-green2)]">{metrics.attention}</span></div>
          {attentionProfiles.length?attentionProfiles.map(([profileId,count])=>{const patient=patients[profileId];return <Link key={profileId} className="grid min-h-[52px] grid-cols-[32px_1fr_16px] items-center gap-[9px] border-b border-[var(--c-border)] px-3.5 py-2 last:border-0" href={`/dietitian/food-logs?profile_id=${profileId}`}>{patient?<PatientAvatar sex={patient.sex} size="sm"/>:<Icon name="user" className="grid h-[30px] w-[30px] place-items-center rounded-[10px] bg-[var(--c-lime)] text-[var(--c-green2)]"/>}<div><strong className="text-[9px]">{patient?`${patient.sex==='male'?'Nam':'Nữ'}, ${patient.age} tuổi`:`Mã hồ sơ ${profileId.slice(0,8).toUpperCase()}`}</strong><small className="mt-[3px] block text-[8px] text-[var(--c-muted)]">{count} món chưa được đối chiếu</small></div><Icon name="chevronRight" className="w-[15px] text-[var(--c-muted)]"/></Link>}):<p className="px-3.5 py-5 text-center text-[9px] text-[var(--c-muted)]">Không có nhật ký chưa đối chiếu.</p>}
        </section>
        <section className="grid grid-cols-[34px_1fr] gap-2.5 rounded-xl border border-[var(--c-border)] bg-[var(--c-card)] p-3 shadow-[var(--shadow-sm)]" data-tour="release-control">
          <div className="grid h-[34px] w-[34px] place-items-center rounded-[10px] bg-[var(--c-lime)] text-[var(--c-green2)]"><Icon name="shield" className="w-[18px]"/></div>
          <div><small className="text-[9px] font-extrabold tracking-[.13em] text-[var(--c-green)]">KIỂM SOÁT PHÁT HÀNH</small><h2 className="mt-0.5 font-[family-name:var(--f-serif)] text-[13px]">Chỉ bản đã duyệt được gửi đi</h2><p className="mt-1 text-[8px] leading-[1.5] text-[#637676]">{releasedToday} thực đơn được phát hành hôm nay. Bản nháp và bản chờ duyệt không xuất hiện phía người bệnh.</p></div>
        </section>
        <section className="rounded-xl border border-[var(--c-border)] bg-[var(--c-card)] p-2.5 shadow-[var(--shadow-sm)] max-[1150px]:col-span-full max-[780px]:col-auto">
          <h2 className="font-[family-name:var(--f-serif)] text-[13px]">Đi nhanh tới công việc</h2>
          <Link className="mt-2 grid min-h-[46px] grid-cols-[26px_1fr_15px] items-center gap-2 rounded-[10px] border border-[var(--c-border)] bg-[var(--c-surface)] p-2" href="/dietitian/patients"><Icon name="user" className="w-[18px] text-[var(--c-green2)]"/><span className="grid"><strong className="text-[9px]">Mở hồ sơ bệnh nhân</strong><small className="mt-[3px] text-[8px] text-[var(--c-muted)]">Xem lâm sàng, thực đơn và lịch sử</small></span><Icon name="chevronRight" className="w-3.5"/></Link>
          <Link className="mt-2 grid min-h-[46px] grid-cols-[26px_1fr_15px] items-center gap-2 rounded-[10px] border border-[var(--c-border)] bg-[var(--c-surface)] p-2" href="/dietitian/food-logs"><Icon name="diary" className="w-[18px] text-[var(--c-green2)]"/><span className="grid"><strong className="text-[9px]">Đối chiếu nhật ký</strong><small className="mt-[3px] text-[8px] text-[var(--c-muted)]">{unresolved.length} dòng đang chờ</small></span><Icon name="chevronRight" className="w-3.5"/></Link>
        </section>
      </aside>
    </div>
    <GuidedTour id="dietitian-dashboard-v2" steps={TOUR}/>
  </div>
}

const METRIC_TONE:Record<string,string>={danger:'text-[#b44d3e] bg-[#fff0ec]',warning:'text-[#a76e12] bg-[#fff5db]',success:'text-[var(--c-green2)] bg-[var(--c-lime)]',neutral:'text-[var(--c-green2)] bg-[var(--c-lime)]'}
function Metric({loading,icon,label,value,tone,href}:{loading:boolean;icon:string;label:string;value:number;tone:string;href:string}){
  return <Link href={href} className="grid min-h-[64px] grid-cols-[28px_1fr_16px] items-center gap-2.5 rounded-xl border border-[var(--c-border)] bg-[var(--c-card)] px-3 py-2.5 shadow-[var(--shadow-sm)] transition-[transform,border-color] duration-[180ms] hover:-translate-y-0.5 hover:border-[var(--c-green3)]">
    <span className={`grid h-7 w-7 place-items-center rounded-lg ${METRIC_TONE[tone]}`}><Icon name={icon} className="w-3.5"/></span>
    <div><small className="text-[8px]">{label}</small><strong className="mt-0.5 block font-[family-name:var(--f-serif)] text-[20px] font-semibold">{loading?'':value}</strong>{loading&&<i className="mt-1 block h-5 w-[28px] animate-[skeleton-pulse_1.3s_infinite] rounded-lg bg-[linear-gradient(90deg,#e7efed,#f6f9f8,#e7efed)] bg-[length:200%_100%]"/>}</div>
    <Icon name="chevronRight" className="w-3.5 text-[var(--c-muted)]"/>
  </Link>
}

const RISK_BAR:Record<string,string>={P0:'bg-[#c65243]',P1:'bg-[#d99b26]',P2:'bg-[#6aa7a2]'}
function QueueRow({plan,patient,referenceTime}:{plan:MealPlan;patient?:PatientProfile;referenceTime:number}){
  const ageMs=referenceTime-new Date(plan.created_at).getTime();const hours=Math.max(0,Math.floor(ageMs/3600000));const finding=plan.safety_findings?.[0]?.message_vi||plan.violations?.[0]?.message_vi||plan.review_packet?.summary||'Đã chuẩn bị đủ dữ liệu kiểm tra.'
  const isP0=plan.highest_risk==='P0'
  return <article className="relative grid min-h-[76px] grid-cols-[minmax(150px,.85fr)_minmax(210px,1.15fr)_minmax(105px,.5fr)_auto] items-center gap-2.5 border-b border-[var(--c-border)] bg-transparent py-2.5 pr-3 pl-4 last:border-0 max-[1150px]:grid-cols-[minmax(150px,.8fr)_minmax(210px,1.2fr)_auto] max-[780px]:grid-cols-[1fr_auto] max-[480px]:pr-[10px]">
    <span className={`absolute inset-y-3 left-0 w-1 rounded-r ${RISK_BAR[plan.highest_risk]||'bg-[var(--c-green)]'}`}/>
    <div className="grid min-w-0 grid-cols-[39px_1fr] items-center gap-[9px]">{patient?<PatientAvatar sex={patient.sex} size="sm"/>:<Icon name="user"/>}<div className="grid min-w-0"><strong className="overflow-hidden text-ellipsis whitespace-nowrap text-[10px]">{patient?`${patient.sex==='male'?'Nam':'Nữ'}, ${patient.age} tuổi`:`Mã hồ sơ ${plan.patient_id.slice(0,8).toUpperCase()}`}</strong><small className="mt-[3px] text-[8px] text-[#6d7e7e]">{patient?.conditions.map(item=>item.code).join(' · ')||'Chưa có chẩn đoán được hiển thị'}</small></div></div>
    <div className="grid min-w-0 max-[780px]:col-span-full max-[780px]:row-start-2"><span className={`w-fit rounded-full px-[7px] py-[5px] text-[7px] font-extrabold ${isP0?'text-[#9e4437] bg-[#ffebe6]':'text-[#8e6217] bg-[#fff4d9]'}`}>{riskLabel[plan.highest_risk]||'Cần xem'}</span><strong className="mt-1.5 line-clamp-2 overflow-hidden text-[9px] leading-[1.4]">{finding}</strong></div>
    <div className="grid min-w-0 max-[1150px]:hidden"><small className="text-[8px] text-[#6d7e7e]">NGÀY ÁP DỤNG</small><strong className="mt-1 font-[family-name:var(--f-mono)] text-[9px]">{new Date(`${plan.plan_date}T00:00:00`).toLocaleDateString('vi-VN')}</strong><span className="mt-[3px] text-[8px] text-[#6d7e7e]">Đã chờ {hours<1?'dưới 1 giờ':`${hours} giờ`}</span></div>
    <Link className="flex min-h-9 items-center gap-[5px] whitespace-nowrap rounded-lg border border-[var(--c-border2)] bg-[var(--c-surface)] px-[11px] text-[8px] font-bold max-[780px]:col-start-2 max-[780px]:row-start-1 max-[480px]:text-[0px]" href={`/dietitian/reviews/${plan.id}`}>Xem và quyết định<Icon name="arrowRight" className="w-3.5 max-[480px]:w-[17px]"/></Link>
  </article>
}

function QueueSkeleton(){return <div className="grid gap-2.5 px-[15px] py-[13px]">{[0,1,2].map(i=><i key={i} className="h-[82px] animate-[skeleton-pulse_1.3s_infinite] rounded-xl bg-[linear-gradient(90deg,#e7efed_25%,#f6f9f8_50%,#e7efed_75%)] bg-[length:200%_100%]"/>)}</div>}
