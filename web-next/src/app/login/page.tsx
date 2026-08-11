'use client'
import Image from 'next/image'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { Icon, LeafMark, RiceBotanical } from '@/components/brand-artwork'
import { ApiError, createApiClient } from '@/lib/api'
import { redirectByRole, saveSession } from '@/lib/auth'
import styles from './login-v2.module.css'

export default function LoginPage(){
  const router=useRouter(); const [role,setRole]=useState<'patient'|'dietitian'>('patient'); const [email,setEmail]=useState(''); const [password,setPassword]=useState(''); const [remember,setRemember]=useState(true); const [loading,setLoading]=useState(false); const [error,setError]=useState('')
  const demo=()=>{setEmail(role==='patient'?'patient1@nutricare.demo':'dietitian1@nutricare.demo');setPassword('Demo1234')}
  const submit=async(event:React.FormEvent)=>{event.preventDefault();setLoading(true);setError('');try{const session=await createApiClient().login(email,password);saveSession(session);router.push(redirectByRole(session.role))}catch(value){setError(value instanceof ApiError?value.message:'Không thể đăng nhập. Vui lòng thử lại.')}finally{setLoading(false)}}
  return <main className={styles.page}>
    <section className={styles.formSide}><RiceBotanical className={styles.rice}/><div className={styles.logo}><LeafMark/><strong>VNUTRICARE</strong></div><div className={styles.formWrap}><small>CHÀO MỪNG BẠN TRỞ LẠI</small><h1>Đăng nhập vào<br/>không gian chăm sóc</h1><p>Tiếp tục với vai trò người bệnh hoặc chuyên gia dinh dưỡng.</p><div className={styles.roles}><button type="button" className={role==='patient'?styles.active:''} onClick={()=>setRole('patient')}><Icon name="user"/>Người bệnh</button><button type="button" className={role==='dietitian'?styles.active:''} onClick={()=>setRole('dietitian')}><Icon name="expert"/>Chuyên gia</button></div><form onSubmit={submit}><label>Email<div><Icon name="mail"/><input type="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder="ten@vidu.vn" required/></div></label><label>Mật khẩu<div><Icon name="lock"/><input type="password" value={password} onChange={e=>setPassword(e.target.value)} required/><Icon name="eye"/></div></label><div className={styles.options}><label><input type="checkbox" checked={remember} onChange={e=>setRemember(e.target.checked)}/> Ghi nhớ đăng nhập</label><button type="button">Quên mật khẩu?</button></div>{error&&<p className={styles.error}>{error}</p>}<button className={styles.submit} disabled={loading}>{loading?'Đang đăng nhập…':'Đăng nhập'}</button></form><div className={styles.or}>hoặc</div><button className={styles.demo} onClick={demo}><Icon name="monitor"/>Xem tài khoản demo</button><p className={styles.support}><Icon name="headset"/>Bạn cần hỗ trợ? <b>Liên hệ đội ngũ VNutriCare</b></p></div></section>
    <section className={styles.photo}><Image src="/images/vnutricare-login-family.png" fill priority sizes="55vw" alt="Gia đình Việt dùng bữa ăn lành mạnh"/><div className={styles.trust}><p><span><Icon name="clipboard"/></span><b>Thực đơn đã duyệt</b></p><p><span><Icon name="document"/></span><b>Dữ liệu có nguồn</b></p><p><span><Icon name="group"/></span><b>Được chuyên gia<br/>đồng hành</b></p></div></section>
  </main>
}
