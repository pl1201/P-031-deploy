import type { Metadata } from 'next'
import './globals.css'
import { ExperienceTools } from '@/components/experience-tools'

export const metadata: Metadata = {
  title: { template: '%s | VNutriCare', default: 'VNutriCare — Tư vấn dinh dưỡng lâm sàng' },
  description: 'AI Agent hỗ trợ chuyên gia lập và duyệt thực đơn dinh dưỡng lâm sàng cho bệnh nhân đái tháo đường type 2.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi" suppressHydrationWarning>
      <head><script dangerouslySetInnerHTML={{__html:`try{const saved=localStorage.getItem('vnutricare_theme');const theme=saved==='dark'||saved==='light'?saved:(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');document.documentElement.dataset.theme=theme;document.documentElement.style.colorScheme=theme}catch{}`}}/></head>
      <body>{children}<ExperienceTools/></body>
    </html>
  )
}
