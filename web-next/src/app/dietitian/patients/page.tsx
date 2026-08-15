'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { Icon } from '@/components/brand-artwork'
import { PatientAvatar } from '@/components/patient-avatar'
import { ApiError, createApiClient, type PatientProfile, type ProfileUpdateRequest } from '@/lib/api'
import { getToken } from '@/lib/auth'
import styles from './patients.module.css'
import rowStyles from './patient-row.module.css'

const CONDITION:Record<string,string>={T2DM:'ĐTĐ type 2',HTN:'Tăng huyết áp',CKD:'Bệnh thận mạn',GOUT:'Gout'}
const ACTIVITY:Record<string,string>={light:'Nhẹ',moderate:'Trung bình',heavy:'Nặng',very_heavy:'Rất nặng'}
const REGION:Record<string,string>={north:'Bắc',central:'Trung',south:'Nam'}

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

  return <div className={styles.page}>
    <header className={styles.header}><div><small>QUẢN LÝ HỒ SƠ</small><h1>Hồ sơ bệnh nhân</h1><p>Tiếp nhận và cập nhật thông tin sức khỏe của bệnh nhân. Chọn một hồ sơ để xem chi tiết hoặc bắt đầu tạo thực đơn.</p></div><button type="button" onClick={()=>setCreateOpen(true)}><Icon name="plus"/>Thêm hồ sơ bệnh nhân</button></header>
    {error&&<div className={styles.error}><Icon name="warning"/>{error}</div>}
    {requests.length>0&&<section className={styles.requestQueue}><header><div><small>YÊU CẦU TỪ NGƯỜI BỆNH</small><h2>Cần xác minh thông tin hồ sơ</h2></div><span>{requests.length} đang chờ</span></header>{requests.map(item=><article key={item.id}><div><strong>Mã hồ sơ {item.profile_id.slice(0,8).toUpperCase()} · {item.patient.sex==='male'?'Nam':'Nữ'}, {item.patient.age} tuổi</strong><p>{item.message}</p><small>Gửi {new Date(item.created_at).toLocaleString('vi-VN')}</small></div><Link href={`/dietitian/patients/${item.profile_id}`}>Mở hồ sơ</Link><textarea value={resolutionNotes[item.id]||''} onChange={event=>setResolutionNotes(current=>({...current,[item.id]:event.target.value}))} placeholder="Ghi kết quả xác minh và nội dung đã cập nhật" rows={2}/><button type="button" disabled={!resolutionNotes[item.id]?.trim()||resolvingId===item.id} onClick={()=>void resolveRequest(item.id)}>{resolvingId===item.id?'Đang lưu…':'Hoàn tất yêu cầu'}</button></article>)}</section>}
    <div className={styles.toolbar}><label><Icon name="search"/><input value={query} onChange={event=>{setLoading(true);setPage(1);setQuery(event.target.value)}} placeholder="Tìm mã hồ sơ, email, bệnh lý hoặc thuốc…"/></label><span>{total} hồ sơ</span></div>
    {loading?<div className={styles.skeleton}><i/><i/><i/><i/></div>:patients.length?<div className={styles.list}>{patients.map(patient=><PatientRow key={patient.id} patient={patient}/>)}</div>:<div className={styles.empty}><Icon name="user"/><h2>{query?'Không tìm thấy hồ sơ phù hợp':'Chưa có hồ sơ bệnh nhân'}</h2><p>{query?'Thử từ khóa khác hoặc tìm bằng mã hồ sơ.':'Thêm hồ sơ sau khi đã có email tài khoản của người bệnh.'}</p>{!query&&<button type="button" onClick={()=>setCreateOpen(true)}>Thêm hồ sơ đầu tiên</button>}</div>}
    {total>20&&<nav className="patient-pagination" aria-label="Phân trang hồ sơ"><button type="button" disabled={page===1||loading} onClick={()=>{setLoading(true);setPage(value=>value-1)}}>Trang trước</button><span>Trang {page} / {Math.ceil(total/20)}</span><button type="button" disabled={page>=Math.ceil(total/20)||loading} onClick={()=>{setLoading(true);setPage(value=>value+1)}}>Trang sau</button></nav>}
    {createOpen&&<div className={styles.modalLayer} role="dialog" aria-modal="true" aria-label="Thêm hồ sơ bệnh nhân"><button className={styles.scrim} type="button" onClick={()=>!saving&&setCreateOpen(false)} aria-label="Đóng"/><form className={styles.modal} onSubmit={createProfile}><header><div><small>HỒ SƠ MỚI</small><h2>Tiếp nhận thông tin bệnh nhân</h2><p>Cần tạo tài khoản role patient trước; hồ sơ được liên kết bằng user_id.</p></div><button type="button" onClick={()=>setCreateOpen(false)} aria-label="Đóng"><Icon name="close"/></button></header><div className={styles.formGrid}><Field label="User ID tài khoản"><input value={form.user_id} onChange={event=>setForm({...form,user_id:event.target.value})} required/></Field><Field label="Tuổi"><input type="number" min="1" max="120" value={form.age} onChange={event=>setForm({...form,age:event.target.value})} required/></Field><Field label="Giới tính"><select value={form.sex} onChange={event=>setForm({...form,sex:event.target.value as FormState['sex']})}><option value="male">Nam</option><option value="female">Nữ</option></select></Field><Field label="Chiều cao (cm)"><input type="number" min="80" max="250" value={form.height_cm} onChange={event=>setForm({...form,height_cm:event.target.value})} required/></Field><Field label="Cân nặng (kg)"><input type="number" min="20" max="300" value={form.weight_kg} onChange={event=>setForm({...form,weight_kg:event.target.value})} required/></Field><Field label="Mức vận động"><select value={form.activity_level} onChange={event=>setForm({...form,activity_level:event.target.value as FormState['activity_level']})}>{Object.entries(ACTIVITY).map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></Field><Field label="Bệnh lý chính"><select value={form.condition} onChange={event=>setForm({...form,condition:event.target.value})}>{Object.entries(CONDITION).map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></Field><Field label="Khẩu vị vùng"><select value={form.region||''} onChange={event=>setForm({...form,region:(event.target.value||null) as FormState['region']})}><option value="">Chưa xác định</option>{Object.entries(REGION).map(([value,label])=><option key={value} value={value}>Miền {label}</option>)}</select></Field><Field label="Thuốc (phân cách bằng dấu phẩy)" wide><input value={form.medications} onChange={event=>setForm({...form,medications:event.target.value})} placeholder="metformin, amlodipine"/></Field><Field label="Dị ứng (phân cách bằng dấu phẩy)" wide><input value={form.allergies} onChange={event=>setForm({...form,allergies:event.target.value})}/></Field></div><footer><button type="button" onClick={()=>setCreateOpen(false)}>Hủy</button><button type="submit" disabled={saving}>{saving?'Đang tạo hồ sơ…':'Tạo hồ sơ'}<Icon name="arrowRight"/></button></footer></form></div>}
  </div>
}

function PatientRow({patient}:{patient:PatientProfile}){const bmi=patient.weight_kg/(patient.height_cm/100)**2;return <article className={rowStyles.row}><PatientAvatar sex={patient.sex}/><div className={rowStyles.identity}><div className={rowStyles.topline}><span className={rowStyles.recordId} title={`ID đầy đủ: ${patient.id}`}><span>Mã hồ sơ</span><code>{patient.id.slice(0,8).toUpperCase()}</code></span>{patient.conditions.map(item=><span className={rowStyles.condition} key={`${item.code}-${item.stage}`}>{CONDITION[item.code]||item.code}{item.stage?` ${item.stage}`:''}</span>)}{patient.allergies.length>0&&<b className={rowStyles.allergy}><Icon name="warning"/>Có dị ứng</b>}</div><p className={rowStyles.facts}><span>{patient.sex==='male'?'Nam':'Nữ'} · {patient.age} tuổi</span><i/><span>{patient.height_cm} cm · {patient.weight_kg} kg</span><i/><span>BMI {bmi.toFixed(1)}</span><i/><span>Vận động {ACTIVITY[patient.activity_level]||patient.activity_level}</span>{patient.region&&<><i/><span>Miền {REGION[patient.region]}</span></>}</p><small className={rowStyles.medication}>{patient.medications.length?`Thuốc đang ghi nhận: ${patient.medications.join(', ')}`:'Chưa ghi nhận thuốc đang dùng'}</small></div><div className={rowStyles.actions}><Link href={`/dietitian/patients/${patient.id}`}>Xem hồ sơ</Link><Link href={`/dietitian/meal-plans/new?profile_id=${patient.id}`}>Tạo thực đơn<Icon name="arrowRight"/></Link></div></article>}

function Field({label,wide,children}:{label:string;wide?:boolean;children:React.ReactNode}){const displayLabel=label==='User ID tài khoản'?'Email tài khoản bệnh nhân':label;return <label className={wide?styles.wide:undefined}><span>{displayLabel}</span>{children}</label>}
