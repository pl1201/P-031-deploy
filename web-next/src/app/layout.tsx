import type { Metadata, Viewport } from 'next'
import { IBM_Plex_Mono, Plus_Jakarta_Sans } from 'next/font/google'
// Tailwind nạp TRƯỚC globals.css: preflight của Tailwind reset các thẻ HTML trần
// (body, h1..h6, button…) cùng độ đặc hiệu với reset hiện có trong globals.css —
// import trước để globals.css luôn thắng khi trùng thuộc tính, giữ đúng design
// token/typography đã có thay vì bị Tailwind ghi đè.
import './tailwind.css'
import './globals.css'
import { AssistantProvider } from '@/components/experience-tools'

// FE-23: redesign theo MyFitnessPal (2026-08-18) — bỏ Fraunces (serif), dùng
// 1 font sans cho cả tiêu đề lẫn nội dung cho CHUNG cả 2 role (không còn phân
// biệt theo [data-role] như bản trước), xem globals.css.
// 2026-08-19: đổi Manrope -> Plus Jakarta Sans theo yêu cầu tham chiếu "Google
// Sans/Google Sans Text" — 2 font đó độc quyền nội bộ Google, không có trên
// Google Fonts để nhúng hợp lệ; Plus Jakarta Sans là lựa chọn gần hình dáng
// hình học nhất có sẵn công khai.
const plusJakartaSans = Plus_Jakarta_Sans({ subsets: ['latin', 'vietnamese'], weight: ['400', '500', '600', '700', '800'], variable: '--font-plus-jakarta', display: 'swap' })
const plexMono = IBM_Plex_Mono({ subsets: ['latin', 'vietnamese'], weight: ['500', '600'], variable: '--font-plex-mono', display: 'swap' })

export const metadata: Metadata = {
  title: { template: '%s | VNutriCare', default: 'VNutriCare — Tư vấn dinh dưỡng lâm sàng' },
  description: 'AI Agent hỗ trợ chuyên gia lập và duyệt thực đơn dinh dưỡng lâm sàng cho bệnh nhân đái tháo đường type 2.',
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#0072bc',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi" suppressHydrationWarning className={`${plusJakartaSans.variable} ${plexMono.variable}`}>
      <head><script dangerouslySetInnerHTML={{__html:`try{const saved=localStorage.getItem('vnutricare_theme');const theme=saved==='dark'||saved==='light'?saved:(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');document.documentElement.dataset.theme=theme;document.documentElement.style.colorScheme=theme}catch{}`}}/></head>
      <body>
        <AssistantProvider>{children}</AssistantProvider>
        <script dangerouslySetInnerHTML={{__html:`if('serviceWorker' in navigator){window.addEventListener('load',()=>{navigator.serviceWorker.register('/sw.js').catch(()=>{})})}`}}/>
      </body>
    </html>
  )
}
