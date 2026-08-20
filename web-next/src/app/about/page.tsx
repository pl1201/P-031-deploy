import Link from 'next/link'

export const metadata = { title: 'Giới thiệu VNutriCare' }

const SECTIONS: { title: string; body: string[] }[] = [
  {
    title: 'VNutriCare là gì',
    body: [
      'VNutriCare là công cụ hỗ trợ chuyên gia dinh dưỡng lâm sàng lập thực đơn cho bệnh nhân đái tháo đường type 2 tại Việt Nam — kết hợp món ăn Việt quen thuộc với các ngưỡng dinh dưỡng đã được tính toán rõ ràng, có nguồn trích dẫn cho từng con số.',
    ],
  },
  {
    title: 'Cách VNutriCare hoạt động: AI hỗ trợ, chuyên gia quyết định',
    body: [
      'Hệ thống dùng trí tuệ nhân tạo để chọn món ăn phù hợp khẩu vị và mục tiêu điều trị, nhưng mọi giá trị calo, đạm, đường, natri… đều được tính bằng công thức xác định trên cơ sở dữ liệu thực phẩm — AI không tự bịa số liệu dinh dưỡng.',
      'Trước khi tới người bệnh, mọi bản thực đơn đều phải qua một chuyên gia dinh dưỡng xem xét và phê duyệt. Không có đường tắt nào đưa thực đơn tới người bệnh mà bỏ qua bước này.',
    ],
  },
  {
    title: 'Ai nên dùng VNutriCare',
    body: [
      'Bệnh nhân đái tháo đường type 2 đang được một chuyên gia dinh dưỡng theo dõi, và các chuyên gia dinh dưỡng lâm sàng cần công cụ lập thực đơn nhanh hơn nhưng vẫn giữ quyền kiểm soát cuối cùng.',
    ],
  },
  {
    title: 'Giới hạn cần biết',
    body: [
      'VNutriCare không chẩn đoán bệnh, không kê đơn thuốc, và không thay thế bác sĩ điều trị. Đây là công cụ hỗ trợ dinh dưỡng, không phải dịch vụ y tế toàn diện.',
    ],
  },
]

export default function AboutPage() {
  return <div className="mx-auto min-h-screen max-w-[720px] px-6 py-12 text-[var(--c-ink)]">
    <Link href="/login" className="text-[11px] font-bold text-[var(--c-green2)]">← Quay lại đăng nhập</Link>
    <h1 className="mt-4 font-[family-name:var(--f-serif)] text-[32px] font-semibold">Giới thiệu VNutriCare</h1>
    <div className="mt-8 grid gap-7">
      {SECTIONS.map(section => <section key={section.title}>
        <h2 className="font-[family-name:var(--f-serif)] text-[17px] font-semibold">{section.title}</h2>
        <div className="mt-2 grid gap-2">{section.body.map((p, i) => <p key={i} className="text-[12.5px] leading-[1.7] text-[var(--c-ink2)]">{p}</p>)}</div>
      </section>)}
    </div>
    <p className="mt-10 text-[11px] text-[var(--c-muted)]">Xem thêm <Link href="/terms" className="font-bold text-[var(--c-green2)] underline">Điều khoản sử dụng</Link>.</p>
  </div>
}
