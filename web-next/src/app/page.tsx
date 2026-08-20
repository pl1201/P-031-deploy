import Image from 'next/image'
import Link from 'next/link'
import { Icon, LeafMark, RiceBotanical } from '@/components/brand-artwork'
import styles from './page.module.css'

const foundations=[
  ['document','Số liệu có nguồn','Món, khẩu phần và rule đều có thể truy ngược về dữ liệu đã lưu.'],
  ['shield','Kiểm tra an toàn','Đối chiếu dị ứng, thuốc và ràng buộc trước khi phát hành.'],
  ['group','Chăm sóc theo ngoại lệ','Chuyên gia tập trung vào ca cần quyết định thay vì duyệt máy móc.'],
]

const trace=[
  ['profile','Hồ sơ','Nam, 58 tuổi · T2DM · metformin'],
  ['chart','Mục tiêu','Phân bố carbohydrate theo bữa'],
  ['bowl','Mâm cơm Việt','Đúng cấu trúc và khẩu vị vùng miền'],
  ['shield','An toàn','Kiểm tra rule và dữ liệu có nguồn'],
  ['usercheck','Quyết định','Duyệt lần đầu hoặc tái sử dụng hợp lệ'],
  ['followup','Theo dõi','Tóm tắt theo tuần, không báo từng bữa'],
]

export default function HomePage(){
  return <main className={styles.page} data-page="landing">
    <header className={styles.nav}><Link className={styles.brand} href="/"><LeafMark/><strong>VNUTRICARE</strong></Link><nav><a href="#patient">Cho người bệnh</a><a href="#expert">Cho chuyên gia</a><a href="#proof">An toàn &amp; nguồn dữ liệu</a></nav><div className={styles.actions}><Link href="/login">Đăng nhập</Link><Link className={styles.demo} href="/login?demo=dietitian">Trải nghiệm demo</Link></div></header>

    <section className={styles.hero}><RiceBotanical className={styles.rice}/><div className={styles.copy}><span className={styles.eyebrow}>DINH DƯỠNG LÂM SÀNG • ĐÁI THÁO ĐƯỜNG TYPE 2</span><h1>Thực đơn món Việt,<br/><em>vừa khẩu vị, đúng<br/>mục tiêu đường huyết.</em></h1><p>Hỗ trợ tạo, kiểm tra và theo dõi thực đơn cá nhân hóa theo carbohydrate, thuốc đang dùng và thói quen ăn uống thực tế.</p><div className={styles.ctas}><Link className={styles.primary} href="/login?demo=patient">Trải nghiệm người bệnh <Icon name="arrowRight"/></Link><Link className={styles.secondary} href="/login?demo=dietitian">Tôi là chuyên gia <Icon name="arrowRight"/></Link></div><div className={styles.safety}><Icon name="shield"/><strong>Hệ thống không tự thay chuyên gia</strong><i/>Chỉ tự động khi policy cho phép</div></div><div className={styles.visual} aria-label="Minh họa bữa ăn Việt được kiểm chứng"><div className={styles.mealPhoto}><Image src="/images/vnutricare-hero-meal.png" alt="Mâm cơm Việt với cơm gạo lứt, cá nướng, rau xanh và canh" fill priority sizes="(max-width: 1050px) 90vw, 52vw"/></div><article className={`${styles.float} ${styles.approved}`}><span><Icon name="check"/></span><strong>ĐÃ KIỂM TRA<br/>TRƯỚC KHI PHÁT HÀNH</strong></article><a className={styles.source} href="#proof"><Icon name="database"/>Xem chuỗi căn cứ <Icon name="chevronRight"/></a></div></section>

    <section className={styles.quickActions} aria-label="Truy cập nhanh">
      <Link href="/login?demo=patient"><span><Icon name="user"/></span><div><strong>Dành cho người bệnh</strong><small>Xem thực đơn và ghi lại bữa ăn</small></div><Icon name="chevronRight"/></Link>
      <Link href="/login?demo=dietitian"><span><Icon name="expert"/></span><div><strong>Dành cho chuyên gia</strong><small>Tạo, kiểm tra và duyệt kế hoạch</small></div><Icon name="chevronRight"/></Link>
      <a href="#proof"><span><Icon name="shield"/></span><div><strong>An toàn và minh bạch</strong><small>Xem cách dữ liệu được kiểm chứng</small></div><Icon name="chevronRight"/></a>
    </section>

    <section className={styles.careStory} aria-labelledby="care-story-title"><div className={styles.carePhoto}><Image src="/images/vnutricare-login-family.png" alt="Gia đình Việt cùng đồng hành trong quá trình chăm sóc sức khỏe" fill sizes="(max-width: 900px) 92vw, 43vw"/></div><div className={styles.careCopy}><small>MỖI NGÀY, MỘT CHÚT AN TÂM HƠN</small><h2 id="care-story-title">Không chỉ là một thực đơn.<br/><em>Đó là cảm giác luôn có người đồng hành.</em></h2><p>VNUTRICARE nối những lựa chọn nhỏ trong từng bữa ăn với mục tiêu chăm sóc dài hạn — đủ rõ để người bệnh làm theo, đủ căn cứ để chuyên gia tin tưởng.</p><ol><li><span>01</span><div><strong>Được thấu hiểu</strong><small>Khẩu vị, bệnh lý và nhịp sống được đặt vào cùng một hồ sơ.</small></div></li><li><span>02</span><div><strong>Được hướng dẫn</strong><small>Mỗi bữa ăn đi kèm khẩu phần và lý do phù hợp dễ hiểu.</small></div></li><li><span>03</span><div><strong>Được đồng hành</strong><small>Tiến trình được nhìn lại theo tuần để điều chỉnh đúng lúc.</small></div></li></ol></div></section>

    <section className={styles.trust}>{foundations.map(([icon,title,text])=><article key={title}><span><Icon name={icon}/></span><div><h2>{title}</h2><p>{text}</p></div></article>)}<div className={styles.process}><h2>Một hành trình, hai vai trò</h2><div>{[['profile','Thu thập hồ sơ'],['chart','Tạo phương án'],['usercheck','Quyết định khi cần'],['followup','Theo dõi theo tuần']].map(([icon,item],index)=><span key={item}><b><Icon name={icon}/><i>{index+1}</i></b><strong>{item}</strong></span>)}</div></div></section>

    <section className={styles.caseStudy} id="proof"><div className={styles.caseIntro}><small>CA MINH HỌA XUYÊN SUỐT</small><h2>Một thực đơn không bắt đầu từ câu hỏi<br/><em>“AI muốn gợi ý món gì?”</em></h2><p>Nó bắt đầu từ hồ sơ, mục tiêu và những điều không được phép bỏ sót. Người xem có thể đi theo cùng một chuỗi từ lúc tạo phương án tới báo cáo tuần.</p><Link href="/login?demo=dietitian">Mở ca demo chuyên gia <Icon name="arrowRight"/></Link></div><div className={styles.patientCard}><span className={styles.patientAvatar}>N</span><div><small>HỒ SƠ #1A8DD9A1</small><h3>Nam · 58 tuổi</h3><p>Đái tháo đường type 2 · Vận động nhẹ · Miền Bắc</p></div><b>metformin</b></div><div className={styles.trace}>{trace.map(([icon,title,text],index)=><article key={title}><span><Icon name={icon}/><i>{index+1}</i></span><div><h3>{title}</h3><p>{text}</p></div>{index<trace.length-1&&<Icon name="chevronRight"/>}</article>)}</div></section>

    <section className={styles.proofMoment}><div className={styles.proofCopy}><small>KHOẢNH KHẮC CHỨNG MINH</small><h2>Nhìn thấy lý do trước khi nhấn duyệt.</h2><p>Thay đổi một món không đưa chuyên gia sang màn hình khác. Hệ thống cho xem chênh lệch dinh dưỡng, cảnh báo mới và nguồn ngay tại vị trí quyết định.</p><ul><li><Icon name="check"/>So sánh món trước và sau</li><li><Icon name="check"/>Tính lại dinh dưỡng trên backend</li><li><Icon name="check"/>Quyết định gắn với đúng phiên bản</li></ul></div><div className={styles.swapCard}><header><div><small>ĐỔI MÓN · BỮA TRƯA</small><h3>Xem trước thay đổi</h3></div><span>Không có cảnh báo mới</span></header><div className={styles.compare}><article><small>HIỆN TẠI</small><strong>Cá nướng nghệ</strong><p>100 g · 210 kcal · 8 g carb</p></article><Icon name="arrowRight"/><article><small>THAY THẾ</small><strong>Cá hấp gừng</strong><p>110 g · 195 kcal · 5 g carb</p></article></div><footer><span>-15 kcal</span><span>-3 g carbohydrate</span><Link href="/login?demo=dietitian" className={styles.primary}>Mở ca demo</Link></footer></div></section>

    <section className={styles.rolesSection}><article id="patient"><small>KHÔNG GIAN NGƯỜI BỆNH</small><h2>Biết hôm nay ăn gì,<br/>không phải đọc một bảng số.</h2><p>Thực đơn theo bữa, khẩu phần dễ hiểu, lý do phù hợp và nhật ký trung thực. Người bệnh chỉ nhìn thấy phiên bản đã được phát hành.</p><div className={styles.miniMeals}>{['Bữa sáng','Bữa trưa','Bữa phụ','Bữa tối'].map((item,index)=><span key={item}><i>{index+1}</i><strong>{item}</strong><small>{index===1?'Đang đến giờ':index===0?'Đã ghi nhận':'Theo kế hoạch'}</small></span>)}</div><Link href="/login?demo=patient">Xem giao diện người bệnh <Icon name="arrowRight"/></Link></article><article id="expert"><small>KHÔNG GIAN CHUYÊN GIA</small><h2>Chỉ hiện điều cần<br/>được xử lý hôm nay.</h2><p>Ca chặn phát hành, ca cần xác nhận và bệnh nhân cần chú ý được ưu tiên. Ca ổn định tiếp tục theo policy đã định.</p><div className={styles.miniQueue}><span><b>3</b><small>Cần xử lý ngay</small></span><span><b>8</b><small>Có thể duyệt nhanh</small></span><span><b>12</b><small>Theo dõi tuần</small></span></div><Link href="/login?demo=dietitian">Xem giao diện chuyên gia <Icon name="arrowRight"/></Link></article></section>

    <section className={styles.finalCta}><RiceBotanical/><div><small>BẮT ĐẦU TỪ MỘT CA BỆNH THẬT</small><h2>Trải nghiệm toàn bộ chuỗi quyết định.</h2><p>Từ thực đơn món Việt đến báo cáo tuần dành cho chuyên gia.</p></div><div><Link href="/login?demo=patient">Demo người bệnh</Link><Link href="/login?demo=dietitian">Demo chuyên gia</Link></div></section>
    <footer className={styles.footer}><Link className={styles.brand} href="/"><LeafMark/><strong>VNUTRICARE</strong></Link><p>Công cụ hỗ trợ dinh dưỡng lâm sàng. Không thay thế tư vấn hoặc chẩn đoán y khoa.</p><Link href="/login">Đăng nhập</Link></footer>
  </main>
}
