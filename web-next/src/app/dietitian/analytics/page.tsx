'use client'

import Link from 'next/link'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Icon } from '@/components/brand-artwork'
import { ApiError, createApiClient, type FoodLog, type MealPlan, type PatientProfile } from '@/lib/api'
import { getToken } from '@/lib/auth'
import { DecisionFlow, ReadinessDonut, RiskDonut } from './charts'
import styles from './analytics.module.css'

type Range='7'|'30'|'all'
type Insight={tone:'urgent'|'watch'|'good';title:string;text:string;href:string;action:string}

const DAY=86400000
const statusLabel:Record<string,string>={pending_review:'Chờ duyệt',manual_review_required:'Cần xem tay',approved:'Đã phát hành',rejected:'Từ chối',failed:'Lỗi tạo'}

export default function AnalyticsPage(){
  const [range,setRange]=useState<Range>('30')
  const [plans,setPlans]=useState<MealPlan[]>([])
  const [patients,setPatients]=useState<PatientProfile[]>([])
  const [logs,setLogs]=useState<FoodLog[]>([])
  const [loading,setLoading]=useState(true)
  const [refreshing,setRefreshing]=useState(false)
  const [error,setError]=useState('')
  const [lastUpdated,setLastUpdated]=useState<Date|null>(null)
  const [now,setNow]=useState(()=>Date.now())
  const loadingRef=useRef(false)

  const refresh=useCallback(async(silent=false)=>{if(loadingRef.current)return;const token=getToken();if(!token)return;loadingRef.current=true;if(silent)setRefreshing(true);else setLoading(true);const api=createApiClient(token);const loadStatus=async(status:string)=>{const first=await api.listMealPlans(undefined,status,1);const pages=Math.ceil(first.total/first.page_size);if(pages<=1)return first.items;const rest=await Promise.all(Array.from({length:pages-1},(_,index)=>api.listMealPlans(undefined,status,index+2)));return[first.items,...rest.map(page=>page.items)].flat()};try{const[pending,approved,rejected,failed,profiles,unresolved]=await Promise.all([
    api.listPendingReviews(),loadStatus('approved'),loadStatus('rejected'),loadStatus('failed'),api.listPatients(1,100),api.listUnresolvedLogs()
  ]);setPlans([...pending,...approved,...rejected,...failed]);setPatients(profiles.items);setLogs(unresolved);setNow(Date.now());setLastUpdated(new Date());setError('')}catch(value){setError(value instanceof ApiError?value.message:'Không thể tải dữ liệu thống kê.')}finally{loadingRef.current=false;setLoading(false);setRefreshing(false)}},[])

  useEffect(()=>{const initial=window.setTimeout(()=>void refresh(),0);const interval=window.setInterval(()=>{if(document.visibilityState==='visible')void refresh(true)},15000);const visible=()=>{if(document.visibilityState==='visible')void refresh(true)};document.addEventListener('visibilitychange',visible);return()=>{window.clearTimeout(initial);window.clearInterval(interval);document.removeEventListener('visibilitychange',visible)}},[refresh])

  const filtered=useMemo(()=>{if(range==='all')return plans;const cutoff=now-Number(range)*DAY;return plans.filter(plan=>new Date(plan.created_at).getTime()>=cutoff)},[plans,range,now])
  const model=useMemo(()=>buildModel(filtered,patients,logs,now),[filtered,patients,logs,now])

  return <div className={styles.page}>
    <header className={styles.header}><div><small>HIỆU SUẤT LÂM SÀNG</small><h1>Thống kê chuyên môn</h1><p>Từ khối lượng công việc đến chất lượng phát hành: số liệu được nối thành nhận định có thể hành động.</p><div className={styles.liveStatus}><i/><strong>LIVE</strong><span>{lastUpdated?`Cập nhật ${lastUpdated.toLocaleTimeString('vi-VN',{hour:'2-digit',minute:'2-digit',second:'2-digit'})}`:'Đang kết nối dữ liệu'} · tự làm mới mỗi 15 giây</span><button type="button" disabled={refreshing||loading} onClick={()=>void refresh(true)}><Icon name="refresh"/>{refreshing?'Đang đồng bộ':'Làm mới'}</button></div></div><div className={styles.range} aria-label="Khoảng thời gian">{([['7','7 ngày'],['30','30 ngày'],['all','Toàn bộ']] as const).map(([value,label])=><button type="button" className={range===value?styles.active:undefined} onClick={()=>setRange(value)} key={value}>{label}</button>)}</div></header>
    {error&&<div className={styles.error}><Icon name="warning"/>{error}<button type="button" onClick={()=>window.location.reload()}>Tải lại</button></div>}

    <section className={styles.story}><div><span>01 · BỨC TRANH ĐIỀU HÀNH</span><h2>{loading?'Đang tổng hợp dữ liệu…':model.headline}</h2><p>{model.subline}</p></div><Icon name="trend"/></section>

    <section className={styles.kpis} aria-label="Chỉ số chính">
      <Kpi icon="clipboard" label="Phương án trong kỳ" value={loading?'—':String(model.total)} note={`${model.patientCoverage} hồ sơ có phương án`} tone="neutral"/>
      <Kpi icon="check" label="Tỷ lệ phát hành" value={loading?'—':`${model.releaseRate}%`} note={`${model.approved} bản đã duyệt`} tone="good"/>
      <Kpi icon="warning" label="Cần can thiệp" value={loading?'—':String(model.blocked)} note={`${model.overdue} bản chờ quá 24 giờ`} tone="danger"/>
      <Kpi icon="clock" label="Thời gian chờ giữa vị" value={loading?'—':`${model.medianWait}h`} note="tính trên hàng chờ hiện tại" tone="warning"/>
      <Kpi icon="database" label="Dòng chưa đối chiếu" value={loading?'—':String(logs.length)} note={`${model.attentionPatients} người bệnh liên quan`} tone="info"/>
    </section>

    <div className={styles.dashboard}>
      <main>
        <section className={styles.panel}><PanelTitle step="02" eyebrow="DÒNG CHẢY QUYẾT ĐỊNH" title="Các trạng thái cần chú ý" note="4 trạng thái chưa xong việc — 'Đã phát hành' đã có riêng ở Tỷ lệ phát hành phía trên."/><div className="mt-4"><DecisionFlow metrics={model.flowMetrics}/></div></section>

        <section className={styles.twoPanels}>
          <section className={styles.panel}><PanelTitle step="03" eyebrow="AN TOÀN LÂM SÀNG" title="Cơ cấu mức rủi ro" note="Ưu tiên P0 trước, sau đó P1 cần xác nhận."/><div className="pt-4"><RiskDonut slices={model.risks} total={model.riskTotal}/></div></section>
          {/* Trước đây mục này chủ yếu là chữ (số 99% cỡ lớn + 1 thanh mỏng) — đổi sang
              dạng donut giống mục 03 để nhất quán ngôn ngữ hình ảnh giữa các biểu đồ, thay vì
              lẫn giữa "biểu đồ" và "khối text có số". */}
          <section className={styles.panel}><PanelTitle step="04" eyebrow="CHẤT LƯỢNG DỮ LIỆU" title="Khả năng đưa ra kết luận" note="Dữ liệu thiếu được tách khỏi kết quả đạt."/><div className="pt-4"><ReadinessDonut ready={Math.max(0,patients.length-model.attentionPatients)} pending={model.attentionPatients} percent={model.dataReady}/></div></section>
        </section>

        <section className={styles.panel}><PanelTitle step="05" eyebrow="NHỊP HOẠT ĐỘNG" title="Phương án được tạo theo ngày" note="Dùng để nhận biết dồn tải và khoảng trống vận hành."/><div className={styles.timeline}>{model.timeline.map(item=><div key={item.day}><span>{item.count}</span><i style={{height:`${Math.max(8,item.height)}%`}}/><small>{item.label}</small></div>)}</div></section>

        <section className={styles.panel}><PanelTitle step="06" eyebrow="CƠ CẤU CA" title="Bệnh lý được ghi nhận nhiều nhất" note="Một hồ sơ có thể thuộc nhiều nhóm."/><div className={styles.conditions}>{model.conditions.length?model.conditions.map(item=><article key={item.name}><div><strong>{item.name}</strong><span>{item.count} hồ sơ</span></div><i><b style={{width:`${item.percent}%`}}/></i></article>):<p className={styles.noData}>Chưa có đủ dữ liệu bệnh lý để phân nhóm.</p>}</div></section>
      </main>

      <aside className={styles.insightRail}><div className={styles.railHeader}><small>NHẬN ĐỊNH TỰ ĐỘNG</small><h2>Điều chuyên gia cần thấy</h2><p>Nhận định mô tả dữ liệu hiện có, không thay thế đánh giá lâm sàng.</p></div>{model.insights.map((item,index)=><article data-tone={item.tone} key={item.title}><span>{String(index+1).padStart(2,'0')}</span><div><strong>{item.title}</strong><p>{item.text}</p><Link href={item.href}>{item.action}<Icon name="arrowRight"/></Link></div></article>)}<div className={styles.method}><Icon name="shield"/><div><strong>Cách đọc dashboard</strong><p>So sánh xu hướng, kiểm tra ngoại lệ, rồi mở hồ sơ gốc trước khi quyết định.</p></div></div></aside>
    </div>
  </div>
}

function Kpi({icon,label,value,note,tone}:{icon:string;label:string;value:string;note:string;tone:string}){return <article className={styles.kpi} data-tone={tone}><span><Icon name={icon}/></span><div><small>{label}</small><strong>{value}</strong><p>{note}</p></div></article>}
function PanelTitle({step,eyebrow,title,note}:{step:string;eyebrow:string;title:string;note:string}){return <header className={styles.panelTitle}><span>{step}</span><div><small>{eyebrow}</small><h2>{title}</h2><p>{note}</p></div></header>}

function buildModel(plans:MealPlan[],patients:PatientProfile[],logs:FoodLog[],now:number){
  const total=plans.length,approved=plans.filter(p=>p.status==='approved').length,blocked=plans.filter(p=>p.highest_risk==='P0'||p.status==='manual_review_required').length
  const pending=plans.filter(p=>p.status==='pending_review'||p.status==='manual_review_required'),overdue=pending.filter(p=>now-new Date(p.created_at).getTime()>DAY).length
  const waits=pending.map(p=>Math.max(0,Math.round((now-new Date(p.created_at).getTime())/3600000))).sort((a,b)=>a-b);const medianWait=waits.length?waits[Math.floor(waits.length/2)]:0
  const releaseRate=total?Math.round(approved/total*100):0,patientCoverage=new Set(plans.map(p=>p.patient_id)).size,attentionPatients=new Set(logs.map(l=>l.profile_id)).size
  const statusKeys=['pending_review','manual_review_required','approved','rejected','failed'];const statuses=statusKeys.map(key=>{const count=plans.filter(p=>p.status===key).length;return{key,label:statusLabel[key],count,percent:total?Math.round(count/total*100):0}})
  // Block 02 "Dòng chảy quyết định" chỉ nêu 4 trạng thái CẦN CHÚ Ý (chờ/cần xem
  // tay/từ chối/lỗi) — bỏ "Đã phát hành" vì đó là kết quả tốt, đã có "Tỷ lệ phát
  // hành" riêng ở dải KPI phía trên, không cần lặp lại ở đây.
  const FLOW_COLORS:Record<string,string>={pending_review:'#38BDF8',manual_review_required:'#FBBF24',rejected:'#F87171',failed:'#94A3B8'}
  const flowMetrics=statuses.filter(item=>item.key!=='approved').map(item=>({...item,color:FLOW_COLORS[item.key]}))
  // Nhãn P0/P1/P2 là mã nội bộ (risk_level trong API) — đổi sang tên nghiệp vụ tiếng Việt
  // cho người xem dashboard, khớp với cách RISK_LABEL đã dùng ở dietitian/page.tsx và
  // reviews/[id]/page.tsx để không tạo thêm 1 bộ tên khác trong cùng hệ thống.
  const riskDefs=[['P0','Chặn phát hành','#F87171'],['P1','Cần xác nhận','#FBBF24'],['P2','Lưu ý','#38BDF8'],['none','Đã qua kiểm tra','#34D399']] as const;const risks=riskDefs.map(([key,label,color])=>({key,label,color,value:plans.filter(p=>p.highest_risk===key).length}));const riskTotal=risks.reduce((s,r)=>s+r.value,0)
  const dataReady=patients.length?Math.max(0,Math.round((patients.length-attentionPatients)/patients.length*100)):100
  const days=14;const timeline=Array.from({length:days},(_,index)=>{const date=new Date(now-(days-1-index)*DAY);const iso=date.toISOString().slice(0,10);const count=plans.filter(p=>p.created_at.slice(0,10)===iso).length;return{day:iso,label:index%2===0?`${date.getDate()}/${date.getMonth()+1}`:'',count,height:0}});const maxDay=Math.max(1,...timeline.map(d=>d.count));timeline.forEach(d=>d.height=Math.round(d.count/maxDay*100))
  const conditionCounts=new Map<string,number>();patients.forEach(p=>p.conditions.forEach(c=>conditionCounts.set(c.code,(conditionCounts.get(c.code)||0)+1)));const conditionMax=Math.max(1,...conditionCounts.values());const conditions=[...conditionCounts].sort((a,b)=>b[1]-a[1]).slice(0,6).map(([name,count])=>({name,count,percent:Math.round(count/conditionMax*100)}))
  const insights:Insight[]=[]
  if(blocked)insights.push({tone:'urgent',title:`${blocked} phương án cần can thiệp`,text:'Có cảnh báo mức chặn phát hành hoặc trạng thái cần xem tay. Đây là nhóm cần được mở trước khi xử lý hàng chờ thông thường.',href:'/dietitian/reviews?priority=blocking',action:'Mở ca bị chặn'})
  if(overdue)insights.push({tone:'watch',title:`${overdue} bản đã chờ quá 24 giờ`,text:'Thời gian chờ kéo dài có thể làm chậm ngày áp dụng. Kiểm tra khả năng duyệt hoặc lý do đang bị chặn.',href:'/dietitian/reviews?age=overdue',action:'Xem hàng chờ lâu'})
  if(logs.length)insights.push({tone:'watch',title:'Dữ liệu thực tế còn khoảng trống',text:`${logs.length} dòng của ${attentionPatients} người bệnh chưa được đối chiếu; tổng hợp dinh dưỡng hiện chỉ mang tính tối thiểu.`,href:'/dietitian/food-logs',action:'Đối chiếu dữ liệu'})
  if(releaseRate>=70)insights.push({tone:'good',title:'Luồng phát hành đang ổn định',text:`${releaseRate}% phương án trong tập dữ liệu đã được duyệt. Tiếp tục theo dõi rủi ro và chất lượng nhật ký thay vì chỉ tăng số lượng.`,href:'/dietitian/reviews',action:'Xem lịch sử quyết định'})
  if(!insights.length)insights.push({tone:'good',title:'Chưa có ngoại lệ nổi bật',text:'Không có tín hiệu cần ưu tiên trong dữ liệu hiện tại. Duy trì kiểm tra theo quy trình và theo dõi biến động ở kỳ tiếp theo.',href:'/dietitian',action:'Về tổng quan hôm nay'})
  const headline=blocked?`${blocked} ca đang quyết định nhịp vận hành.`:logs.length?'Luồng duyệt ổn định, chất lượng nhật ký là điểm cần tập trung.':'Không có nút thắt nổi bật trong dữ liệu hiện tại.'
  const subline=total?`${total} phương án được phân tích, ${approved} bản đã phát hành và ${attentionPatients} hồ sơ còn dữ liệu thực tế cần chú ý.`:'Chưa có đủ phương án trong khoảng thời gian này; hãy mở rộng bộ lọc để xem bức tranh dài hơn.'
  return{total,approved,blocked,overdue,medianWait,releaseRate,patientCoverage,attentionPatients,statuses,flowMetrics,risks,riskTotal,dataReady,timeline,conditions,insights:insights.slice(0,4),headline,subline}
}
