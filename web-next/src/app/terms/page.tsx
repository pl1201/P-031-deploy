import Link from 'next/link'

export const metadata = { title: 'Điều khoản sử dụng' }

const SECTIONS: { title: string; body: string[] }[] = [
  {
    title: '1. VNutriCare là gì',
    body: [
      'VNutriCare là công cụ hỗ trợ chuyên gia dinh dưỡng lâm sàng lập và theo dõi thực đơn cho bệnh nhân đái tháo đường type 2. Hệ thống sử dụng công nghệ trí tuệ nhân tạo để soạn bản nháp thực đơn, nhưng mọi bản nháp đều phải được chuyên gia dinh dưỡng có chuyên môn xem xét và phê duyệt trước khi tới người bệnh.',
    ],
  },
  {
    title: '2. Giới hạn y tế quan trọng',
    body: [
      'VNutriCare KHÔNG chẩn đoán bệnh, KHÔNG kê đơn thuốc, KHÔNG đề xuất thay đổi liều lượng hoặc loại thuốc đang dùng, và KHÔNG diễn giải kết quả xét nghiệm thành kết luận y khoa.',
      'VNutriCare KHÔNG thay thế bác sĩ điều trị hoặc chuyên gia y tế của bạn. Mọi quyết định liên quan tới chẩn đoán, điều trị, hoặc thuốc men phải do bác sĩ của bạn quyết định.',
      'Nếu bạn gặp triệu chứng bất thường hoặc tình huống khẩn cấp, hãy liên hệ ngay cơ sở y tế gần nhất — không chờ phản hồi từ hệ thống hoặc chuyên gia dinh dưỡng.',
    ],
  },
  {
    title: '3. Trách nhiệm của bạn khi sử dụng',
    body: [
      'Cung cấp thông tin sức khoẻ, cân nặng, và nhật ký ăn uống trung thực và chính xác nhất có thể — thực đơn được lập dựa trên dữ liệu bạn cung cấp.',
      'Số cân nặng bạn tự ghi trong ứng dụng là dữ liệu theo dõi hỗ trợ chuyên gia quan sát xu hướng, không tự động thay đổi hồ sơ lâm sàng gốc của bạn — mọi thay đổi hồ sơ lâm sàng vẫn do chuyên gia xác nhận.',
      'Không chia sẻ tài khoản của bạn với người khác. Bạn chịu trách nhiệm bảo mật thông tin đăng nhập.',
    ],
  },
  {
    title: '4. Dữ liệu và quyền riêng tư',
    body: [
      'Thông tin sức khoẻ của bạn chỉ được dùng để lập và theo dõi thực đơn, và chỉ chia sẻ với chuyên gia dinh dưỡng phụ trách hồ sơ của bạn.',
      'Mọi giá trị dinh dưỡng hiển thị trong thực đơn đều có nguồn trích dẫn (cơ sở dữ liệu thực phẩm đã kiểm chứng hoặc ước tính có ghi chú rõ ràng) — hệ thống không tự bịa số liệu.',
    ],
  },
  {
    title: '5. Thay đổi điều khoản',
    body: [
      'Điều khoản này có thể được cập nhật khi hệ thống bổ sung tính năng mới. Phiên bản áp dụng là phiên bản hiển thị tại thời điểm bạn sử dụng ứng dụng.',
    ],
  },
]

export default function TermsPage() {
  return <div className="mx-auto min-h-screen max-w-[720px] px-6 py-12 text-[var(--c-ink)]">
    <Link href="/login" className="text-[11px] font-bold text-[var(--c-green2)]">← Quay lại đăng nhập</Link>
    <h1 className="mt-4 font-[family-name:var(--f-serif)] text-[32px] font-semibold">Điều khoản sử dụng</h1>
    <p className="mt-2 text-[11px] text-[var(--c-muted)]">Bản nháp — vui lòng liên hệ đội vận hành nếu cần bản có giá trị pháp lý chính thức.</p>
    <div className="mt-8 grid gap-7">
      {SECTIONS.map(section => <section key={section.title}>
        <h2 className="font-[family-name:var(--f-serif)] text-[17px] font-semibold">{section.title}</h2>
        <div className="mt-2 grid gap-2">{section.body.map((p, i) => <p key={i} className="text-[12.5px] leading-[1.7] text-[var(--c-ink2)]">{p}</p>)}</div>
      </section>)}
    </div>
  </div>
}
