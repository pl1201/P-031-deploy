'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { Icon } from '@/components/brand-artwork'
import { PatientAvatar } from '@/components/patient-avatar'
import { ApiError, createApiClient, type PatientProfile, type ProfileUpdateRequest } from '@/lib/api'
import { getToken } from '@/lib/auth'
import { ACTIVITY_LABELS as ACTIVITY, CONDITION_LABELS as CONDITION, REGION_LABELS as REGION } from '@/lib/labels'

type FormState={user_id:string;age:string;sex:'male'|'female';height_cm:string;weight_kg:string;activity_level:PatientProfile['activity_level'];condition:string;medications:string;allergies:string;region:PatientProfile['region']}
const EMPTY:FormState={user_id:'',age:'',sex:'male',height_cm:'',weight_kg:'',activity_level:'light',condition:'T2DM',medications:'',allergies:'',region:'north'}

export default function PatientsPage(){
  const [patients,setPatients]=useState<PatientProfile[]>([])
  const [loading,setLoading]=useState(true)
  const [error,setError]=useState('')
  const [query,setQuery]=useState('')
  const [total,setTotal]=useState(0)
  const [page,setPage]=useState(1)
  const [requests,setRequests]=useState<ProfileUpdateRequest[]>([])
  const [resolutionNotes,setResolutionNotes]=useState<Record<string,string>>({})
  const [resolvingId,setResolvingId]=useState('')
  const [createOpen,setCreateOpen]=useState(false)
  const [form,setForm]=useState<FormState>(EMPTY)
  const [saving,setSaving]=useState(false)

  useEffect(()=>{
    const token=getToken();if(!token)return
    let cancelled=false
    const timer=window.setTimeout(async()=>{
      try{const api=createApiClient(token!);const [result,pending]=await Promise.all([api.listPatients(page,20,query||undefined),api.listProfileUpdateRequests()]);if(!cancelled){setPatients(result.items);setTotal(result.total);setRequests(pending)}}
      catch(value){if(!cancelled)setError(value instanceof ApiError?value.message:'Không thể tải hồ sơ.')}
      finally{if(!cancelled)setLoading(false)}
    },query?350:0)
    return()=>{cancelled=true;window.clearTimeout(timer)}
  },[query,page])

  async function resolveRequest(requestId:string){const token=getToken();const note=resolutionNotes[requestId]?.trim();if(!token||!note)return;setResolvingId(requestId);setError('');try{await createApiClient(token).resolveProfileUpdateRequest(requestId,note);setRequests(current=>current.filter(item=>item.id!==requestId))}catch(value){setError(value instanceof ApiError?value.message:'Không thể hoàn tất yêu cầu.')}finally{setResolvingId('')}}

  async function createProfile(event:React.FormEvent){
    event.preventDefault();const token=getToken();if(!token)return;setSaving(true);setError('')
    try{const created=await createApiClient(token).createPatient({patient_email:form.user_id.trim(),age:Number(form.age),sex:form.sex,height_cm:Number(form.height_cm),weight_kg:Number(form.weight_kg),activity_level:form.activity_level,conditions:form.condition?[{code:form.condition}]:[],lab_values:{},allergies:form.allergies.split(',').map(value=>value.trim()).filter(Boolean),medications:form.medications.split(',').map(value=>value.trim()).filter(Boolean),region:form.region});setPatients(current=>[created,...current]);setCreateOpen(false);setForm(EMPTY)}catch(value){setError(value instanceof ApiError?value.message:'Không thể tạo hồ sơ.')}finally{setSaving(false)}
  }

  return <div data-page="dietitian-patients" className="min-h-screen px-[28px] pt-[20px] pb-10 text-[var(--c-ink)] max-[850px]:px-[15px] max-[850px]:pt-[58px] max-[850px]:pb-[30px]">
    <header className="flex items-start justify-between gap-5 max-[850px]:grid">
      <div>
        <small className="text-[9px] font-extrabold tracking-[.13em] text-[#0e5f95]">QUẢN LÝ HỒ SƠ</small>
        <h1 className="mt-1 font-[family-name:var(--f-serif)] text-[20px] font-semibold tracking-[-.01em]">Hồ sơ bệnh nhân</h1>
        <p className="mt-1 max-w-[700px] text-[9.5px] leading-[1.5] text-[var(--c-muted)]">Tiếp nhận và cập nhật thông tin sức khỏe của bệnh nhân. Chọn một hồ sơ để xem chi tiết hoặc bắt đầu tạo thực đơn.</p>
      </div>
      <button type="button" className="flex min-h-[38px] items-center gap-2 rounded-[10px] bg-[linear-gradient(100deg,var(--c-green),#79a1bc)] px-3 text-[10px] font-bold text-white" onClick={()=>setCreateOpen(true)}><Icon name="plus" className="w-4"/>Thêm hồ sơ bệnh nhân</button>
    </header>
    {error&&<div className="mt-2.5 flex items-center gap-2 rounded-xl border border-[#efb4a4] bg-[#fff5f1] p-2.5 text-[9px] text-[#8b3d2b]"><Icon name="warning" className="w-4"/>{error}</div>}
    {requests.length>0&&<section className="mt-3 rounded-xl border border-[#9b7938] bg-[var(--c-card)] px-3.5 py-3 shadow-[var(--shadow-sm)]">
      <header className="flex items-start justify-between gap-3">
        <div><small className="block text-[9px] font-extrabold tracking-[.1em] text-[#9a6517]">YÊU CẦU TỪ NGƯỜI BỆNH</small><h2 className="mt-0.5 font-[family-name:var(--f-serif)] text-[13.5px] font-semibold">Cần xác minh thông tin hồ sơ</h2></div>
        <span className="flex-none rounded-full bg-[#fff0cf] px-2.5 py-1 text-[9.5px] font-bold text-[#8a5a13]">{requests.length} đang chờ</span>
      </header>
      {requests.map(item=><article key={item.id} className="mt-2.5 grid gap-1.5 border-t border-[#f0dcae] pt-2.5">
        <div><strong className="text-[11px]">Mã hồ sơ {item.profile_id.slice(0,8).toUpperCase()} · {item.patient.sex==='male'?'Nam':'Nữ'}, {item.patient.age} tuổi</strong><p className="mt-1 text-[10.5px] leading-[1.5] text-[#5c676e]">{item.message}</p><small className="mt-1 block text-[9px] text-[#8a9494]">Gửi {new Date(item.created_at).toLocaleString('vi-VN')}</small></div>
        <Link className="w-fit text-[9.5px] font-bold text-[var(--c-green2)]" href={`/dietitian/patients/${item.profile_id}`}>Mở hồ sơ</Link>
        <textarea className="resize-y rounded-[9px] border border-[var(--c-border)] bg-[var(--c-surface)] px-3 py-2.5 font-[inherit] text-[10.5px] outline-none" value={resolutionNotes[item.id]||''} onChange={event=>setResolutionNotes(current=>({...current,[item.id]:event.target.value}))} placeholder="Ghi kết quả xác minh và nội dung đã cập nhật" rows={2}/>
        <button type="button" className="w-fit min-h-[32px] rounded-lg bg-[var(--c-green)] px-3 text-[9.5px] font-bold text-white disabled:cursor-not-allowed disabled:opacity-50" disabled={!resolutionNotes[item.id]?.trim()||resolvingId===item.id} onClick={()=>void resolveRequest(item.id)}>{resolvingId===item.id?'Đang lưu…':'Hoàn tất yêu cầu'}</button>
      </article>)}
    </section>}
    <div className="mt-3.5 mb-2.5 flex items-center justify-between gap-3.5 max-[560px]:flex-col max-[560px]:items-stretch">
      <label className="flex h-[38px] w-[min(530px,100%)] items-center gap-2 rounded-xl border border-[var(--c-border)] bg-[var(--c-card)] px-3"><Icon name="search" className="w-4 text-[var(--c-muted)]"/><input className="min-w-0 flex-1 border-0 bg-transparent text-[10.5px] outline-none" value={query} onChange={event=>{setLoading(true);setPage(1);setQuery(event.target.value)}} placeholder="Tìm mã hồ sơ, email, bệnh lý hoặc thuốc…"/></label>
      <span className="flex-none rounded-full bg-[#e4f0f4] px-2.5 py-1.5 text-[9px] font-bold text-[var(--c-green2)] max-[560px]:w-fit">{total} hồ sơ</span>
    </div>
    {loading?<div className="grid gap-2">{[0,1,2,3].map(i=><i key={i} className="block h-[76px] animate-[skeleton-pulse_1.3s_infinite] rounded-xl bg-[linear-gradient(90deg,#e7eeef_25%,#f6f9f9_50%,#e7eeef_75%)] bg-[length:200%_100%]"/>)}</div>
      :patients.length?<div className="grid gap-2">{patients.map(patient=><PatientRow key={patient.id} patient={patient}/>)}</div>
      :<div className="grid min-h-[240px] content-center place-items-center rounded-xl border border-[var(--c-border)] bg-[var(--c-card)] text-center">
        <Icon name="user" className="w-9 rounded-xl bg-[#e4f0f4] p-2 text-[var(--c-green2)]"/>
        <h2 className="mt-2.5 font-[family-name:var(--f-serif)] text-[15px] font-semibold">{query?'Không tìm thấy hồ sơ phù hợp':'Chưa có hồ sơ bệnh nhân'}</h2>
        <p className="mt-1.5 text-[9px] text-[var(--c-muted)]">{query?'Thử từ khóa khác hoặc tìm bằng mã hồ sơ.':'Thêm hồ sơ sau khi đã có email tài khoản của người bệnh.'}</p>
        {!query&&<button type="button" className="mt-3 rounded-lg bg-[var(--c-green)] px-3 py-2 text-[9px] font-bold text-white" onClick={()=>setCreateOpen(true)}>Thêm hồ sơ đầu tiên</button>}
      </div>}
    {total>20&&<nav className="patient-pagination" aria-label="Phân trang hồ sơ"><button type="button" disabled={page===1||loading} onClick={()=>{setLoading(true);setPage(value=>value-1)}}>Trang trước</button><span>Trang {page} / {Math.ceil(total/20)}</span><button type="button" disabled={page>=Math.ceil(total/20)||loading} onClick={()=>{setLoading(true);setPage(value=>value+1)}}>Trang sau</button></nav>}
    {createOpen&&<div className="fixed inset-0 z-[80]" role="dialog" aria-modal="true" aria-label="Thêm hồ sơ bệnh nhân">
      <button className="absolute inset-0 h-full w-full bg-[rgba(13,47,48,.5)] backdrop-blur-[3px]" type="button" onClick={()=>!saving&&setCreateOpen(false)} aria-label="Đóng"/>
      <form className="absolute top-1/2 left-1/2 max-h-[calc(100vh-30px)] w-[min(720px,calc(100vw-30px))] -translate-x-1/2 -translate-y-1/2 overflow-auto rounded-[19px] bg-[var(--c-card)] p-[22px] shadow-[0_28px_80px_rgba(10,52,53,.27)]" onSubmit={createProfile}>
        <header className="flex justify-between gap-3">
          <div><small className="text-[9px] font-extrabold tracking-[.13em] text-[#0e5f95]">HỒ SƠ MỚI</small><h2 className="mt-1 font-[family-name:var(--f-serif)] text-[19px] font-semibold">Tiếp nhận thông tin bệnh nhân</h2><p className="mt-1 text-[9px] text-[#667178]">Cần tạo tài khoản role patient trước; hồ sơ được liên kết bằng user_id.</p></div>
          <button type="button" className="grid h-[34px] w-[34px] place-items-center rounded-lg bg-[#eaf2f3]" onClick={()=>setCreateOpen(false)} aria-label="Đóng"><Icon name="close" className="w-[17px]"/></button>
        </header>
        <div className="mt-[18px] grid grid-cols-2 gap-[11px] max-[560px]:grid-cols-1">
          <Field label="User ID tài khoản"><input value={form.user_id} onChange={event=>setForm({...form,user_id:event.target.value})} required/></Field>
          <Field label="Tuổi"><input type="number" min="1" max="120" value={form.age} onChange={event=>setForm({...form,age:event.target.value})} required/></Field>
          <Field label="Giới tính"><select value={form.sex} onChange={event=>setForm({...form,sex:event.target.value as FormState['sex']})}><option value="male">Nam</option><option value="female">Nữ</option></select></Field>
          <Field label="Chiều cao (cm)"><input type="number" min="80" max="250" value={form.height_cm} onChange={event=>setForm({...form,height_cm:event.target.value})} required/></Field>
          <Field label="Cân nặng (kg)"><input type="number" min="20" max="300" value={form.weight_kg} onChange={event=>setForm({...form,weight_kg:event.target.value})} required/></Field>
          <Field label="Mức vận động"><select value={form.activity_level} onChange={event=>setForm({...form,activity_level:event.target.value as FormState['activity_level']})}>{Object.entries(ACTIVITY).map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></Field>
          <Field label="Bệnh lý chính"><select value={form.condition} onChange={event=>setForm({...form,condition:event.target.value})}>{Object.entries(CONDITION).map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></Field>
          <Field label="Khẩu vị vùng"><select value={form.region||''} onChange={event=>setForm({...form,region:(event.target.value||null) as FormState['region']})}><option value="">Chưa xác định</option>{Object.entries(REGION).map(([value,label])=><option key={value} value={value}>Miền {label}</option>)}</select></Field>
          <Field label="Thuốc (phân cách bằng dấu phẩy)" wide><input value={form.medications} onChange={event=>setForm({...form,medications:event.target.value})} placeholder="metformin, amlodipine"/></Field>
          <Field label="Dị ứng (phân cách bằng dấu phẩy)" wide><input value={form.allergies} onChange={event=>setForm({...form,allergies:event.target.value})}/></Field>
        </div>
        <footer className="sticky bottom-[-22px] mx-[-22px] mt-5 mb-[-22px] flex justify-end gap-2 border-t border-[var(--c-border)] bg-[var(--c-card)] px-[22px] py-3.5">
          <button type="button" className="flex min-h-10 items-center gap-[7px] rounded-lg border border-[#cbd5d8] px-3.5 text-[9px] font-bold" onClick={()=>setCreateOpen(false)}>Hủy</button>
          <button type="submit" className="flex min-h-10 items-center gap-[7px] rounded-lg border border-transparent bg-[var(--c-green)] px-3.5 text-[9px] font-bold text-white" disabled={saving}>{saving?'Đang tạo hồ sơ…':'Tạo hồ sơ'}<Icon name="arrowRight" className="w-[15px]"/></button>
        </footer>
      </form>
    </div>}
  </div>
}

function PatientRow({patient}:{patient:PatientProfile}){
  const bmi=patient.weight_kg/(patient.height_cm/100)**2
  return <article className="grid grid-cols-[40px_minmax(0,1fr)_auto] items-center gap-3 rounded-xl border border-[var(--c-border)] bg-[var(--c-card)] px-3.5 py-2.5 shadow-[var(--shadow-sm)] transition-colors duration-150 hover:border-[var(--c-green3)] min-h-[64px] max-[850px]:grid-cols-[40px_minmax(0,1fr)] max-[560px]:min-h-0 max-[560px]:grid-cols-[40px_minmax(0,1fr)] max-[560px]:items-start max-[560px]:gap-3 max-[560px]:p-3">
    <PatientAvatar sex={patient.sex} size="sm"/>
    <div className="min-w-0">
      <div className="flex flex-wrap items-center gap-1.5">
        <span className="inline-flex items-baseline gap-[5px] text-[var(--c-muted)]" title={`ID đầy đủ: ${patient.id}`}><span className="text-[8.5px] font-bold">Mã hồ sơ</span><code className="text-[9.5px] font-bold text-[var(--c-ink)]">{patient.id.slice(0,8).toUpperCase()}</code></span>
        {patient.conditions.map(item=><span className="rounded-full border border-[#eed494] bg-[#fff6df] px-[7px] py-[3px] text-[8.5px] font-bold text-[#8b601a]" key={`${item.code}-${item.stage}`}>{CONDITION[item.code]||item.code}{item.stage?` ${item.stage}`:''}</span>)}
        {patient.allergies.length>0&&<b className="inline-flex items-center gap-1 rounded-full border border-[#efb8af] bg-[#ffefec] px-[7px] py-[3px] text-[8.5px] font-bold text-[#984738]"><Icon name="warning" className="w-[11px]"/>Có dị ứng</b>}
      </div>
      <p className="mt-[7px] flex flex-wrap items-center gap-[7px] text-[10px] text-[var(--c-ink2)] max-[560px]:mt-2 max-[560px]:gap-1.5 max-[560px]:text-[10px] max-[560px]:leading-relaxed">
        <span className="max-[560px]:border-r max-[560px]:border-[#d8e2e4] max-[560px]:pr-[7px]">{patient.sex==='male'?'Nam':'Nữ'} · {patient.age} tuổi</span>
        <i className="h-[3px] w-[3px] rounded-full bg-[var(--c-green)] max-[560px]:hidden"/>
        <span className="max-[560px]:border-r max-[560px]:border-[#d8e2e4] max-[560px]:pr-[7px]">{patient.height_cm} cm · {patient.weight_kg} kg</span>
        <i className="h-[3px] w-[3px] rounded-full bg-[var(--c-green)] max-[560px]:hidden"/>
        <span className="max-[560px]:border-r max-[560px]:border-[#d8e2e4] max-[560px]:pr-[7px]">BMI {bmi.toFixed(1)}</span>
        <i className="h-[3px] w-[3px] rounded-full bg-[var(--c-green)] max-[560px]:hidden"/>
        <span className="max-[560px]:border-r max-[560px]:border-[#d8e2e4] max-[560px]:pr-[7px]">Vận động {ACTIVITY[patient.activity_level]||patient.activity_level}</span>
        {patient.region&&<><i className="h-[3px] w-[3px] rounded-full bg-[var(--c-green)] max-[560px]:hidden"/><span className="max-[560px]:border-r max-[560px]:border-[#d8e2e4] max-[560px]:pr-[7px]">Miền {REGION[patient.region]}</span></>}
      </p>
      <small className="mt-1.5 block text-[9px] text-[var(--c-muted)]">{patient.medications.length?`Thuốc đang ghi nhận: ${patient.medications.join(', ')}`:'Chưa ghi nhận thuốc đang dùng'}</small>
    </div>
    <div className="flex gap-[7px] max-[850px]:col-span-2 max-[560px]:grid max-[560px]:grid-cols-2">
      <Link className="flex min-h-[30px] items-center justify-center gap-[5px] whitespace-nowrap rounded-lg border border-[var(--c-border2)] bg-[var(--c-surface)] px-[11px] text-[9.5px] font-bold max-[850px]:flex-1 max-[560px]:min-w-0 max-[560px]:whitespace-normal max-[560px]:px-2 max-[560px]:text-[9px]" href={`/dietitian/patients/${patient.id}`}>Xem hồ sơ</Link>
      <Link className="flex min-h-[30px] items-center justify-center gap-[5px] whitespace-nowrap rounded-lg border border-[#166092] bg-[#166092] px-[11px] text-[9.5px] font-bold text-white max-[850px]:flex-1 max-[560px]:min-w-0 max-[560px]:whitespace-normal max-[560px]:px-2 max-[560px]:text-[9px]" href={`/dietitian/meal-plans/new?profile_id=${patient.id}`}>Tạo thực đơn<Icon name="arrowRight" className="w-[13px]"/></Link>
    </div>
  </article>
}

function Field({label,wide,children}:{label:string;wide?:boolean;children:React.ReactNode}){
  const displayLabel=label==='User ID tài khoản'?'Email tài khoản bệnh nhân':label
  const inputStyle="[&_input]:h-[42px] [&_input]:rounded-lg [&_input]:border [&_input]:border-[var(--c-border)] [&_input]:bg-[var(--c-surface)] [&_input]:px-[11px] [&_input]:text-[10px] [&_input]:outline-none [&_select]:h-[42px] [&_select]:rounded-lg [&_select]:border [&_select]:border-[var(--c-border)] [&_select]:bg-[var(--c-surface)] [&_select]:px-[11px] [&_select]:text-[10px] [&_select]:outline-none"
  return <label className={`grid gap-1.5 ${inputStyle} ${wide?'col-span-full max-[560px]:col-auto':''}`}><span className="text-[9px] font-bold">{displayLabel}</span>{children}</label>
}
