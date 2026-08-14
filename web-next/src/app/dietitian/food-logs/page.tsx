'use client'

import Link from 'next/link'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Icon } from '@/components/brand-artwork'
import { ApiError, createApiClient, type FoodLog, type PatientProfile } from '@/lib/api'
import { getToken } from '@/lib/auth'
import styles from './followup.module.css'

const SLOT:Record<string,string>={breakfast:'Bữa sáng',lunch:'Bữa trưa',snack:'Bữa phụ',dinner:'Bữa tối'}
const isSkippedMeal=(log:FoodLog)=>(log.free_text_vi??'').trim().toLocaleLowerCase('vi-VN').startsWith('bỏ ')

export default function DietitianFoodLogsPage(){
  const [rows,setRows]=useState<FoodLog[]>([])
  const [patients,setPatients]=useState<Record<string,PatientProfile>>({})
  const [loading,setLoading]=useState(true)
  const [busyId,setBusyId]=useState<string|null>(null)
  const [error,setError]=useState('')
  const [tab,setTab]=useState<'attention'|'mapping'>('attention')

  const refresh=useCallback(async()=>{const token=getToken();if(!token)return;const api=createApiClient(token);try{const [logs,result]=await Promise.all([api.listUnresolvedLogs(),api.listPatients(1,100)]);setRows(logs);setPatients(Object.fromEntries(result.items.map(patient=>[patient.id,patient])))}catch(value){setError(value instanceof ApiError?value.message:'Không thể tải dữ liệu theo dõi.')}},[])
  useEffect(()=>{
    let cancelled=false
    async function load(){await refresh();if(!cancelled)setLoading(false)}
    void load()
    return()=>{cancelled=true}
  },[refresh])

  const grouped=useMemo(()=>Object.entries(rows.reduce<Record<string,FoodLog[]>>((acc,row)=>{(acc[row.profile_id]??=[]).push(row);return acc},{})).sort((a,b)=>b[1].length-a[1].length),[rows])
  const mappableRows=useMemo(()=>rows.filter(row=>!isSkippedMeal(row)),[rows])
  const skippedRows=useMemo(()=>rows.filter(isSkippedMeal),[rows])

  async function resolve(logId:string,body:{action:'map_to_existing'|'mark_no_data';food_id?:number;grams?:number}){setBusyId(logId);setError('');try{await createApiClient(getToken()!).resolveFoodLog(logId,body);await refresh()}catch(value){setError(value instanceof Error?value.message:'Không thể xử lý dòng nhật ký.')}finally{setBusyId(null)}}

  return <div className={styles.page}>
    <header className={styles.header}><div><small>EXCEPTION-BASED FOLLOW-UP</small><h1>Theo dõi tuần</h1><p>Trang ưu tiên những bệnh nhân có dữ liệu cần đối chiếu. Các bữa ổn định không tạo thêm việc duyệt thủ công.</p></div><span>Tuần hiện tại</span></header>
    <section className={styles.metrics}><article><span><Icon name="warning"/></span><div><small>BỆNH NHÂN CẦN CHÚ Ý</small><strong>{loading?'':grouped.length}</strong></div></article><article><span><Icon name="diary"/></span><div><small>MÓN CHỜ ĐỐI CHIẾU</small><strong>{loading?'':mappableRows.length}</strong></div></article><article><span><Icon name="info"/></span><div><small>BỮA ĐƯỢC BÁO BỎ</small><strong>{loading?'':skippedRows.length}</strong></div></article></section>
    <div className={styles.tabs}><button className={tab==='attention'?styles.active:undefined} onClick={()=>setTab('attention')}>Bệnh nhân cần chú ý ({grouped.length})</button><button className={tab==='mapping'?styles.active:undefined} onClick={()=>setTab('mapping')}>Đối chiếu món ({mappableRows.length})</button></div>
    {error&&<div className={styles.error}><Icon name="warning"/>{error}</div>}
    {loading?<div className={styles.skeleton}><i/><i/><i/></div>:tab==='attention'?<AttentionList groups={grouped} patients={patients} onOpenMapping={()=>setTab('mapping')}/>:<div className={styles.mapping}>{mappableRows.length?mappableRows.map(row=><UnresolvedRow key={row.id} row={row} patient={patients[row.profile_id]} busy={busyId===row.id} onResolve={resolve}/>):<Empty/>}</div>}
  </div>
}

function AttentionList({groups,patients,onOpenMapping}:{groups:Array<[string,FoodLog[]]>;patients:Record<string,PatientProfile>;onOpenMapping:()=>void}){if(!groups.length)return <Empty/>;return <div className={styles.attentionList}>{groups.map(([profileId,logs])=>{const patient=patients[profileId];const latest=logs[0];const skipped=logs.filter(isSkippedMeal).length;const unmatched=logs.length-skipped;const summary=[skipped?`${skipped} bữa được báo bỏ`:null,unmatched?`${unmatched} món cần đối chiếu`:null].filter(Boolean).join(' · ');return <article key={profileId}><span className={styles.avatar}>{patient?.sex==='female'?'Nữ':'N'}</span><div className={styles.patient}><small>HỒ SƠ #{profileId.slice(0,8)}</small><h2>{patient?`${patient.sex==='male'?'Nam':'Nữ'}, ${patient.age} tuổi`:'Bệnh nhân'}</h2><p>{patient?.conditions.map(item=>item.code).join(' · ')||'Chưa có thông tin bệnh nền'}</p></div><div className={styles.reason}><span>{unmatched?'Cần đối chiếu dữ liệu':'Cần theo dõi tuân thủ'}</span><strong>{summary}</strong><small>Gần nhất: “{latest.free_text_vi}” · {new Date(latest.logged_at).toLocaleDateString('vi-VN')}</small></div><div className={styles.actions}><Link href={`/dietitian/patients/${profileId}`}>Xem hồ sơ</Link>{unmatched>0&&<button type="button" onClick={onOpenMapping}>Đối chiếu món<Icon name="arrowRight"/></button>}</div></article>})}</div>}

function UnresolvedRow({row,patient,busy,onResolve}:{row:FoodLog;patient?:PatientProfile;busy:boolean;onResolve:(logId:string,body:{action:'map_to_existing'|'mark_no_data';food_id?:number;grams?:number})=>void}){
  const [grams,setGrams]=useState(row.grams!=null?String(row.grams):'')
  const [chosen,setChosen]=useState<number|null>(row.suggestions[0]?.food_id??null)
  const invalid=!grams||Number(grams)<=0
  return <article className={styles.logRow}><header><div><small>{patient?`${patient.sex==='male'?'Nam':'Nữ'}, ${patient.age} tuổi`:`Hồ sơ #${row.profile_id.slice(0,8)}`} · {SLOT[row.slot??'']||'Không rõ bữa'}</small><h2>“{row.free_text_vi}”</h2></div><time>{new Date(row.logged_at).toLocaleString('vi-VN')}</time></header><p>Hệ thống chưa đủ chắc chắn để tính món này. Chuyên gia chọn một ứng viên hoặc xác nhận không đủ dữ liệu.</p>{row.suggestions.length?<div className={styles.suggestions}>{row.suggestions.slice(0,5).map(item=><label key={item.food_id} className={chosen===item.food_id?styles.selected:undefined}><input type="radio" name={`sug-${row.id}`} checked={chosen===item.food_id} onChange={()=>setChosen(item.food_id)}/><span><strong>{item.name_vi}</strong><small>{item.matched_on} · {(item.score*100).toFixed(0)}%</small></span></label>)}</div>:<div className={styles.noSuggestion}>Không có ứng viên đủ gần. Không tự đoán món.</div>}<footer><input type="number" min="1" max="5000" value={grams} onChange={event=>setGrams(event.target.value)} placeholder="Khẩu phần gram"/><button type="button" disabled={busy||chosen==null||invalid} onClick={()=>onResolve(row.id,{action:'map_to_existing',food_id:chosen!,grams:Number(grams)})}>{busy?'Đang lưu…':'Gán món và tính lại'}</button><button type="button" disabled={busy} onClick={()=>onResolve(row.id,{action:'mark_no_data'})}>Không đủ dữ liệu</button></footer></article>
}

function Empty(){return <div className={styles.empty}><Icon name="check"/><h2>Không có ngoại lệ đang chờ</h2><p>Mọi món đã được đối chiếu hoặc đánh dấu trung thực là không đủ dữ liệu.</p></div>}
