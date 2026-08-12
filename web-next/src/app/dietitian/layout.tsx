'use client'

import { useEffect, useState } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import Link from 'next/link'
import { createApiClient } from '@/lib/api'
import { clearSession, getSession, getToken } from '@/lib/auth'
import { LeafMark } from '@/components/brand-artwork'

type IconName='overview'|'patient'|'calendar'|'sparkles'|'database'|'shield'|'account'|'logout'|'menu'
function Icon({name}:{name:IconName}){
  const paths:Record<IconName,React.ReactNode>={
    overview:<><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></>,
    patient:<><circle cx="12" cy="7" r="4"/><path d="M5 21v-2a7 7 0 0 1 14 0v2"/></>,
    calendar:<><rect x="4" y="5" width="16" height="16" rx="2"/><path d="M8 3v4M16 3v4M4 10h16M8 14h3M8 17h6"/></>,
    sparkles:<><path d="m12 3 1.2 3.8L17 8l-3.8 1.2L12 13l-1.2-3.8L7 8l3.8-1.2zM18 14l.7 2.3L21 17l-2.3.7L18 20l-.7-2.3L15 17l2.3-.7z"/></>,
    database:<><ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/></>,
    shield:<><path d="M12 2 4 5v6c0 5 3.3 9 8 11 4.7-2 8-6 8-11V5zM9 12l2 2 4-5"/></>,
    account:<><circle cx="12" cy="8" r="4"/><path d="M4 22a8 8 0 0 1 16 0"/></>,
    logout:<><path d="M10 5H4v14h6M14 8l4 4-4 4M8 12h10"/></>,
    menu:<><path d="M4 7h16M4 12h16M4 17h16"/></>,
  }
  return <svg className="ui-icon" viewBox="0 0 24 24" aria-hidden="true">{paths[name]}</svg>
}

const NAV=[
  {href:'/dietitian',label:'Tổng quan',icon:'overview' as IconName,exact:true},
  {href:'/dietitian/patients',label:'Bệnh nhân',icon:'patient' as IconName},
  {href:'/dietitian/reviews',label:'Chờ duyệt',icon:'calendar' as IconName,badge:true},
  {href:'/dietitian/meal-plans/new',label:'Tạo thực đơn',icon:'sparkles' as IconName,nested:true},
  {href:'/dietitian/food-logs',label:'Nhật ký ăn uống',icon:'calendar' as IconName},
  {href:'',label:'Nguồn dữ liệu',icon:'database' as IconName,disabled:true},
  {href:'/eval',label:'Đánh giá hệ thống',icon:'shield' as IconName},
  {href:'',label:'Tài khoản',icon:'account' as IconName,disabled:true},
]

export default function DietitianLayout({children}:{children:React.ReactNode}){
  const router=useRouter();const pathname=usePathname();const [pending,setPending]=useState<number|null>(null);const [open,setOpen]=useState(false)
  useEffect(()=>{const session=getSession();if(!session||(session.role!=='dietitian'&&session.role!=='admin')){router.replace('/login');return}const token=getToken();if(token)void createApiClient(token).listPendingReviews().then(rows=>setPending(rows.length)).catch(()=>setPending(null))},[router])
  const logout=()=>{clearSession();router.push('/login')}
  return <div className="app-shell clinical-shell">
    <aside className={`sidebar clinical-sidebar${open?' open':''}`}>
      <div className="sidebar-brand"><LeafMark/><div><div className="brand-name">VNUTRICARE</div></div><button className="sidebar-close" onClick={()=>setOpen(false)} aria-label="Đóng menu">×</button></div>
      <nav className="sidebar-nav">{NAV.map(item=>{const active=item.exact?pathname===item.href:Boolean(item.href&&pathname.startsWith(item.href));const body=<><span className="nav-icon"><Icon name={item.icon}/></span><span>{item.label}</span>{item.badge&&pending!==null&&<span className="nav-badge">{pending}</span>}</>;return item.disabled?<span key={item.label} className="nav-item nav-disabled" aria-disabled="true" title="Chưa có chức năng backend">{body}</span>:<Link key={item.label} href={item.href} className={`nav-item${active?' active':''}${item.nested?' nav-nested':''}`} onClick={()=>setOpen(false)}>{body}</Link>})}</nav>
      <div className="sidebar-footer"><div className="user-avatar">CG</div><div className="user-copy"><div className="user-name">Tài khoản chuyên gia</div><div className="user-role">Chuyên gia dinh dưỡng</div></div><button className="logout-button" onClick={logout} title="Đăng xuất" aria-label="Đăng xuất"><Icon name="logout"/></button></div>
    </aside>
    <main className="main-content"><button className="mobile-menu-btn" aria-label="Mở menu" onClick={()=>setOpen(true)}><Icon name="menu"/></button>{children}</main>
    {open&&<button className="mobile-overlay" aria-label="Đóng menu" onClick={()=>setOpen(false)}/>}
  </div>
}
