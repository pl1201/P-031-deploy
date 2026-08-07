import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: { template: '%s | VNutriCare', default: 'VNutriCare — Tư vấn dinh dưỡng lâm sàng' },
  description: 'AI Agent hỗ trợ chuyên gia lập và duyệt thực đơn dinh dưỡng lâm sàng cho bệnh nhân đái tháo đường type 2.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body>{children}</body>
    </html>
  )
}
