'use client'

import Link from 'next/link'
import { useCallback, useEffect, useState } from 'react'
import { Icon } from '@/components/brand-artwork'
import { ApiError, createApiClient, type DaySummary, type FoodLog, type MatchSuggestion } from '@/lib/api'
import { getToken } from '@/lib/auth'
import styles from './diary.module.css'

const SLOTS=[['breakfast','Bữa sáng'],['lunch','Bữa trưa'],['snack','Bữa phụ'],['dinner','Bữa tối']] as const
const VERDICT:Record<string,{label:string;tone:string}>={exceeded:{label:'Đã vượt ngưỡng',tone:'danger'},below_min:{label:'Thấp hơn mức tối thiểu',tone:'warning'},within:{label:'Trong ngưỡng',tone:'success'},insufficient_data:{label:'Chưa đủ dữ liệu',tone:'neutral'}}
function todayISO(){return new Date().toISOString().slice(0,10)}
function formatNutrient(value:number|null,unit:string|null){if(value==null)return 'Chưa tính được';const digits=unit==='kcal'||unit==='mg'?0:1;return `${new Intl.NumberFormat('vi-VN',{maximumFractionDigits:digits}).format(value)}${unit?` ${unit}`:''}`}

export default function DiaryPage(){
  const [profileId,setProfileId]=useState('')
  const [day,setDay]=useState(todayISO())
  const [logs,setLogs]=useState<FoodLog[]>([])
  const [summary,setSummary]=useState<DaySummary|null>(null)
  const [loading,setLoading]=useState(true)
  const [saving,setSaving]=useState(false)
  const [error,setError]=useState('')
  const [text,setText]=useState('')
  const [grams,setGrams]=useState('')
  const [slot,setSlot]=useState('lunch')
  const [notice,setNotice]=useState('')
  const [suggestions,setSuggestions]=useState<MatchSuggestion[]>([])
  const [selectedFoodId,setSelectedFoodId]=useState<number|null>(null)
  const [noSuitableMatch,setNoSuitableMatch]=useState(false)
  const [suggesting,setSuggesting]=useState(false)

  const refresh=useCallback(async(pid:string,targetDay:string)=>{const token=getToken();if(!token)return;const api=createApiClient(token);const [items,total]=await Promise.all([api.listFoodLogs(pid,targetDay),api.getDaySummary(pid,targetDay)]);setLogs(items);setSummary(total)},[])

  useEffect(()=>{const token=getToken();if(!token)return;createApiClient(token).getMyProfile().then(async profile=>{setProfileId(profile.id);await refresh(profile.id,day)}).catch(value=>setError(value instanceof ApiError?value.message:'Không thể tải nhật ký.')).finally(()=>setLoading(false))},[day,refresh])

  useEffect(()=>{if(text.trim().length<2)return;const token=getToken();if(!token)return;const timer=window.setTimeout(()=>{setSuggesting(true);createApiClient(token).suggestFoods(text.trim()).then(result=>setSuggestions(result.suggestions)).catch(()=>setSuggestions([])).finally(()=>setSuggesting(false))},300);return()=>window.clearTimeout(timer)},[text])

  function changeFoodText(value:string){setText(value);setSelectedFoodId(null);setNoSuitableMatch(false);if(value.trim().length<2)setSuggestions([])}

  async function add(event:React.FormEvent){event.preventDefault();if(!profileId||!text.trim())return;if(suggestions.length&&!selectedFoodId&&!noSuitableMatch){setError('Hãy chọn món phù hợp hoặc xác nhận món không có trong danh sách.');return}setSaving(true);setError('');try{const created=await createApiClient(getToken()!).createFoodLog({profile_id:profileId,free_text_vi:text.trim(),food_id:selectedFoodId,grams:grams?Number(grams):null,slot});setText('');setGrams('');setSuggestions([]);setSelectedFoodId(null);setNoSuitableMatch(false);setNotice(created.match_status==='unmatched'?'Đã lưu. Món này chưa đủ dữ liệu nên chưa được cộng vào tổng.':'Đã ghi nhận món ăn.');await refresh(profileId,day);window.setTimeout(()=>setNotice(''),3200)}catch(value){setError(value instanceof ApiError?value.message:'Không thể lưu nhật ký.')}finally{setSaving(false)}}

  return <div className={styles.page}>
    <header className={styles.header}><div><small>MÓN ĂN THỰC TẾ</small><h1>Món bạn đã ăn</h1><p>Dùng trang này khi bạn ăn món khác kế hoạch hoặc muốn ghi thêm món thực tế.</p></div><label>Ngày xem<input type="date" value={day} max={todayISO()} onChange={event=>{setLoading(true);setDay(event.target.value)}}/></label></header>
    {error&&<div className={styles.error}><Icon name="warning"/>{error}</div>}{notice&&<div className={styles.notice}><Icon name="check"/>{notice}</div>}
    {loading?<div className={styles.skeleton}/>:<div className={styles.layout}>
      <main>
        <form className={styles.form} onSubmit={add}><div><small>THÊM GHI NHẬN</small><h2>Hôm đó bạn đã ăn gì?</h2><p>Cứ dùng tên món quen thuộc; hệ thống sẽ đưa lựa chọn khi tên món còn chung chung.</p></div><label className={styles.food}><span>Tên món</span><input value={text} onChange={event=>changeFoodText(event.target.value)} placeholder="VD: cơm tẻ, canh rau muống, cá kho…" maxLength={255} required autoComplete="off"/></label>{(suggesting||suggestions.length>0)&&<div className="diary-suggestion-panel" aria-live="polite"><div><strong>{suggesting?'Đang tìm món phù hợp…':'Bạn muốn nói đến món nào?'}</strong>{!suggesting&&<small>Chọn đúng loại để hệ thống không phải đoán.</small>}</div>{!suggesting&&<div className="diary-suggestion-list">{suggestions.map(item=><button type="button" key={item.food_id} className={selectedFoodId===item.food_id?'selected':undefined} onClick={()=>{setSelectedFoodId(item.food_id);setNoSuitableMatch(false)}}><span>{item.name_vi}</span><small>{Math.round(item.score*100)}% phù hợp</small></button>)}<button type="button" className={noSuitableMatch?'selected':undefined} onClick={()=>{setNoSuitableMatch(true);setSelectedFoodId(null)}}><span>Không có trong danh sách</span><small>Chuyển chuyên gia đối chiếu</small></button></div>}</div>}<div className={styles.formRow}><label><span>Khẩu phần gram</span><input type="number" value={grams} onChange={event=>setGrams(event.target.value)} min="1" max="5000" placeholder="Có thể để trống"/></label><label><span>Bữa ăn</span><select value={slot} onChange={event=>setSlot(event.target.value)}>{SLOTS.map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></label><button type="submit" disabled={saving||suggesting||!text.trim()}>{saving?'Đang lưu…':'Ghi vào nhật ký'}<Icon name="arrowRight"/></button></div></form>

        <section className={styles.logs}><div className={styles.cardTitle}><div><small>THEO BỮA</small><h2>Đã ghi trong ngày</h2></div><span>{logs.length} món</span></div>{logs.length?<div>{logs.map(log=><LogRow key={log.id} log={log}/>)}</div>:<div className={styles.empty}><Icon name="diary"/><h3>Chưa có món nào</h3><p>Ghi nhận đầu tiên để bắt đầu tổng hợp ngày.</p></div>}</section>
      </main>
      <aside>
        <section className={styles.coverage}><div className={styles.cardTitle}><div><small>ĐỘ ĐẦY ĐỦ DỮ LIỆU</small><h2>{summary?Math.round(summary.coverage*100):0}%</h2></div><Icon name="database"/></div><div className={styles.progress}><i style={{width:`${summary?summary.coverage*100:0}%`}}/></div><p>{summary?.is_complete?'Các món đã được đối chiếu để tạo tổng hợp ngày.':'Còn món chưa tra được, các con số hiện tại chỉ là mức tối thiểu và không được dùng để kết luận “đạt”.'}</p></section>
        <section className={styles.verdicts}><div className={styles.cardTitle}><div><small>TỔNG HỢP NGÀY</small><h2>Kết quả có điều kiện</h2></div></div>{summary?.verdicts.length?summary.verdicts.map(item=>{const ui=VERDICT[item.verdict]||VERDICT.insufficient_data;return <article key={item.nutrient} data-tone={ui.tone}><span/><div><strong>{item.label_vi}</strong><small>{formatNutrient(item.counted,item.unit)}{item.max_value!=null?` / tối đa ${formatNutrient(item.max_value,item.unit)}`:item.min_value!=null?` / tối thiểu ${formatNutrient(item.min_value,item.unit)}`:''}</small></div><b>{ui.label}</b></article>}):<p className={styles.noData}>Chưa có dữ liệu để tổng hợp.</p>}</section>
        <section className={styles.help}><Icon name="info"/><div><h2>Không cần ghi hoàn hảo</h2><p>Nhật ký dùng để hiểu xu hướng. Cuối tuần, hệ thống tổng hợp thay vì gửi từng bữa cho chuyên gia.</p><Link href="/patient/weekly">Xem tuần của tôi<Icon name="arrowRight"/></Link></div></section>
      </aside>
    </div>}
  </div>
}

function LogRow({log}:{log:FoodLog}){const unresolved=log.match_status==='unmatched'||log.match_status==='no_data';return <article className={styles.logRow}><span><Icon name={unresolved?'warning':'check'}/></span><div><small>{SLOTS.find(([value])=>value===log.slot)?.[1]||'Không rõ bữa'} · {new Date(log.logged_at).toLocaleTimeString('vi-VN',{hour:'2-digit',minute:'2-digit'})}</small><strong>{log.food_name_vi||log.free_text_vi}</strong>{log.food_name_vi&&log.free_text_vi!==log.food_name_vi&&<p>Bạn ghi: {log.free_text_vi}</p>}</div><b>{log.grams!=null?`${log.grams} g`:'Chưa có gram'}</b><em>{unresolved?'Chờ đối chiếu':'Đã tra được'}</em></article>}
