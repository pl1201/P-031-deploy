import { useState } from 'react'
import '../styles.css'

type Patient = {
  id: number
  initials: string
  name: string
  meta: string
  weight: number
  height: number
  bmi: number
  hba1c: number
  diagnosis: string
  medication: string
  allergy: string
  alert: string
}

const patients: Patient[] = [
  { id: 1, initials: 'MA', name: 'Nguyễn Minh Anh', meta: 'Nữ · 54 tuổi · TP. Hồ Chí Minh', weight: 64, height: 158, bmi: 25.6, hba1c: 7.2, diagnosis: 'Đái tháo đường type 2', medication: 'Metformin 500 mg', allergy: 'Không ghi nhận', alert: 'HbA1c cao hơn mục tiêu; ưu tiên phân bổ carbohydrate đều giữa các bữa.' },
  { id: 2, initials: 'QT', name: 'Trần Quốc Tuấn', meta: 'Nam · 61 tuổi · Đà Nẵng', weight: 72, height: 169, bmi: 25.2, hba1c: 6.8, diagnosis: 'Đái tháo đường type 2', medication: 'Metformin 850 mg', allergy: 'Tôm, cua', alert: 'Có tiền sử dị ứng hải sản; tất cả món chứa giáp xác phải bị loại.' },
  { id: 3, initials: 'HL', name: 'Lê Thu Hương', meta: 'Nữ · 48 tuổi · Hà Nội', weight: 58, height: 155, bmi: 24.1, hba1c: 7.6, diagnosis: 'Đái tháo đường type 2', medication: 'Gliclazide 30 mg', allergy: 'Không ghi nhận', alert: 'Nguy cơ hạ đường huyết; cần duy trì giờ ăn ổn định và không bỏ bữa.' },
]

const initialMeals = [
  { time: '07:00', label: 'BỮA SÁNG', title: 'Bún cá rau cần', description: 'Bún tươi 80 g · cá rô phi 90 g · rau cần 60 g · nước dùng nhạt', kcal: 415, carb: 49, protein: 28, source: 'NIN + công thức chuẩn hóa' },
  { time: '12:00', label: 'BỮA TRƯA', title: 'Cơm gạo lứt · gà áp chảo', description: 'Gạo lứt 65 g · ức gà 110 g · cải thìa 120 g · canh bí xanh', kcal: 632, carb: 68, protein: 42, source: 'NIN + USDA FDC' },
  { time: '18:30', label: 'BỮA TỐI', title: 'Cá thu sốt cà · rau luộc', description: 'Cá thu 90 g · cơm trắng 55 g · rau muống 120 g · bưởi 100 g', kcal: 541, carb: 56, protein: 34, source: 'NIN + dữ liệu món Việt' },
]

function App() {
  const [patient, setPatient] = useState(patients[0])
  const [meals, setMeals] = useState(initialMeals)
  const [generating, setGenerating] = useState(false)
  const [approved, setApproved] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [toast, setToast] = useState('')

  const notify = (message: string) => {
    setToast(message)
    window.setTimeout(() => setToast(''), 2600)
  }

  const choosePatient = (next: Patient) => {
    setPatient(next)
    setApproved(false)
    notify(`Đã chuyển sang hồ sơ ${next.name}`)
  }

  const regenerate = () => {
    setGenerating(true)
    window.setTimeout(() => {
      setMeals((current) => current.map((meal, index) => index === 0 ? {
        ...meal,
        title: meal.title === 'Bún cá rau cần' ? 'Miến gà nấm hương' : 'Bún cá rau cần',
        description: meal.title === 'Bún cá rau cần' ? 'Miến dong 65 g · ức gà 90 g · nấm hương 40 g · cải xanh' : initialMeals[0].description,
      } : meal))
      setGenerating(false)
      notify('Phương án mới đã vượt qua 12 kiểm tra an toàn')
    }, 900)
  }

  const approve = () => {
    setApproved(true)
    setDialogOpen(false)
    notify(`Đã duyệt thực đơn cho ${patient.name}`)
  }

  return (
    <>
      <a className="skip-link" href="#main-content">Bỏ qua điều hướng</a>
      <div className="app-shell">
        <aside className={`sidebar ${menuOpen ? 'open' : ''}`} aria-label="Điều hướng chính">
          <a className="brand" href="#overview" aria-label="VNUTRICARE, trang tổng quan">
            <span className="brand-mark" aria-hidden="true">V</span>
            <span><strong>VNUTRI</strong><em>CARE</em></span>
          </a>
          <nav className="main-nav" aria-label="Chức năng">
            <p className="nav-label">Không gian làm việc</p>
            <a className="nav-item active" href="#overview" aria-current="page"><span aria-hidden="true">⌂</span>Tổng quan</a>
            <a className="nav-item" href="#patients"><span aria-hidden="true">◎</span>Hồ sơ mô phỏng</a>
            <a className="nav-item" href="#meal-plan"><span aria-hidden="true">◇</span>Thực đơn AI</a>
            <a className="nav-item" href="#evidence"><span aria-hidden="true">◫</span>Nguồn dữ liệu</a>
            <p className="nav-label nav-label-secondary">Kiểm soát</p>
            <a className="nav-item" href="#safety"><span aria-hidden="true">△</span>Cảnh báo an toàn <b>2</b></a>
            <a className="nav-item" href="#history"><span aria-hidden="true">↻</span>Lịch sử duyệt</a>
          </nav>
          <div className="sidebar-note"><span className="pulse" aria-hidden="true" /><div><strong>Hệ thống sẵn sàng</strong><small>Clinical engine v0.3</small></div></div>
          <div className="sidebar-foot"><div className="avatar" aria-hidden="true">LP</div><div><strong>BS. Linh Phạm</strong><small>Chuyên gia dinh dưỡng</small></div><button className="icon-button" aria-label="Mở tùy chọn tài khoản">•••</button></div>
        </aside>

        <main id="main-content" tabIndex={-1}>
          <header className="topbar">
            <button className="menu-button" onClick={() => setMenuOpen(!menuOpen)} aria-label="Mở điều hướng" aria-expanded={menuOpen}>☰</button>
            <div className="breadcrumb"><span>Hồ sơ mô phỏng</span><i>/</i><strong>{patient.name}</strong></div>
            <div className="top-actions"><span className="synthetic-badge">DỮ LIỆU MÔ PHỎNG</span><button className="icon-button bell" aria-label="Thông báo mới">♢<span /></button></div>
          </header>

          <section className="content" id="overview">
            <div className="hero-row">
              <div><p className="eyebrow">HỒ SƠ #VN-0248 · CẬP NHẬT HÔM NAY</p><h1>Chào buổi sáng,<br /><em>BS. Linh.</em></h1><p className="hero-copy">Một thực đơn mới đang chờ bạn kiểm tra. Mọi con số được tính bởi lõi quy tắc và có thể truy vết về nguồn.</p></div>
              <div className="hero-stamp" aria-hidden="true"><span>01</span><small>CA CHỜ DUYỆT</small></div>
            </div>

            <section className="patient-selector" id="patients" aria-labelledby="patient-heading">
              <div className="section-heading"><div><p className="eyebrow">BƯỚC 01</p><h2 id="patient-heading">Chọn hồ sơ</h2></div><button className="text-button" type="button">Xem tất cả 06 hồ sơ →</button></div>
              <div className="patient-list" role="list">
                {patients.map((item) => <button key={item.id} className={`patient-card ${item.id === patient.id ? 'selected' : ''}`} type="button" role="listitem" aria-pressed={item.id === patient.id} onClick={() => choosePatient(item)}><span className="card-top"><span className="mini-monogram" aria-hidden="true">{item.initials}</span><span className="check" aria-hidden="true">✓</span></span><strong>{item.name}</strong><small>{item.meta}</small></button>)}
              </div>
            </section>

            <div className="clinical-grid">
              <section className="profile-panel" aria-labelledby="profile-heading">
                <div className="panel-title"><div><p className="eyebrow">HỒ SƠ ĐANG CHỌN</p><h2 id="profile-heading">Chỉ số lâm sàng</h2></div><button className="icon-button outlined" aria-label="Chỉnh sửa hồ sơ">✎</button></div>
                <div className="identity"><div className="identity-monogram">{patient.initials}</div><div><h3>{patient.name}</h3><p>{patient.meta}</p></div><span className="status-chip">Đủ dữ liệu</span></div>
                <dl className="stats"><div><dt>Cân nặng</dt><dd>{patient.weight} <small>kg</small></dd></div><div><dt>Chiều cao</dt><dd>{patient.height} <small>cm</small></dd></div><div><dt>BMI</dt><dd>{patient.bmi} <small>kg/m²</small></dd></div><div><dt>HbA1c</dt><dd>{patient.hba1c} <small>%</small></dd></div></dl>
                <div className="clinical-detail"><div><span>Chẩn đoán</span><strong>{patient.diagnosis}</strong></div><div><span>Thuốc đang dùng</span><strong>{patient.medication}</strong></div><div><span>Dị ứng</span><strong>{patient.allergy}</strong></div></div>
                <div className="alert warning" role="status"><span aria-hidden="true">!</span><p><strong>Cần lưu ý</strong><br />{patient.alert}</p></div>
              </section>

              <section className="target-panel" aria-labelledby="target-heading">
                <div className="panel-title"><div><p className="eyebrow">BƯỚC 02 · LÕI XÁC ĐỊNH</p><h2 id="target-heading">Mục tiêu mỗi ngày</h2></div><span className="verified-chip">✓ ĐÃ TÍNH</span></div>
                <div className="energy-orbit"><div><span>1.650</span><small>kcal / ngày</small></div><svg viewBox="0 0 180 180" role="img" aria-label="Mục tiêu năng lượng 1.650 kilocalo mỗi ngày"><circle cx="90" cy="90" r="78" className="orbit-track" /><circle cx="90" cy="90" r="78" className="orbit-value" /></svg></div>
                <div className="macro-list">{[['carb','Carbohydrate','45% năng lượng','186 g'],['protein','Protein','20% năng lượng','82 g'],['fat','Chất béo','35% năng lượng','64 g'],['fiber','Chất xơ','Tối thiểu','25 g']].map(([tone,label,note,value]) => <div key={label}><span className={`macro-dot ${tone}`} /><p><strong>{label}</strong><small>{note}</small></p><b>{value}</b></div>)}</div>
                <details className="rule-details"><summary>04 quy tắc đã áp dụng <span>⌄</span></summary><ul><li>Phân bổ carbohydrate đều theo bữa</li><li>Ưu tiên thực phẩm GI thấp</li><li>Đường tự do dưới 10% năng lượng</li><li>Đánh dấu món thiếu nguồn để chuyên gia kiểm tra</li></ul></details>
              </section>
            </div>

            <section className="meal-section" id="meal-plan" aria-labelledby="meal-heading">
              <div className="section-heading meal-heading"><div><p className="eyebrow">BƯỚC 03 · AGENT + KIỂM TRA QUY TẮC</p><h2 id="meal-heading">Thực đơn gợi ý</h2></div><div className="meal-actions"><span className="draft-chip">{approved ? 'ĐÃ DUYỆT · SẴN SÀNG PHÁT HÀNH' : generating ? 'ĐANG KIỂM TRA QUY TẮC' : 'BẢN NHÁP · CHỜ DUYỆT'}</span><button className="secondary-button" onClick={regenerate} disabled={generating}>↻ {generating ? 'Đang sinh...' : 'Sinh lại'}</button><button className="primary-button" onClick={() => setDialogOpen(true)}>Duyệt thực đơn <span>→</span></button></div></div>
              <div className="safety-strip" role="status"><div><span>✓</span><p><strong>Đã qua 12 kiểm tra an toàn</strong><small>Không phát hiện dị ứng, tương tác thuốc hoặc vượt ngưỡng bắt buộc.</small></p></div><button className="text-button" type="button">Xem báo cáo kiểm tra</button></div>
              <div className="meal-grid" aria-busy={generating}>{meals.map((meal) => <article className="meal-card" key={`${meal.label}-${meal.title}`}><header className="meal-card-head"><span>{meal.label}</span><b>{meal.time}</b></header><div className="meal-dish"><h3>{meal.title}</h3><p>{meal.description}</p></div><div className="meal-macros" aria-label="Dinh dưỡng bữa ăn"><div><span>{meal.kcal}</span><small>kcal</small></div><div><span>{meal.carb} g</span><small>carb</small></div><div><span>{meal.protein} g</span><small>protein</small></div></div><a className="source-link" href="#evidence"><span>⌘ {meal.source}</span><span aria-hidden="true">→</span></a></article>)}</div>
              <p className="medical-note"><strong>Lưu ý:</strong> Gợi ý này chỉ hỗ trợ chuyên gia ra quyết định, không thay thế chẩn đoán hoặc chỉ định y khoa. Chỉ thực đơn đã được chuyên gia duyệt mới hiển thị cho người bệnh.</p>
            </section>
          </section>
        </main>
      </div>

      <div className={`toast ${toast ? 'show' : ''}`} role="status" aria-live="polite">{toast}</div>
      {dialogOpen && <div className="dialog-backdrop" role="presentation" onMouseDown={() => setDialogOpen(false)}><div className="dialog-card" role="dialog" aria-modal="true" aria-labelledby="dialog-title" onMouseDown={(event) => event.stopPropagation()}><button className="dialog-close icon-button" onClick={() => setDialogOpen(false)} aria-label="Đóng">×</button><p className="eyebrow">XÁC NHẬN LÂM SÀNG</p><h2 id="dialog-title">Duyệt thực đơn này?</h2><p>Sau khi duyệt, thực đơn sẽ được phát hành cho hồ sơ mô phỏng <strong>{patient.name}</strong> và lưu vào lịch sử.</p><label htmlFor="approval-note">Ghi chú chuyên gia <span>(không bắt buộc)</span></label><textarea id="approval-note" rows={3} placeholder="Ví dụ: Theo dõi đường huyết sau ăn trong tuần đầu..." autoFocus /><div className="dialog-actions"><button className="secondary-button" onClick={() => setDialogOpen(false)}>Quay lại</button><button className="primary-button" onClick={approve}>Xác nhận duyệt</button></div></div></div>}
    </>
  )
}

export default App
