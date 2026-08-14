'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'
import { Icon } from '@/components/brand-artwork'
import { ApiError, createApiClient, type PatientProfile } from '@/lib/api'
import { getToken } from '@/lib/auth'
import styles from './patients.module.css'

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
  const [createOpen,setCreateOpen]=useState(false)
  const [form,setForm]=useState<FormState>(EMPTY)
  const [saving,setSaving]=useState(false)

  useEffect(()=>{
    const token=getToken();if(!token)return
    let cancelled=false
    async function loadPatients(){
      try{const result=await createApiClient(token!).listPatients(1,100);if(!cancelled)setPatients(result.items)}
      catch(value){if(!cancelled)setError(value instanceof ApiError?value.message:'Không thể tải hồ sơ.')}
      finally{if(!cancelled)setLoading(false)}
    }
    void loadPatients()
    return()=>{cancelled=true}
  },[])
  const filtered=useMemo(()=>patients.filter(patient=>`${patient.id} ${patient.conditions.map(item=>item.code).join(' ')} ${patient.medications.join(' ')}`.toLowerCase().includes(query.trim().toLowerCase())),[patients,query])

  async function createProfile(event:React.FormEvent){
    event.preventDefault();const token=getToken();if(!token)return;setSaving(true);setError('')
    try{const created=await createApiClient(token).createPatient({user_id:form.user_id.trim(),age:Number(form.age),sex:form.sex,height_cm:Number(form.height_cm),weight_kg:Number(form.weight_kg),activity_level:form.activity_level,conditions:form.condition?[{code:form.condition}]:[],lab_values:{},allergies:form.allergies.split(',').map(value=>value.trim()).filter(Boolean),medications:form.medications.split(',').map(value=>value.trim()).filter(Boolean),region:form.region});setPatients(current=>[created,...current]);setCreateOpen(false);setForm(EMPTY)}catch(value){setError(value instanceof ApiError?value.message:'Không thể tạo hồ sơ.')}finally{setSaving(false)}
  }

  return <div className={styles.page}>
    <header className={styles.header}><div><small>PATIENT INTELLIGENCE</small><h1>Hồ sơ bệnh nhân</h1><p>Trang này chỉ tiếp nhận và quản lý dữ liệu bệnh nhân. Tạo thực đơn là một workflow riêng bắt đầu từ hồ sơ đã chọn.</p></div><button type="button" onClick={()=>setCreateOpen(true)}><Icon name="plus"/>Thêm hồ sơ bệnh nhân</button></header>
    {error&&<div className={styles.error}><Icon name="warning"/>{error}</div>}
    <div className={styles.toolbar}><label><Icon name="search"/><input value={query} onChange={event=>setQuery(event.target.value)} placeholder="Tìm mã hồ sơ, bệnh lý hoặc thuốc…"/></label><span>{filtered.length} hồ sơ</span></div>
    {loading?<div className={styles.skeleton}><i/><i/><i/><i/></div>:filtered.length?<div className={styles.list}>{filtered.map(patient=><PatientRow key={patient.id} patient={patient}/>)}</div>:<div className={styles.empty}><Icon name="user"/><h2>{query?'Không tìm thấy hồ sơ phù hợp':'Chưa có hồ sơ bệnh nhân'}</h2><p>{query?'Thử từ khóa khác hoặc tìm bằng mã hồ sơ.':'Thêm hồ sơ khi đã có user_id của tài khoản người bệnh.'}</p>{!query&&<button type="button" onClick={()=>setCreateOpen(true)}>Thêm hồ sơ đầu tiên</button>}</div>}
    {createOpen&&<div className={styles.modalLayer} role="dialog" aria-modal="true" aria-label="Thêm hồ sơ bệnh nhân"><button className={styles.scrim} type="button" onClick={()=>!saving&&setCreateOpen(false)} aria-label="Đóng"/><form className={styles.modal} onSubmit={createProfile}><header><div><small>HỒ SƠ MỚI</small><h2>Tiếp nhận thông tin bệnh nhân</h2><p>Cần tạo tài khoản role patient trước; hồ sơ được liên kết bằng user_id.</p></div><button type="button" onClick={()=>setCreateOpen(false)} aria-label="Đóng"><Icon name="close"/></button></header><div className={styles.formGrid}><Field label="User ID tài khoản"><input value={form.user_id} onChange={event=>setForm({...form,user_id:event.target.value})} required/></Field><Field label="Tuổi"><input type="number" min="1" max="120" value={form.age} onChange={event=>setForm({...form,age:event.target.value})} required/></Field><Field label="Giới tính"><select value={form.sex} onChange={event=>setForm({...form,sex:event.target.value as FormState['sex']})}><option value="male">Nam</option><option value="female">Nữ</option></select></Field><Field label="Chiều cao (cm)"><input type="number" min="80" max="250" value={form.height_cm} onChange={event=>setForm({...form,height_cm:event.target.value})} required/></Field><Field label="Cân nặng (kg)"><input type="number" min="20" max="300" value={form.weight_kg} onChange={event=>setForm({...form,weight_kg:event.target.value})} required/></Field><Field label="Mức vận động"><select value={form.activity_level} onChange={event=>setForm({...form,activity_level:event.target.value as FormState['activity_level']})}>{Object.entries(ACTIVITY).map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></Field><Field label="Bệnh lý chính"><select value={form.condition} onChange={event=>setForm({...form,condition:event.target.value})}>{Object.entries(CONDITION).map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></Field><Field label="Khẩu vị vùng"><select value={form.region||''} onChange={event=>setForm({...form,region:(event.target.value||null) as FormState['region']})}><option value="">Chưa xác định</option>{Object.entries(REGION).map(([value,label])=><option key={value} value={value}>Miền {label}</option>)}</select></Field><Field label="Thuốc (phân cách bằng dấu phẩy)" wide><input value={form.medications} onChange={event=>setForm({...form,medications:event.target.value})} placeholder="metformin, amlodipine"/></Field><Field label="Dị ứng (phân cách bằng dấu phẩy)" wide><input value={form.allergies} onChange={event=>setForm({...form,allergies:event.target.value})}/></Field></div><footer><button type="button" onClick={()=>setCreateOpen(false)}>Hủy</button><button type="submit" disabled={saving}>{saving?'Đang tạo hồ sơ…':'Tạo hồ sơ'}<Icon name="arrowRight"/></button></footer></form></div>}
  </div>
}

function PatientRow({patient}:{patient:PatientProfile}){const bmi=patient.weight_kg/(patient.height_cm/100)**2;return <article className={styles.row}><span className={styles.avatar}>{patient.sex==='male'?'N':'Nữ'}</span><div className={styles.identity}><div><code>#{patient.id.slice(0,8)}</code>{patient.conditions.map(item=><span key={`${item.code}-${item.stage}`}>{CONDITION[item.code]||item.code}{item.stage?` ${item.stage}`:''}</span>)}{patient.allergies.length>0&&<b><Icon name="warning"/>Dị ứng</b>}</div><p>{patient.sex==='male'?'Nam':'Nữ'} · {patient.age} tuổi <i/> {patient.height_cm} cm · {patient.weight_kg} kg <i/> BMI {bmi.toFixed(1)} <i/> Hoạt động {ACTIVITY[patient.activity_level]||patient.activity_level}{patient.region&&<><i/> Miền {REGION[patient.region]}</>}</p><small>{patient.medications.length?`Thuốc: ${patient.medications.join(', ')}`:'Chưa ghi nhận thuốc'}</small></div><div className={styles.actions}><Link href={`/dietitian/patients/${patient.id}`}>Xem hồ sơ</Link><Link href={`/dietitian/meal-plans/new?profile_id=${patient.id}`}>Tạo phương án<Icon name="arrowRight"/></Link></div></article>}

function Field({label,wide,children}:{label:string;wide?:boolean;children:React.ReactNode}){return <label className={wide?styles.wide:undefined}><span>{label}</span>{children}</label>}
