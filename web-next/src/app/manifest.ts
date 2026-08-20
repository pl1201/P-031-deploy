import type { MetadataRoute } from 'next'

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'VNutriCare — Tư vấn dinh dưỡng lâm sàng',
    short_name: 'VNutriCare',
    description: 'AI Agent hỗ trợ chuyên gia lập và duyệt thực đơn dinh dưỡng lâm sàng cho bệnh nhân đái tháo đường type 2.',
    start_url: '/login',
    display: 'standalone',
    background_color: '#f7faf8',
    theme_color: '#0072bc',
    lang: 'vi',
    icons: [
      { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
      { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'maskable' },
      { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
      { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
    ],
  }
}
