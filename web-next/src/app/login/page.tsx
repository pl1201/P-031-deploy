'use client'

import { useRouter } from 'next/navigation'
import { useCallback, useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { Icon, LeafMark, RiceBotanical } from '@/components/brand-artwork'
import { ApiError, createApiClient, type Role } from '@/lib/api'
import { redirectByRole, saveSession } from '@/lib/auth'
import styles from './login-v2.module.css'

type LoginRole = 'patient' | 'dietitian'
const DEMO:Record<LoginRole,{email:string;password:string}>={patient:{email:'patient1@nutricare.demo',password:'Demo1234'},dietitian:{email:'dietitian1@nutricare.demo',password:'Demo1234'}}

function safeReturnTo(role:Role){
  const target=new URLSearchParams(window.location.search).get('returnTo')
  if(!target)return redirectByRole(role)
  if(role==='patient'&&target.startsWith('/patient'))return target
  if((role==='dietitian'||role==='admin')&&target.startsWith('/dietitian'))return target
  return redirectByRole(role)
}

export default function LoginPage(){
  const router=useRouter()
  const [role,setRole]=useState<LoginRole>('patient')
  const [email,setEmail]=useState('')
  const [password,setPassword]=useState('')
  const [showPassword,setShowPassword]=useState(false)
  const [loading,setLoading]=useState(false)
  const [waking,setWaking]=useState(false)
  const [error,setError]=useState('')
  const [message,setMessage]=useState('')
  const wakingTimer=useRef<ReturnType<typeof setTimeout>|null>(null)
  const autoStarted=useRef(false)

  const authenticate=useCallback(async(loginEmail:string,loginPassword:string)=>{
    setLoading(true);setWaking(false);setError('');setMessage('')
    wakingTimer.current=setTimeout(()=>setWaking(true),8000)
    try{
      const session=await createApiClient().login(loginEmail,loginPassword)
      saveSession(session)
      router.push(safeReturnTo(session.role))
    }catch(value){setError(value instanceof ApiError?value.message:'Không thể đăng nhập. Vui lòng thử lại.')}
    finally{if(wakingTimer.current)clearTimeout(wakingTimer.current);wakingTimer.current=null;setWaking(false);setLoading(false)}
  },[router])

  useEffect(()=>{
    if(autoStarted.current)return
    const demo=new URLSearchParams(window.location.search).get('demo')
    if(demo==='patient'||demo==='dietitian'){
      autoStarted.current=true
      const account=DEMO[demo]
      const timer=window.setTimeout(()=>void authenticate(account.email,account.password),0)
      return()=>window.clearTimeout(timer)
    }
    return()=>{if(wakingTimer.current)clearTimeout(wakingTimer.current)}
  },[authenticate])

  const submit=(event:React.FormEvent)=>{event.preventDefault();void authenticate(email,password)}
  const openDemo=(nextRole:LoginRole)=>{setRole(nextRole);const account=DEMO[nextRole];void authenticate(account.email,account.password)}

  return <main className={styles.page} data-page="login">
    <section className={styles.formSide}><RiceBotanical className={styles.rice}/><div className={styles.logo}><LeafMark/><strong>VNUTRICARE</strong></div><div className={styles.formWrap}><div className={styles.roles}><button type="button" className={role==='patient'?styles.active:''} onClick={()=>setRole('patient')}><Icon name="user"/>Người bệnh</button><button type="button" className={role==='dietitian'?styles.active:''} onClick={()=>setRole('dietitian')}><Icon name="expert"/>Chuyên gia</button></div><form onSubmit={submit}><label>Email<div><Icon name="mail"/><input type="email" value={email} onChange={event=>setEmail(event.target.value)} placeholder="ten@vidu.vn" autoComplete="email" required/></div></label><label>Mật khẩu<div><Icon name="lock"/><input type={showPassword?'text':'password'} value={password} onChange={event=>setPassword(event.target.value)} autoComplete="current-password" required/><button type="button" className={styles.eye} onClick={()=>setShowPassword(value=>!value)} aria-label={showPassword?'Ẩn mật khẩu':'Hiện mật khẩu'}><Icon name="eye"/></button></div></label><div className={styles.options}><span>Phiên đăng nhập được bảo vệ trên trình duyệt này.</span><button type="button" onClick={()=>setMessage('Vui lòng liên hệ quản trị viên của đơn vị để đặt lại mật khẩu.')}>Quên mật khẩu?</button></div>{waking&&<p className={styles.waking} role="status">Hệ thống đang khởi động vì chưa có ai dùng gần đây. Lần đầu có thể mất 30–60 giây, bạn cứ chờ, không cần bấm đăng nhập lại.</p>}{error&&<p className={styles.error} role="alert">{error}</p>}{message&&<p className={styles.waking} role="status">{message}</p>}<button className={styles.submit} disabled={loading}>{loading?(waking?'Đang khởi động, vui lòng chờ…':'Đang đăng nhập…'):'Đăng nhập'}</button></form><div className={styles.or}>hoặc trải nghiệm ngay</div><div className={styles.demoGrid}><button type="button" className={styles.demo} disabled={loading} onClick={()=>openDemo('patient')}><Icon name="user"/><span><strong>Demo người bệnh</strong><small>Xem thực đơn và ghi bữa</small></span></button><button type="button" className={styles.demo} disabled={loading} onClick={()=>openDemo('dietitian')}><Icon name="expert"/><span><strong>Demo chuyên gia</strong><small>Tạo, kiểm tra và duyệt</small></span></button></div><p className={styles.support}><Icon name="headset"/>Bạn cần hỗ trợ? <b>Liên hệ đội ngũ VNutriCare</b></p><p className={styles.support}><Link href="/about" style={{textDecoration:'underline'}}>Giới thiệu ứng dụng</Link>{' · '}<Link href="/terms" style={{textDecoration:'underline'}}>Điều khoản sử dụng</Link></p></div></section>
    <section className={styles.carePanel} aria-label="Không gian chăm sóc dinh dưỡng của VNUTRICARE"><div className={styles.careCard}><span className={styles.careStamp} title="Chuyên gia đã duyệt"><Icon name="check"/></span><div className={styles.careCardHead}><span><Icon name="bowl"/></span><div><small>THỰC ĐƠN ĐÃ DUYỆT</small><strong>Cá kho tộ · rau lang · cơm gạo lứt</strong></div></div><div className={styles.careCardKcal}><strong>420<i>kcal</i></strong></div><div className={styles.careCardStats}><div><small>Đạm</small><b>24 g</b></div><div><small>Natri</small><b>480 mg</b></div><div><small>Chất xơ</small><b>6 g</b></div></div><div className={styles.careCardSource}><Icon name="database"/>Nguồn: NIN · USDA FoodData</div></div><div className={styles.carePath}><article title="Hiểu hồ sơ và thói quen"><span><Icon name="profile"/><i>01</i></span><strong>Hiểu hồ sơ</strong><p className="sr-only">Khẩu vị, thuốc và mục tiêu được xem xét cùng nhau.</p></article><article title="Thực đơn Việt dễ làm theo"><span><Icon name="bowl"/><i>02</i></span><strong>Thực đơn dễ làm</strong><p className="sr-only">Khẩu phần rõ ràng, phù hợp với nhịp sống thực tế.</p></article><article title="Nhìn lại và điều chỉnh"><span><Icon name="followup"/><i>03</i></span><strong>Theo dõi, điều chỉnh</strong><p className="sr-only">Chuyên gia theo dõi tiến trình và hỗ trợ đúng lúc.</p></article></div></section>
  </main>
}
