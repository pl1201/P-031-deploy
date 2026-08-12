'use client'

import { useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import { ApiError, createApiClient, type MealPlan, type MealPlanItem, type PatientProfile, type ReplacementCandidate } from '@/lib/api'
import { getToken } from '@/lib/auth'
import styles from './page.module.css'

const SLOT_LABEL: Record<string,string>={breakfast:'Bữa sáng',lunch:'Bữa trưa',dinner:'Bữa tối',snack:'Bữa phụ'}
const CHECKS=[['energy','Năng lượng'],['carb','Carbohydrate'],['distribution','Phân bổ bữa ăn'],['gi','GI/GL'],['allergy','Dị ứng']]

function Icon({name}:{name:string}){
  const paths:Record<string,React.ReactNode>={calendar:<><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M8 3v4M16 3v4M3 10h18"/></>,sparkle:<><path d="m12 2 1.4 5.6L19 9l-5.6 1.4L12 16l-1.4-5.6L5 9l5.6-1.4zM19 16l.7 2.3L22 19l-2.3.7L19 22l-.7-2.3L16 19l2.3-.7z"/></>,sun:<><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/><circle cx="12" cy="12" r="4"/></>,moon:<><path d="M20 15.5A8.5 8.5 0 0 1 8.5 4 8.5 8.5 0 1 0 20 15.5Z"/></>,check:<path d="m5 12 4 4L19 6"/>,warn:<><path d="M12 3 2 21h20zM12 9v5M12 18h.01"/></>,info:<><circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/></>,edit:<><path d="m4 20 4.5-1L19 8.5 15.5 5 5 15.5zM13.5 7l3.5 3.5M4 20h16"/></>,save:<><path d="M5 3h12l2 2v16H5zM8 3v6h8V3M8 21v-7h8v7"/></>,refresh:<><path d="M20 7v5h-5M4 17v-5h5M18.5 9A7 7 0 0 0 6 6.5L4 12M5.5 15A7 7 0 0 0 18 17.5l2-5.5"/></>}
  return <svg viewBox="0 0 24 24" aria-hidden="true"><g fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{paths[name]}</g></svg>
}

export default function NewMealPlanPage(){
  const router=useRouter()
  const [patients,setPatients]=useState<PatientProfile[]>([])
  const [patientId,setPatientId]=useState('')
  const [date,setDate]=useState(new Date().toISOString().slice(0,10))
  const [loading,setLoading]=useState(true)
  const [generating,setGenerating]=useState(false)
  const [error,setError]=useState('')
  const [plan,setPlan]=useState<MealPlan|null>(null)
  const [swapItem,setSwapItem]=useState<MealPlanItem|null>(null)
  const [candidates,setCandidates]=useState<ReplacementCandidate[]>([])
  const [swapping,setSwapping]=useState(false)
  const selected=useMemo(()=>patients.find(item=>item.id===patientId),[patientId,patients])
  const grouped=useMemo(()=>plan?.items.reduce<Record<string,MealPlanItem[]>>((acc,item)=>{(acc[item.slot]??=[]).push(item);return acc},{})??{},[plan])

  useEffect(()=>{const token=getToken();if(!token)return;createApiClient(token).listPatients(1,100).then(result=>{setPatients(result.items);const requested=new URLSearchParams(window.location.search).get('patient_id');setPatientId(result.items.some(item=>item.id===requested)?requested!:result.items[0]?.id??'')}).catch(value=>setError(value instanceof Error?value.message:'Không thể tải hồ sơ.')).finally(()=>setLoading(false))},[])

  const generate=async()=>{
    const token=getToken();if(!token||!patientId)return
    setGenerating(true);setError('');setPlan(null)
    try{
      const result=await createApiClient(token).createMealPlan(patientId,date)
      for(let attempt=0;attempt<30;attempt+=1){
        await new Promise(resolve=>setTimeout(resolve,2000))
        const current=await createApiClient(token).getMealPlan(result.plan_id)
        if(current.status==='pending_review'){setPlan(current);setGenerating(false);return}
        if(current.status==='failed'||current.status==='rejected')throw new Error('Hệ thống không thể tạo bản nháp an toàn cho cấu hình này.')
      }
      throw new Error('Quá thời gian chờ. Bản nháp vẫn được lưu và có thể xuất hiện trong hàng chờ sau.')
    }catch(value){setError(value instanceof ApiError?value.message:value instanceof Error?value.message:'Không thể sinh thực đơn.');setGenerating(false)}
  }

  const target=(key:string)=>{const item=plan?.targets?.targets?.[key];return item?.max_value??item?.min_value??null}
  const kcal=plan?.computed_nutrition?.kcal
  const carb=plan?.computed_nutrition?.carb_g
  const hasViolation=(term:string)=>plan?.violations.some(v=>(v.nutrient||'').toLowerCase().includes(term)||(v.message_vi||'').toLowerCase().includes(term))
  const openSwap=async(item:MealPlanItem)=>{const token=getToken();if(!token||!plan)return;setSwapItem(item);setCandidates([]);setError('');try{setCandidates(await createApiClient(token).listReplacementCandidates(plan.id,item.id))}catch(value){setError(value instanceof Error?value.message:'Không thể tải món thay thế.')}}
  const replaceItem=async(candidate:ReplacementCandidate)=>{const token=getToken();if(!token||!plan||!swapItem)return;setSwapping(true);setError('');try{setPlan(await createApiClient(token).replaceMealPlanItem(plan.id,swapItem.id,candidate.dish_id,candidate.serving_g));setSwapItem(null)}catch(value){setError(value instanceof Error?value.message:'Không thể đổi món.')}finally{setSwapping(false)}}

  return <div className={styles.page}>
    <div className={styles.breadcrumb}>Thực đơn <b>/</b> Tạo thực đơn nháp</div>
    <h1 className={styles.heading}>Sinh thực đơn cá nhân hóa</h1>
    <p className={styles.lead}>AI đề xuất món và khẩu phần. Hệ thống tính toán, kiểm tra an toàn trước khi chuyển chuyên gia duyệt.</p>
    <div className={styles.steps}>{['Chọn bệnh nhân','Thiết lập mục tiêu','Sinh & kiểm tra','Chuyên gia duyệt'].map((label,index)=><div className={`${styles.step} ${index===2?styles.active:''}`} key={label}><span>{index+1}</span><b>{label}</b></div>)}</div>

    <div className={styles.grid}>
      <div className={styles.leftCol}>
        <section className={styles.card}><header><h2>Hồ sơ bệnh nhân</h2></header><div className={styles.patientBody}>
          {loading?<div className={styles.loading}>Đang tải hồ sơ…</div>:<select aria-label="Chọn hồ sơ bệnh nhân" className={styles.patientSelect} value={patientId} onChange={e=>{setPatientId(e.target.value);setPlan(null)}}>{patients.map(p=><option key={p.id} value={p.id}>Hồ sơ #{p.id.slice(0,8)} · {p.age} tuổi</option>)}</select>}
          {selected&&<><div className={styles.patientIntro}><span>{selected.sex==='female'?'N':'B'}</span><div><strong>Hồ sơ #{selected.id.slice(0,8)}</strong><p>{selected.conditions.map(c=>c.code).join(' · ')||'Chưa ghi nhận bệnh nền'}</p></div></div><dl><div><dt>Mục tiêu năng lượng</dt><dd>{target('energy_kcal')?`${Math.round(target('energy_kcal')!)} kcal`:'Tính khi sinh'}</dd></div><div><dt>Carbohydrate</dt><dd>{target('carb_g')?`${Math.round(target('carb_g')!)} g/ngày`:'Tính khi sinh'}</dd></div><div><dt>Dị ứng</dt><dd>{selected.allergies.join(', ')||'Không có'}</dd></div><div><dt>Thuốc</dt><dd>{selected.medications.join(', ')||'Chưa ghi nhận'}</dd></div></dl></>}
        </div></section>
        {selected&&<section className={styles.card}><header><h2>Sở thích &amp; ràng buộc</h2></header><div className={styles.preferences}><span>⌁ Món Việt</span><span>♨ Theo hồ sơ</span><span>◫ Khẩu phần chuẩn</span><span>⊘ {selected.allergies.length?'Tránh dị ứng':'Không dị ứng'}</span></div></section>}
      </div>

      <div className={styles.centerCol}>
        <section className={styles.card}><header><h2>Thiết lập &amp; sinh thực đơn</h2></header><div className={styles.config}><div className={styles.controls}><label>Ngày áp dụng<div><Icon name="calendar"/><input type="date" value={date} onChange={e=>{setDate(e.target.value);setPlan(null)}}/></div></label><label>Số bữa<select value="3+1" disabled><option>3 bữa chính + 1 bữa phụ</option></select></label><label>Ưu tiên món<select value={selected?.region??'vn'} disabled><option value="vn">Món Việt Nam</option><option value="north">Miền Bắc</option><option value="central">Miền Trung</option><option value="south">Miền Nam</option></select></label></div><button className={styles.generate} onClick={generate} disabled={!patientId||generating||Boolean(plan)}><Icon name="sparkle"/>{generating?'Đang sinh và kiểm tra…':plan?'Đã sinh bản nháp':'Sinh thực đơn bằng AI'}</button><p className={styles.note}><Icon name="info"/>AI chỉ chọn món và gram — số dinh dưỡng do hệ thống tính từ dữ liệu có nguồn.</p>{error&&<div className={styles.error} role="alert">{error}</div>}</div></section>
        <section className={styles.card}><header><h2>{plan?`Bản nháp #${plan.id.slice(0,8).toUpperCase()}`:'Bản nháp thực đơn'}</h2></header><div className={styles.draft}>
          {!plan&&!generating&&<div className={styles.empty}>Chọn hồ sơ và nhấn “Sinh thực đơn bằng AI” để tạo bản nháp thật.</div>}
          {generating&&<div className={styles.empty}><span className="spinner"/> Hệ thống đang chọn món, tính dinh dưỡng và kiểm tra an toàn…</div>}
          {plan&&['breakfast','lunch','dinner','snack'].map(slot=>(grouped[slot]??[]).map((item,index)=><div className={styles.meal} key={item.id}><span className={styles.mealIcon}><Icon name={slot==='snack'?'moon':'sun'}/></span><small>{index===0?SLOT_LABEL[slot]:''}</small><strong>{item.name_vi}</strong><b>{Math.round(item.grams)} g</b><span className={styles.edit}><Icon name="edit"/></span><span className={styles.carbCell}/><button onClick={()=>openSwap(item)}>Đổi món</button></div>))}
        </div></section>
      </div>

      <aside className={styles.rightCol}><section className={styles.card}><header><h2>Kiểm tra lâm sàng</h2></header><div className={styles.checks}>{CHECKS.map(([key,label])=>{const verified=Boolean(plan?.review_packet&&Object.keys(plan.review_packet).length&&plan.menu_hash_ready&&plan.nutrition_hash_ready);const warning=Boolean(plan&&(key==='carb'?hasViolation('carb'):key==='allergy'?hasViolation('dị ứng'):false));let detail=verified?'Đã kiểm tra':'Chưa đủ dữ liệu kiểm tra';if(plan&&key==='energy')detail=kcal?`${Math.round(kcal)}${target('kcal')?` / ${Math.round(target('kcal')!)} kcal`:' kcal'}`:'Chưa tính';if(plan&&key==='carb')detail=carb?`${Math.round(carb)}${target('carb_g')?` / ${Math.round(target('carb_g')!)} g`:' g'}`:'Chưa tính';return <div className={styles.check} key={key}><span><Icon name={warning?'warn':verified?'check':'info'}/></span><b>{label}</b><small>{detail}</small><strong className={warning?styles.warnText:verified?styles.ok:styles.warnText}>{warning?'Lưu ý':verified?'Đạt':'Chờ'}</strong></div>})}
          <div className={styles.medication}><div><span><Icon name="warn"/></span><b>Thuốc – thực phẩm</b><strong>{plan&&plan.violations.some(v=>v.kind?.includes('interaction'))?'1 lưu ý':'Sẽ kiểm tra'}</strong></div><p>{selected?.medications.length?`${selected.medications.join(', ')}: kiểm tra thời điểm dùng thuốc cùng bữa ăn.`:'Chưa ghi nhận thuốc trong hồ sơ.'}</p></div><div className={styles.source}><Icon name="check"/>Số liệu hiển thị lấy từ nguồn backend đã kiểm chứng</div>
        </div></section></aside>
    </div>

    <footer className={styles.actionBar}><span className={styles.gate}><Icon name="warn"/>Chưa phát hành cho người bệnh</span><button className={styles.primary} disabled={!plan} onClick={()=>plan&&router.push(`/dietitian/reviews/${plan.id}`)}>Mở màn hình duyệt <b>›</b></button></footer>
    {swapItem&&<div className={styles.swapBackdrop} role="presentation" onMouseDown={()=>!swapping&&setSwapItem(null)}><section className={styles.swapPanel} role="dialog" aria-modal="true" aria-label="Đổi món" onMouseDown={event=>event.stopPropagation()}><header><div><small>Đổi món tại {SLOT_LABEL[swapItem.slot]}</small><h2>{swapItem.name_vi}</h2></div><button onClick={()=>setSwapItem(null)} aria-label="Đóng">×</button></header><p>Món thay thế được lấy từ cơ sở dữ liệu. Sau khi chọn, hệ thống sẽ tính lại toàn bộ dinh dưỡng và kiểm tra lâm sàng.</p><div className={styles.candidateList}>{!candidates.length?<div className={styles.empty}>Đang tải hoặc chưa có món phù hợp…</div>:candidates.map(candidate=><button key={candidate.dish_id} disabled={swapping} onClick={()=>replaceItem(candidate)}><span><strong>{candidate.name_vi}</strong><small>{candidate.region?`Miền ${candidate.region}`:'Phù hợp toàn quốc'}</small></span><b>{Math.round(candidate.serving_g)} g</b></button>)}</div></section></div>}
  </div>
}
