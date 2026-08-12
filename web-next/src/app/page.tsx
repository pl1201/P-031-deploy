import Link from 'next/link'
import Image from 'next/image'
import { Icon, LeafMark, RiceBotanical } from '@/components/brand-artwork'
import styles from './page.module.css'

export default function HomePage() {
  const values=[
    ['document','Số liệu có nguồn','Sử dụng dữ liệu dinh dưỡng được kiểm chứng và cập nhật thường xuyên.'],
    ['shield','Kiểm tra an toàn','Kiểm tra tương tác với thuốc, dị ứng và các rủi ro dinh dưỡng liên quan.'],
    ['group','Chuyên gia phê duyệt','Chuyên gia dinh dưỡng/tiết chế duyệt trước khi thực đơn được phát hành.'],
  ]
  return <main className={styles.page}>
    <header className={styles.nav}>
      <Link className={styles.brand} href="/"><LeafMark/><strong>VNUTRICARE</strong></Link>
      <nav><a href="#roles">Cho người bệnh</a><a href="#roles">Cho chuyên gia</a><a href="#safety">An toàn &amp; nguồn dữ liệu</a></nav>
      <div className={styles.actions}><Link href="/login">Đăng nhập</Link><Link className={styles.demo} href="/login">Xem bản demo</Link></div>
    </header>
    <section className={styles.hero}>
      <RiceBotanical className={styles.rice}/>
      <div className={styles.copy}>
        <span className={styles.eyebrow}>DINH DƯỠNG LÂM SÀNG • ĐÁI THÁO ĐƯỜNG TYPE 2</span>
        <h1>Thực đơn món Việt,<br/><em>vừa khẩu vị, đúng<br/>mục tiêu đường huyết.</em></h1>
        <p>Hỗ trợ chuyên gia tạo và duyệt thực đơn cá nhân hóa theo carbohydrate, GI/GL, thuốc đang dùng và thói quen ăn uống.</p>
        <div className={styles.ctas}><Link className={styles.primary} href="/login">Xem bản demo <b>›</b></Link><Link className={styles.secondary} href="/login">Tôi là chuyên gia <b>›</b></Link></div>
        <div className={styles.safety}><Icon name="shield"/><strong>AI không tự quyết định</strong><i/>Chuyên gia duyệt trước khi phát hành</div>
      </div>
      <div className={styles.visual} aria-label="Minh họa bữa ăn Việt được kiểm chứng">
        <div className={styles.mealPhoto}><Image src="/images/vnutricare-hero-meal.png" alt="Mâm cơm Việt với cơm gạo lứt, cá nướng, rau xanh và canh" fill priority sizes="(max-width: 1050px) 90vw, 52vw"/></div>
        <article className={`${styles.float} ${styles.nutrition}`}><small>BỮA TRƯA HÔM NAY</small><strong>46 <i>g Carb</i></strong><span>GL 14</span><b><Icon name="check"/>Đạt mục tiêu</b></article>
        <article className={`${styles.float} ${styles.approved}`}><span><Icon name="check"/></span><strong>ĐÃ ĐƯỢC<br/>CHUYÊN GIA DUYỆT</strong></article>
        <div className={styles.source}><Icon name="database"/>Xem nguồn dữ liệu <b>›</b></div>
      </div>
    </section>
    <section className={styles.trust} id="safety">
      {values.map(([icon,title,text])=><article key={title}><span><Icon name={icon}/></span><div><h2>{title}</h2><p>{text}</p></div></article>)}
      <div className={styles.process} id="roles"><h2>Quy trình 4 bước chuẩn hóa</h2><div>{[
        ['profile','Thu thập thông tin','Hồ sơ lâm sàng, thuốc, thói quen ăn uống.'],
        ['chart','Đề xuất thực đơn','AI gợi ý thực đơn phù hợp mục tiêu đường huyết.'],
        ['usercheck','Chuyên gia duyệt','Chuyên gia xem xét, chỉnh sửa và phê duyệt.'],
        ['followup','Theo dõi & tối ưu','Theo dõi đáp ứng và tối ưu theo thời gian.'],
      ].map(([icon,item,description],index)=><span key={item}><b><Icon name={icon}/><i>{index+1}</i></b><strong>{item}</strong><small>{description}</small></span>)}</div></div>
    </section>
  </main>
}
