'use client'

import Link from 'next/link'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Icon } from '@/components/brand-artwork'
import { PatientAvatar } from '@/components/patient-avatar'
import { ApiError, createApiClient, type FoodLog, type PatientProfile } from '@/lib/api'
import { getToken } from '@/lib/auth'
import { CONDITION_LABELS } from '@/lib/labels'

const SLOT:Record<string,string>={breakfast:'Bữa sáng',lunch:'Bữa trưa',snack:'Bữa phụ',dinner:'Bữa tối'}
const isSkippedMeal=(log:FoodLog)=>(log.free_text_vi??'').trim().toLocaleLowerCase('vi-VN').startsWith('bỏ ')

// FE-13: matched_on là field kỹ thuật của bộ khớp món (xem src/clinical/matching.py:112,
// enum "exact"|"alias"|"token" — xác nhận qua tests/test_matching.py). Map sang nhãn dinh
// dưỡng viên hiểu được; fallback về giá trị gốc nếu backend thêm enum mới chưa map.
const MATCH_REASON_LABEL:Record<string,string>={exact:'Khớp chính xác tên món',alias:'Khớp theo tên gọi khác',token:'Khớp gần đúng theo từ khoá'}

// FE-10: mitigation tạm thời cho BE-01 (backend trả confidence score giống hệt nhau
// cho nhiều ứng viên khác nhau, vi phạm RULE-2). Gỡ bỏ khi BE-01 đóng và xác nhận
// score đã phân biệt được thật sự — đây chỉ là cảnh báo, không sửa được dữ liệu gốc.
const SCORE_DISTINGUISH_THRESHOLD = 0.01

export default function DietitianFoodLogsPage(){
  const [rows,setRows]=useState<FoodLog[]>([])
  const [patients,setPatients]=useState<Record<string,PatientProfile>>({})
  const [loading,setLoading]=useState(true)
  const [busyId,setBusyId]=useState<string|null>(null)
  const [error,setError]=useState('')
  const [tab,setTab]=useState<'attention'|'mapping'>('attention')
  const [focusedProfileId,setFocusedProfileId]=useState('')

  const refresh=useCallback(async()=>{const token=getToken();if(!token)return;const api=createApiClient(token);try{const [logs,result]=await Promise.all([api.listUnresolvedLogs(),api.listPatients(1,100)]);setRows(logs);setPatients(Object.fromEntries(result.items.map(patient=>[patient.id,patient])))}catch(value){setError(value instanceof ApiError?value.message:'Không thể tải dữ liệu theo dõi.')}},[])
  useEffect(()=>{
    let cancelled=false
    const timer=window.setTimeout(()=>{const params=new URLSearchParams(window.location.search);const profileId=params.get('profile_id')||'';if(profileId){setFocusedProfileId(profileId);setTab('mapping')}},0)
    async function load(){await refresh();if(!cancelled)setLoading(false)}
    void load()
    return()=>{cancelled=true;window.clearTimeout(timer)}
  },[refresh])

  const visibleRows=useMemo(()=>focusedProfileId?rows.filter(row=>row.profile_id===focusedProfileId):rows,[rows,focusedProfileId])
  const grouped=useMemo(()=>Object.entries(visibleRows.reduce<Record<string,FoodLog[]>>((acc,row)=>{(acc[row.profile_id]??=[]).push(row);return acc},{})).sort((a,b)=>b[1].length-a[1].length),[visibleRows])
  const mappableRows=useMemo(()=>visibleRows.filter(row=>!isSkippedMeal(row)),[visibleRows])
  const skippedRows=useMemo(()=>visibleRows.filter(isSkippedMeal),[visibleRows])

  async function resolve(logId:string,body:{action:'map_to_existing'|'mark_no_data';food_id?:number;grams?:number}){setBusyId(logId);setError('');try{await createApiClient(getToken()!).resolveFoodLog(logId,body);await refresh()}catch(value){setError(value instanceof Error?value.message:'Không thể xử lý dòng nhật ký.')}finally{setBusyId(null)}}

  return <div className="min-h-screen px-[28px] pt-[20px] pb-10 text-[var(--c-ink)] max-[900px]:px-[15px] max-[900px]:pt-[58px] max-[900px]:pb-[30px]">
    <header className="flex items-start justify-between max-[520px]:grid max-[520px]:gap-2">
      <div><small className="text-[9px] font-extrabold tracking-[.13em] text-[#0e5f95]">NHẬT KÝ CẦN ĐỐI CHIẾU</small><h1 className="mt-1 font-[family-name:var(--f-serif)] text-[20px] font-semibold tracking-[-.01em]">Đối chiếu nhật ký</h1><p className="mt-1 max-w-[720px] text-[9.5px] leading-[1.5] text-[#626e75]">Chỉ hiển thị bệnh nhân có món chưa rõ hoặc bữa cần chú ý; dữ liệu ổn định không tạo thêm việc.</p></div>
      <span className="rounded-full bg-[#e3f0f4] px-2.5 py-1.5 text-[9px] font-bold text-[var(--c-green2)]">Tuần hiện tại</span>
    </header>
    <section className="mt-3.5 grid grid-cols-3 gap-2.5 max-[900px]:grid-cols-2 max-[520px]:grid-cols-1">
      <article className="flex min-h-[62px] items-center gap-2.5 rounded-xl border border-[#d8e1e3] bg-white px-3 py-2.5"><span className="grid h-7 w-7 flex-none place-items-center rounded-lg bg-[#e3f0f4] text-[var(--c-green2)]"><Icon name="warning" className="w-3.5"/></span><div><small className="block text-[7.5px]">BỆNH NHÂN CẦN CHÚ Ý</small><strong className="mt-0.5 block font-[family-name:var(--f-serif)] text-[20px] font-semibold">{loading?'':grouped.length}</strong></div></article>
      <article className="flex min-h-[62px] items-center gap-2.5 rounded-xl border border-[#d8e1e3] bg-white px-3 py-2.5"><span className="grid h-7 w-7 flex-none place-items-center rounded-lg bg-[#e3f0f4] text-[var(--c-green2)]"><Icon name="diary" className="w-3.5"/></span><div><small className="block text-[7.5px]">MÓN CHỜ ĐỐI CHIẾU</small><strong className="mt-0.5 block font-[family-name:var(--f-serif)] text-[20px] font-semibold">{loading?'':mappableRows.length}</strong></div></article>
      <article className="flex min-h-[62px] items-center gap-2.5 rounded-xl border border-[#d8e1e3] bg-white px-3 py-2.5"><span className="grid h-7 w-7 flex-none place-items-center rounded-lg bg-[#e3f0f4] text-[var(--c-green2)]"><Icon name="info" className="w-3.5"/></span><div><small className="block text-[7.5px]">BỮA ĐƯỢC BÁO BỎ</small><strong className="mt-0.5 block font-[family-name:var(--f-serif)] text-[20px] font-semibold">{loading?'':skippedRows.length}</strong></div></article>
    </section>
    {focusedProfileId&&<div className="active-filter-note"><span>Đang xem hồ sơ #{focusedProfileId.slice(0,8)}</span><button type="button" onClick={()=>{setFocusedProfileId('');window.history.replaceState(null,'','/dietitian/food-logs')}}>Xem tất cả</button></div>}
    <div className="mt-3 mb-2.5 flex w-fit rounded-[10px] bg-[#e9f1f2] p-1">
      <button type="button" className={`min-h-[30px] rounded-lg px-2.5 text-[9px] font-bold ${tab==='attention'?'bg-white text-[var(--c-green2)] shadow-[0_4px_12px_rgba(22,85,83,.08)]':'text-[#647077]'}`} onClick={()=>setTab('attention')}>Bệnh nhân cần chú ý ({grouped.length})</button>
      <button type="button" className={`min-h-[30px] rounded-lg px-2.5 text-[9px] font-bold ${tab==='mapping'?'bg-white text-[var(--c-green2)] shadow-[0_4px_12px_rgba(22,85,83,.08)]':'text-[#647077]'}`} onClick={()=>setTab('mapping')}>Đối chiếu món ({mappableRows.length})</button>
    </div>
    {error&&<div className="mb-2.5 flex gap-2 rounded-[10px] border border-[#efb5a5] bg-[#fff5f1] p-2.5 text-[9px] text-[#8b3d2b]"><Icon name="warning" className="w-[16px]"/>{error}</div>}
    {loading?<div className="grid gap-2">{[0,1,2].map(i=><i key={i} className="h-[88px] animate-[skeleton-pulse_1.3s_infinite] rounded-xl bg-[linear-gradient(90deg,#e7eeef,var(--c-bg),#e7eeef)] bg-[length:200%_100%]"/>)}</div>
      :tab==='attention'?<AttentionList groups={grouped} patients={patients} onOpenMapping={profileId=>{setFocusedProfileId(profileId);setTab('mapping');window.history.replaceState(null,'',`/dietitian/food-logs?profile_id=${profileId}`)}}/>
      :<div className="grid gap-2">{mappableRows.length?mappableRows.map(row=><UnresolvedRow key={row.id} row={row} patient={patients[row.profile_id]} busy={busyId===row.id} onResolve={resolve}/>):<Empty/>}</div>}
  </div>
}

function AttentionList({groups,patients,onOpenMapping}:{groups:Array<[string,FoodLog[]]>;patients:Record<string,PatientProfile>;onOpenMapping:(profileId:string)=>void}){
  if(!groups.length)return <Empty/>
  return <div className="grid gap-2">{groups.map(([profileId,logs])=>{
    const patient=patients[profileId];const latest=logs[0];const skipped=logs.filter(isSkippedMeal).length;const unmatched=logs.length-skipped
    const summary=[skipped?`${skipped} bữa được báo bỏ`:null,unmatched?`${unmatched} món cần đối chiếu`:null].filter(Boolean).join(' · ')
    return <article key={profileId} className="grid min-h-[76px] grid-cols-[40px_minmax(140px,.7fr)_minmax(220px,1.3fr)_auto] items-center gap-3 rounded-xl border border-[#d8e1e3] bg-white px-3 py-2.5 max-[900px]:grid-cols-[40px_1fr]">
      {patient?<PatientAvatar sex={patient.sex}/>:<Icon name="user"/>}
      <div><small className="text-[7px] font-extrabold text-[#0e5f95]">MÃ HỒ SƠ {profileId.slice(0,8).toUpperCase()}</small><h2 className="mt-0.5 font-[family-name:var(--f-serif)] text-[13px]">{patient?`${patient.sex==='male'?'Nam':'Nữ'}, ${patient.age} tuổi`:'Bệnh nhân'}</h2><p className="mt-0.5 text-[8px] text-[#69747b]">{patient?.conditions.map(item=>CONDITION_LABELS[item.code]??item.code).join(' · ')||'Chưa có thông tin bệnh nền'}</p></div>
      <div className="grid max-[900px]:col-start-2"><span className="w-fit rounded-full bg-[#fff4d9] px-[6px] py-[3px] text-[7px] font-extrabold text-[#9a6517]">{unmatched?'Cần đối chiếu dữ liệu':'Cần theo dõi tuân thủ'}</span><strong className="mt-1 text-[9.5px]">{summary}</strong><small className="mt-0.5 text-[8px] text-[#69747b]">Gần nhất: “{latest.free_text_vi}” · {new Date(latest.logged_at).toLocaleDateString('vi-VN')}</small></div>
      <div className="flex gap-[6px] max-[900px]:col-start-2 max-[520px]:col-span-full">
        <Link className="flex min-h-[32px] items-center gap-[5px] rounded-lg border border-[#cad5d8] px-2.5 text-[8px] font-bold max-[520px]:flex-1 max-[520px]:justify-center" href={`/dietitian/patients/${profileId}`}>Xem hồ sơ</Link>
        {unmatched>0&&<button type="button" className="flex min-h-[32px] items-center gap-[5px] rounded-lg border border-transparent bg-[var(--c-green)] px-2.5 text-[8px] font-bold text-white max-[520px]:flex-1 max-[520px]:justify-center" onClick={()=>onOpenMapping(profileId)}>Đối chiếu món<Icon name="arrowRight" className="w-3.5"/></button>}
      </div>
    </article>
  })}</div>
}

function UnresolvedRow({row,patient,busy,onResolve}:{row:FoodLog;patient?:PatientProfile;busy:boolean;onResolve:(logId:string,body:{action:'map_to_existing'|'mark_no_data';food_id?:number;grams?:number})=>void}){
  const [grams,setGrams]=useState(row.grams!=null?String(row.grams):'')
  const [chosen,setChosen]=useState<number|null>(row.suggestions[0]?.food_id??null)
  const invalid=!grams||Number(grams)<=0
  const topScores=row.suggestions.slice(0,5).map(item=>item.score)
  const scoresIndistinguishable=topScores.length>1&&(Math.max(...topScores)-Math.min(...topScores))<SCORE_DISTINGUISH_THRESHOLD
  const suggestionCount=row.suggestions.slice(0,5).length
  return <article className="rounded-xl border border-[#d8e1e3] bg-white p-3">
    <header className="flex justify-between gap-3"><div><small className="text-[8px] font-bold text-[#0e5c91]">{patient?`${patient.sex==='male'?'Nam':'Nữ'}, ${patient.age} tuổi`:`Mã hồ sơ ${row.profile_id.slice(0,8).toUpperCase()}`} · {SLOT[row.slot??'']||'Không rõ bữa'}</small><h2 className="mt-0.5 font-[family-name:var(--f-serif)] text-[14px]">“{row.free_text_vi}”</h2></div><time className="text-[8px] text-[#69747b]">{new Date(row.logged_at).toLocaleString('vi-VN')}</time></header>
    <p className="mt-1.5 text-[8.5px] text-[#636e75]">Hệ thống chưa đủ chắc chắn để tính món này. Chuyên gia chọn một ứng viên hoặc xác nhận không đủ dữ liệu.</p>
    {row.suggestions.length?<div className="mt-2 grid grid-cols-2 gap-[6px] max-[900px]:grid-cols-1">{row.suggestions.slice(0,5).map((item,index)=><label key={item.food_id} className={`flex min-h-[38px] items-center gap-2 rounded-lg border p-2 ${chosen===item.food_id?'border-[var(--c-green)] bg-[#eaf4f7]':'border-[#dce4e5]'} ${index===suggestionCount-1&&suggestionCount%2===1?'col-span-full':''}`}><input type="radio" name={`sug-${row.id}`} checked={chosen===item.food_id} onChange={()=>setChosen(item.food_id)}/><span className="grid"><strong className="text-[9px]">{item.name_vi}</strong><small className="mt-0.5 text-[7px] text-[#6c777e]">{MATCH_REASON_LABEL[item.matched_on]||item.matched_on} · {(item.score*100).toFixed(0)}%</small></span></label>)}</div>:<div className="mt-2 rounded-lg bg-[#f3f6f7] p-2.5 text-[8.5px] text-[#68747b]">Không có ứng viên đủ gần. Không tự đoán món.</div>}
    {scoresIndistinguishable&&<p className="mt-2 flex items-center gap-[6px] rounded-lg border border-[#f0d896] bg-[#fff4d9] px-2.5 py-2 text-[8px] font-semibold text-[#9a6517]"><Icon name="warning" className="w-3.5 flex-none"/>Độ tin cậy chưa phân biệt rõ giữa các lựa chọn — chuyên gia tự xem xét, không nên dựa vào tỉ lệ %.</p>}
    <footer className="mt-2.5 flex flex-wrap gap-2 max-[520px]:grid">
      <input className="h-[33px] w-[110px] rounded-lg border border-[#cad5d8] px-2.5 text-[9px] outline-none max-[520px]:w-full" type="number" min="1" max="5000" value={grams} onChange={event=>setGrams(event.target.value)} placeholder="Số gram"/>
      <button type="button" className="min-h-[33px] rounded-lg border border-transparent bg-[var(--c-green)] px-2.5 text-[8px] font-bold text-white disabled:cursor-not-allowed disabled:opacity-50" disabled={busy||chosen==null||invalid} onClick={()=>onResolve(row.id,{action:'map_to_existing',food_id:chosen!,grams:Number(grams)})}>{busy?'Đang lưu…':'Gán món và tính lại'}</button>
      <button type="button" className="min-h-[33px] rounded-lg border border-[#cad5d8] px-2.5 text-[8px] font-bold disabled:cursor-not-allowed disabled:opacity-50" disabled={busy} onClick={()=>onResolve(row.id,{action:'mark_no_data'})}>Không đủ dữ liệu</button>
    </footer>
  </article>
}

function Empty(){return <div className="grid min-h-[240px] content-center place-items-center rounded-xl border border-[#d8e1e3] bg-white text-center"><Icon name="check" className="w-9 rounded-xl bg-[#e3f0f4] p-2 text-[var(--c-green2)]"/><h2 className="mt-2.5 font-[family-name:var(--f-serif)] text-[15px]">Không có ngoại lệ đang chờ</h2><p className="mt-1 text-[9px] text-[#68747b]">Mọi món đã được đối chiếu hoặc đánh dấu trung thực là không đủ dữ liệu.</p></div>}
