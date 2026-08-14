'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { Icon } from '@/components/brand-artwork'
import { ApiError, createApiClient, type PatientProfile } from '@/lib/api'
import { getToken } from '@/lib/auth'
import styles from '../secondary.module.css'

const activity:Record<string,string>={light:'Nhẹ',moderate:'Trung bình',heavy:'Nặng',very_heavy:'Rất nặng'}
const region:Record<string,string>={north:'Bắc',central:'Trung',south:'Nam'}

export default function PatientProfilePage(){
  const [profile,setProfile]=useState<PatientProfile|null>(null)
  const [error,setError]=useState('')
  const [requestInfo,setRequestInfo]=useState(false)
  useEffect(()=>{const token=getToken();if(!token)return;createApiClient(token).getMyProfile().then(setProfile).catch(value=>setError(value instanceof ApiError?value.message:'Không thể tải hồ sơ.'))},[])
  return <div className={styles.page}>
    <header className={styles.header}><div><small>THÔNG TIN ĐANG ĐƯỢC SỬ DỤNG</small><h1>Hồ sơ của tôi</h1><p>Đây là dữ liệu hệ thống dùng để cá nhân hóa và kiểm tra an toàn. Thay đổi lâm sàng cần được chuyên gia xác nhận.</p></div><div style={{display:'flex',gap:8,flexWrap:'wrap'}}><button type="button" onClick={()=>setRequestInfo(value=>!value)}><Icon name="message"/>Yêu cầu cập nhật</button><Link href="/patient"><Icon name="arrowLeft"/>Về hôm nay</Link></div></header>
    {requestInfo&&<div className={styles.notice}><Icon name="info"/><p>Kênh gửi yêu cầu trực tiếp chưa được backend cung cấp. Hiện tại, hãy liên hệ chuyên gia phụ trách và nêu rõ thông tin cần thay đổi; hồ sơ chỉ được cập nhật sau khi chuyên gia xác nhận.</p></div>}
    {error&&<div className={styles.error}>{error}</div>}
    {!profile?<div className={styles.skeleton}/>:<div className={styles.profileGrid}>
      <main>
        <section className={styles.profileHero}><div className={styles.avatar}>{profile.sex==='male'?'N':'Nữ'}</div><div><h2>Hồ sơ #{profile.id.slice(0,8)}</h2><p>{profile.sex==='male'?'Nam':'Nữ'} · {profile.age} tuổi</p></div><span>Đang theo dõi</span></section>
        <section className={styles.card} style={{marginTop:14}}><div className={styles.cardTitle}><div><small>THÔNG TIN CƠ BẢN</small><h2>Chỉ số và thói quen</h2></div></div><dl className={styles.details}><div><dt>Chiều cao</dt><dd>{profile.height_cm} cm</dd></div><div><dt>Cân nặng</dt><dd>{profile.weight_kg} kg</dd></div><div><dt>BMI</dt><dd>{(profile.weight_kg/((profile.height_cm/100)**2)).toFixed(1)}</dd></div><div><dt>Mức vận động</dt><dd>{activity[profile.activity_level]||profile.activity_level}</dd></div><div><dt>Khẩu vị vùng miền</dt><dd>{profile.region?`Miền ${region[profile.region]}`:'Chưa ghi nhận'}</dd></div><div><dt>Mã hồ sơ</dt><dd>#{profile.id.slice(0,8)}</dd></div></dl></section>
      </main>
      <aside className={styles.card}><div className={styles.cardTitle}><div><small>AN TOÀN LÂM SÀNG</small><h2>Dữ liệu cần đối chiếu</h2></div></div><h3 style={{marginTop:18,fontSize:11}}>Bệnh lý đang ghi nhận</h3><div className={styles.tags}>{profile.conditions.length?profile.conditions.map(item=><span key={`${item.code}-${item.stage}`}>{item.code}{item.stage?` · ${item.stage}`:''}</span>):<span>Chưa ghi nhận</span>}</div><h3 style={{marginTop:18,fontSize:11}}>Thuốc đang dùng</h3><div className={styles.tags}>{profile.medications.length?profile.medications.map(item=><span key={item}>{item}</span>):<span>Chưa ghi nhận</span>}</div><h3 style={{marginTop:18,fontSize:11}}>Dị ứng</h3><div className={styles.tags}>{profile.allergies.length?profile.allergies.map(item=><span key={item}>{item}</span>):<span>Không có dị ứng được ghi nhận</span>}</div><div className={styles.notice}><Icon name="info"/><p>Nếu thuốc, dị ứng, chẩn đoán hoặc chỉ số của bạn đã thay đổi, hãy liên hệ chuyên gia trước khi tiếp tục áp dụng thực đơn hiện tại.</p></div></aside>
    </div>}
  </div>
}
