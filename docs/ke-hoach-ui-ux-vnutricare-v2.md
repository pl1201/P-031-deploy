# Kế hoạch cập nhật UI/UX — VNutriCare (v2 — bản thực thi)

Ngày lập: 2026-08-15 · Cập nhật: 2026-08-15 (v2)
Phạm vi: `web-next` — 5 màn hình đã audit trực tiếp trên code
Trạng thái: **kế hoạch đã bổ sung tiêu chí nghiệm thu, sẵn sàng giao thực thi**
Thay đổi so với v1: bổ sung acceptance criteria cho từng ticket, decision gate chặn, test strategy, phạm vi mobile/accessibility, tách ticket quá tải, chuyển vấn đề backend thành ticket có chủ.

---

## 0. Cách đọc tài liệu

Mỗi mục theo format: **Vấn đề → Bằng chứng code → Đề xuất → Tiêu chí nghiệm thu → Ticket**.

Ưu tiên P0 > P1 > P2 > P3, tiêu chí: rủi ro an toàn lâm sàng > vỡ mô hình vai trò (bệnh nhân vs chuyên gia) > rò rỉ thuật ngữ kỹ thuật/thiếu phân cấp thị giác > polish thuần túy.

Ticket prefix `FE-` nối tiếp `docs/TICKETS.md` (đã có `FE-01`…`FE-08`), bắt đầu `FE-09`. Ticket backend dùng prefix `BE-`. Quyết định cần chốt dùng prefix `DEC-`.

**Quy ước cho agent thực thi:**
- Không bắt đầu ticket nào khi decision gate liên quan (mục 1) chưa `RESOLVED`.
- Không tự đặt ngưỡng lâm sàng. Gặp chỗ cần ngưỡng → dừng, ghi câu hỏi vào mục 8, chờ R2.
- Mọi ticket phải pass toàn bộ tiêu chí nghiệm thu của chính nó trước khi mở PR.
- Ticket có nhãn `[cần thiết kế trước]` không được code khi chưa có mockup được duyệt.

Màn hình audit:
- A. Hàng chờ phê duyệt — `src/app/dietitian/reviews/page.tsx`
- B. Tạo thực đơn — `src/app/dietitian/meal-plans/new/page.tsx`
- C. Đối chiếu nhật ký — `src/app/dietitian/food-logs/page.tsx`
- D. Chi tiết phương án thực đơn (trong file B, phần review sau khi sinh)
- E. Không gian bệnh nhân — Tuần của bạn — `src/app/patient/weekly/page.tsx`

**Màn hình CHƯA audit nhưng nằm trong vùng ảnh hưởng** (quan trọng cho FE-11):
`/dietitian` (Tổng quan hôm nay) · `/dietitian/patients` · `/dietitian/stats` · `/patient` (Hôm nay) · `/patient/foods` (Món đã ăn) · `/patient/profile` · toàn bộ layout/sidebar dùng chung.

---

## 1. Decision gates — chặn trước khi code

Ba quyết định dưới đây phải chốt trước, vì chọn sai thứ tự sẽ phải làm lại phần lớn công việc.

### DEC-01 — Có tách design system riêng cho không gian bệnh nhân không?

**Vì sao chặn:** nếu chốt "có tách", phần lớn công của `FE-11` (refactor token dùng chung) và `FE-12` (redesign weekly) phải làm lại theo hệ mới. Quyết định này đứng **trước** `FE-11`, không phải song song.

**Cần trả lời:** (a) Tách hoàn toàn 2 design system, (b) chung token nền tảng nhưng tách lớp component patient, hay (c) giữ chung, chỉ giảm mật độ thông tin ở màn patient.

**Chủ trì:** R3 · **Hạn:** trước khi mở sprint kế · **Trạng thái:** `OPEN`

### DEC-02 — Cơ chế override cho cảnh báo chặn duyệt (liên quan FE-09)

**Vì sao chặn:** không thiết kế xong đường thoát thì không code được phần chặn.

**Cần trả lời:** mức nghiêm trọng nào chặn cứng hoàn toàn, mức nào cho override kèm lý do bắt buộc, ai có quyền override, log lưu những trường gì.

**Chủ trì:** R2 (lâm sàng) · **Hạn:** trước khi bắt đầu FE-09 · **Trạng thái:** `OPEN`

### DEC-03 — Hàng chờ phê duyệt thực tế dài bao nhiêu?

**Vì sao chặn:** quyết định P3-mục-8 (chỉ báo ưu tiên/khẩn cấp) có được nâng lên P1 hay không phụ thuộc con số này. Ở v1 nó nằm trong nhóm P3 nên gần như chắc chắn bị quên.

**Cần trả lời:** số ca chờ duyệt trung bình và ở P95 trong vận hành thật. Nếu P95 > 15 ca → nâng lên P1, vì lúc đó chuyên gia không còn khả năng quét mắt toàn danh sách.

**Chủ trì:** R2 + data · **Hạn:** trong sprint này · **Trạng thái:** `OPEN`

---

## 2. P0 — Rủi ro an toàn lâm sàng

### 2.1 Tick xanh "đã kiểm tra" che mất cảnh báo thuốc–thực phẩm (màn D)

**Vấn đề:** 5 mục checklist (Năng lượng, Carbohydrate, Phân bổ bữa, GI/GL, Dị ứng) đều tô xanh `.stateOk` như đã pass; cảnh báo tương tác thuốc–insulin (nghiêm trọng hơn) nằm ở box cam bên dưới với trọng lượng thị giác yếu hơn 5 chip xanh phía trên.

**Bằng chứng code** (`meal-plans/new/page.tsx:16, 184-185`): `verified` là **một boolean tính chung cho cả kế hoạch** (`plan?.review_packet && menu_hash_ready && nutrition_hash_ready`), áp cho cả 5 mục. Chỉ `carb` và `allergy` có `hasViolation()` riêng; `distribution` và `gi` **không bao giờ** chuyển sang cảnh báo dù dữ liệu có vấn đề. Box `.drugCheck` (nền `#fff9ef`, viền `#e9bd82`) nằm dưới checklist trong cùng `evidenceCard`.

**Đề xuất:**
1. Bỏ pattern "1 boolean áp cho 5 mục". Mỗi mục tự tính trạng thái từ dữ liệu của chính nó — `distribution`, `gi`, `energy` cũng cần logic riêng như `carb`/`allergy` đã có.
2. Cảnh báo tương tác thuốc–thực phẩm đưa lên **đầu** evidence rail (trước checklist), dùng tông cảnh báo mạnh hơn mức thông thường.
3. Chặn nút duyệt khi tương tác ở mức nghiêm trọng — **kèm override có ghi log**, không chặn cứng tuyệt đối (xem DEC-02). Chặn cứng không đường thoát sẽ khiến chuyên gia xử lý vòng ngoài hệ thống khi rule chạy sai.
4. Đọc skill `menu-safety-check` trước khi sửa.

**Tiêu chí nghiệm thu:**
- [ ] Mỗi mục trong 5 mục checklist có hàm tính trạng thái độc lập; grep toàn file không còn chỗ nào 1 biến boolean chung áp cho nhiều mục.
- [ ] Test case: dữ liệu vi phạm `distribution` → mục Phân bổ bữa hiện cảnh báo (v1 luôn xanh). Tương tự cho `gi`, `energy`.
- [ ] Test case: dữ liệu có tương tác thuốc nghiêm trọng → cảnh báo hiển thị **phía trên** checklist trong DOM order, và nút duyệt ở trạng thái chặn.
- [ ] Override ghi đủ: user id, thời điểm, mức nghiêm trọng bị override, lý do do người dùng nhập (bắt buộc, không cho để trống).
- [ ] Kiểm tra thủ công: che phần dưới màn hình, chỉ nhìn 2 giây phần trên evidence rail — cảnh báo thuốc phải là thứ nhìn thấy trước tiên.
- [ ] Tương phản cảnh báo đạt WCAG AA (≥4.5:1 cho text).

**Ticket:** `FE-09` · Ước lượng: 3–5 ngày · Phụ thuộc: DEC-02 · `[cần R2 duyệt ngưỡng]`

### 2.2 Điểm confidence trùng nhau ở mọi ứng viên gán món (màn C)

**Vấn đề:** 5 lựa chọn gán món trong 1 card đều hiện `67%`.

**Bằng chứng code** (`food-logs/page.tsx:55`): `{item.matched_on} · {(item.score*100).toFixed(0)}%` — `score` lấy từ `api.listUnresolvedLogs()`, **là dữ liệu backend thật, không hardcode frontend**. Nguồn lỗi nằm ở service matching/scoring phía backend.

**Đề xuất — tách làm 2 việc có chủ rõ ràng:**

**BE-01 (backend, gốc rễ):** Kiểm tra hàm tính confidence trong service matching. Model trả điểm giống hệt cho nhiều ứng viên khác nhau là vi phạm RULE-2 (không con số nào không có nguồn).
- Chủ trì: đội backend/data · Hạn: trong sprint này · Ưu tiên: P0
- Đây **không phải** việc ngoài phạm vi — đây là gốc của vấn đề P0. Ticket FE chỉ giảm nhẹ triệu chứng.

**FE-10 (frontend, giảm nhẹ tạm thời):** Khi chênh lệch giữa các score < 1%, hiển thị chú thích "độ tin cậy chưa phân biệt rõ giữa các lựa chọn" thay vì im lặng hiện số trùng.

**Tiêu chí nghiệm thu FE-10:**
- [x] Ngưỡng 1% đặt trong constant có tên rõ nghĩa (`SCORE_DISTINGUISH_THRESHOLD`), không phải magic number rải rác.
- [x] Có comment ở đầu block giải thích đây là mitigation tạm thời cho BE-01.
- [x] Ghi vào `docs/TICKETS.md`: FE-10 là mitigation, điều kiện gỡ = BE-01 đóng và verify score đã phân biệt.
- [x] Test case xác nhận bằng browser thật trên dữ liệu demo: card "rau" (5 ứng viên cùng 67%) → hiện chú thích. "trứng"/"thịt bò"/"thịt heo" (score chênh) → không hiện.

**Ticket:** `FE-10` ✅ đã làm (2026-08-15, `web-next`) + `BE-01` (chưa làm, thuộc backend) · Ước lượng FE: 0.5 ngày

### 2.3 Trạng thái disabled của nút hành động không đủ rõ (màn C)

**Vấn đề:** nút "Gán món và tính lại" trông như bấm được dù nội dung nói "không có ứng viên đủ gán".

**Bằng chứng code** (`food-logs/page.tsx:55`, `followup.module.css`): nút **có** `disabled={busy||chosen==null||invalid}` và CSS `.logRow footer button:disabled{opacity:.5}` — logic đúng, nhưng `opacity:.5` trên nền teal đậm (`#18a5a7`) vẫn đủ bão hòa để trông bấm được. Đây là vấn đề **tương phản trạng thái**, không phải lỗi logic.

**Đề xuất:** trạng thái disabled đổi sang nền xám trung tính (giảm cả saturation lẫn độ sáng, không chỉ opacity), thêm `cursor:not-allowed`.

**Tiêu chí nghiệm thu:**
- [x] Nút disabled không còn giữ hue teal — dùng nền xám trung tính (`--c-border2` + `--c-disabled-fg`, xác nhận bằng browser thật: `rgb(182,192,197)`/`rgb(58,69,70)`).
- [x] Có `cursor:not-allowed`.
- [ ] Kiểm tra ở chế độ giả lập mù màu (deuteranopia) vẫn phân biệt được enabled/disabled — **chưa làm**, cần công cụ DevTools/extension ngoài sandbox này.
- [x] Áp dụng nhất quán cho **mọi** nút disabled trong app — rule toàn cục trong `globals.css` + dọn 10 rule `opacity` cục bộ trùng lặp ở 9 file CSS module khác.

**Ticket:** `FE-18` ✅ đã làm (2026-08-15, `web-next`) · Ước lượng: 1 ngày

---

## 3. P1 — Vỡ mô hình vai trò / hệ thống màu

### 3.1 Teal dùng cho quá nhiều loại tín hiệu (toàn bộ app)

**Bằng chứng code** (`globals.css`): `--c-green:#18a5a7` áp cho `.btn-primary`, `.clinical-tab.active`, gradient sidebar nav, badge trạng thái, tick checklist, viền "hôm nay" ở weekly, huy hiệu "Cần thêm dữ liệu" — ít nhất 5 vai trò ngữ nghĩa dùng chung 1 token.

**Đề xuất — tách token theo vai trò:**

| Token mới | Vai trò | Thay cho |
|---|---|---|
| `--c-action` | Nút hành động chính (bấm được) | `.btn-primary` |
| `--c-nav-active` | Điều hướng đang chọn | `.clinical-tab.active`, sidebar gradient |
| `--c-status-ok` | Trạng thái "đạt/đủ" | checklist xanh, `.stateOk` |
| `--c-selected` | Item đang được chọn trong danh sách/lịch | viền `.today` |

Có thể giữ cùng tông teal cho `--c-action` và `--c-nav-active` để giữ nhận diện, nhưng `--c-status-ok` và `--c-selected` phải tách sắc độ hoặc hình dạng riêng.

**Rủi ro:** đây là item rủi ro cao nhất tài liệu. Sửa `globals.css` ảnh hưởng **toàn bộ** app bao gồm 7 màn chưa audit (liệt kê ở mục 0). Không được đối xử như việc thường.

**Tiêu chí nghiệm thu:**
- [ ] Chụp screenshot baseline **toàn bộ** màn hình (5 đã audit + 7 chưa audit), cả light lẫn dark mode, trước khi sửa dòng CSS đầu tiên.
- [ ] Chạy visual regression sau khi sửa; mọi khác biệt phải giải thích được là cố ý, không có regression ngoài ý muốn.
- [ ] Grep toàn repo: không còn chỗ nào dùng trực tiếp `--c-green` hoặc hardcode `#18a5a7`.
- [ ] Mỗi token mới đạt WCAG AA với nền của nó ở cả 2 mode.
- [ ] Triển khai sau feature flag, có thể tắt về token cũ trong 1 lần deploy.
- [ ] Kiểm tra thủ công 7 màn chưa audit — mục tiêu là không hỏng, không phải cải thiện.

**Ticket:** `FE-11` · Ước lượng: 4–6 ngày (gồm cả baseline + kiểm tra 12 màn) · Phụ thuộc: **DEC-01 phải RESOLVED**

### 3.2 Khối "Tuần của bạn" nhầm vai trò: tuân thủ ghi log ≠ thời khóa biểu (màn E)

**Vấn đề gốc:** tiêu đề trong code là "Mức độ ghi nhận" (`weekly/page.tsx:57`) và đơn vị `slots.size}/4 bữa` — đây là **chỉ số tuân thủ ghi log**, không phải thực đơn được kê. Phải chốt đúng vai trò này trước khi quyết định có hiện tên món hay không.

**Bằng chứng code:**
- 4 chấm mỗi ngày (`.dots i`) chỉ có 2 trạng thái nhị phân qua class `done`/không — không phân biệt khung bữa nào thiếu, không phân biệt "chủ động báo bỏ" và "chưa ghi".
- Highlight "hôm nay" (`.day.today`) so `day.iso === new Date().toISOString().slice(0,10)` — **so ngày UTC thô, không chuẩn hoá timezone**. Với người dùng ở GMT+7, từ 00:00 đến 07:00 giờ VN hệ thống sẽ highlight nhầm sang ngày hôm trước.
- Ngưỡng "đủ dữ liệu" lặp ở 2 nơi: dòng 51 dùng `activeDays>=5`, dòng 59 (`Insight`) dùng `activeDays<5` — cùng ngưỡng nhưng người dùng thấy "1/7 ngày" ở thẻ trên và "5 ngày" ở gợi ý dưới, không có câu nối 2 số.

**Đề xuất (giữ nguyên hướng đã thống nhất):**
1. **Không hiện tên món ở lưới 7 ngày.** Lưới trả lời "tuần này ghi đều không", không phải "hôm nào ăn gì".
2. Nâng cấp 4 chấm/ngày thành có nghĩa:
   - Gắn cố định theo khung bữa (sáng · trưa · phụ · tối), có nhãn/icon nhỏ phân biệt vị trí.
   - 4 trạng thái phân biệt bằng cả hình dạng lẫn màu: đã ghi · chủ động báo bỏ · chờ đối chiếu · chưa ghi.
   - **Lưu ý kích thước:** ở cỡ 8–10px, ký hiệu ✓ và ⚠ sẽ nhòe thành hai đốm giống nhau. Dùng khác biệt thô hơn ở cỡ này — tô đặc / viền rỗng / gạch chéo / để trống — rồi mới cộng màu. Ký hiệu chi tiết để dành cho tooltip và panel.
   - Tách riêng trạng thái "chờ đối chiếu" để con số ở thẻ trên cùng truy vết được về đúng ngày.
3. **Tầng 2 — chạm vào 1 cột ngày** → mở panel bên dưới (chỗ khoảng trắng đang lãng phí) hiện chi tiết ngày đó: 4 bữa, tên món, gram, trạng thái đối chiếu. Chỉ 1 ngày tại 1 thời điểm. Đây là đường đi **chính** để xem tên món.
4. **Tooltip chỉ là bổ trợ cho desktop.** Hover không tồn tại trên mobile và chấm 8px dưới ngưỡng chạm 44px — nếu chỉ dựa vào tooltip, người dùng điện thoại sẽ không bao giờ tới được thông tin đó.
5. Sửa "hôm nay" thành "ngày đang mở" — highlight đổi ý nghĩa từ "ngày quan trọng nhất" (sai) thành "ngày đang xem chi tiết" (đúng). Đồng thời sửa lỗi timezone UTC.
6. Gộp 2 ngưỡng thành 1 constant dùng chung, copy nối rõ: "Đã ghi X/7 ngày — cần tối thiểu 5/7 để có xu hướng đáng tin".
7. Nếu cần khối "thời khóa biểu" (thực đơn kê theo ngày), đó là **component riêng đặt ở màn "Hôm nay"** (`/patient`), không nhồi vào lưới tuần. Bố cục đề xuất: trục thời gian dọc, cột giờ nằm ngoài card làm xương sống, mỗi bữa một trạng thái riêng, chỉ bữa sắp tới có nút hành động.

**Tiêu chí nghiệm thu:**
- [ ] Có mockup được duyệt trước khi code (`[cần thiết kế trước]`).
- [ ] Test timezone: giả lập 01:00 giờ VN → highlight đúng ngày hiện tại theo giờ địa phương, không lệch sang hôm trước.
- [ ] 4 trạng thái phân biệt được khi in đen trắng (chứng minh không chỉ dựa vào màu).
- [ ] Vùng chạm mỗi cột ngày ≥ 44×44px trên mobile.
- [x] Đường đi xem tên món hoạt động — **đã làm mục 3 riêng (2026-08-15), theo yêu cầu trực tiếp của người dùng, bỏ qua gate `[cần thiết kế trước]`/`DEC-01` một cách có chủ ý cho đúng phạm vi này.** Bấm vào 1 cột ngày (`<button>`, có `aria-expanded`/`aria-controls`) mở `DayDetail` bên dưới lưới, đúng ngày đó, 4 cột bữa sáng/trưa/phụ/tối, mỗi món hiện tên + gram + trạng thái ("Đã tính vào tổng"/"Chờ đối chiếu"/"Đã báo bỏ bữa"). Xác nhận bằng browser thật trên dữ liệu demo. **Chưa làm mobile touch target ≥44px cho nút ngày** — cần đo lại.
- [ ] Ngưỡng 5/7 khai báo 1 chỗ duy nhất; grep không còn magic number `5` rời rạc trong file.
- [ ] Con số "chờ đối chiếu" ở thẻ tổng bằng đúng tổng các chấm trạng thái tương ứng trong lưới.
- [x] Điều hướng bàn phím: cột ngày giờ là `<button>` thật (trước là `<article>`) — tự động có Tab/Enter/Space qua semantics HTML chuẩn, không cần code tay; `:focus-visible` đã có từ `FE-19`. Chưa test Esc để đóng panel.

**Trạng thái:** mục 3 (tầng 2 xem món) đã làm; mục 1, 2, 4, 5, 6, 7 (4 chấm có nghĩa, sửa timezone, đổi ý nghĩa "hôm nay"→"đang mở", gộp ngưỡng, component thời khóa biểu riêng ở "Hôm nay") **vẫn chưa làm**, vẫn cần mockup + `DEC-01` trước khi làm phần còn lại của `FE-12` — không coi đây là đã mở khoá toàn bộ ticket.

**Ticket:** `FE-12` (một phần) · Ước lượng phần còn lại: 5–7 ngày · Phụ thuộc: DEC-01, FE-11 · `[cần thiết kế trước]` (vẫn áp dụng cho phần chưa làm)

### 3.3 Ngôn ngữ thiết kế bệnh nhân trùng ngôn ngữ chuyên gia

Cả `/patient/**` và `/dietitian/**` dùng chung `globals.css`, cùng mật độ card/stat, cùng token màu. Hệ quả trực tiếp của §3.1 cộng việc chưa có design system riêng cho patient.

**Không lập ticket riêng** — đây chính là nội dung của `DEC-01`. Chốt DEC-01 trước, kết quả sẽ định hình lại phạm vi FE-11 và FE-12.

---

## 4. P2 — Rò rỉ thuật ngữ kỹ thuật / thiếu phân cấp thị giác

### 4.1 Thuật ngữ kỹ thuật lộ ra UI lâm sàng

**Bằng chứng code:**
- `meal-plans/new/page.tsx:164`: text cứng "Backend chọn món và gram... giao diện không tự suy đoán" hiện thẳng cho dinh dưỡng viên.
- `food-logs/page.tsx:55`: `{item.matched_on}` (field kỹ thuật kiểu "token") không có nhãn giải thích.
- `meal-plans/new/page.tsx:200` (`MealSlot`): `{item.source_ref||item.source||'Nguồn backend'}` — nếu `source_ref` dạng `dish:NIN-PHO-BO-TAI`, hiện nguyên văn dưới tên món tiếng Việt.

**Đề xuất:** đổi implementation-note sang ngôn ngữ nghiệp vụ ("Số liệu được hệ thống tính lại tự động, đã kiểm tra chuẩn"); map `matched_on` sang nhãn dễ hiểu theo enum thực tế ("khớp theo tên món" / "khớp theo tên gọi khác"); `source_ref` hiện dạng rút gọn ("Nguồn: NIN 2017"), mã đầy đủ đưa vào tooltip/expand.

**Tiêu chí nghiệm thu:**
- [x] Đã sửa 3 vị trí đã biết: text implementation-note ở `meal-plans/new` (giờ "Số liệu dinh dưỡng luôn được tính lại chính xác"), `matched_on` map sang tiếng Việt qua `MATCH_REASON_LABEL` (có fallback về giá trị gốc), `source_ref` chuyển vào `title` tooltip thay vì hiện thẳng, dòng chính hiện `item.source` (nhãn ngắn "Nguồn: NIN"...). Chưa grep lại toàn bộ `/dietitian/**`+`/patient/**` để đảm bảo hết sạch — chỉ đã sửa các chỗ audit trước đó phát hiện.
- [x] Enum `matched_on` xác nhận từ `src/clinical/matching.py:112` (`"exact"|"alias"|"token"`, đối chiếu `tests/test_matching.py`) — trả lời được `Q6` ngay từ code trong cùng monorepo, không cần chờ backend riêng. Cả 3 giá trị đã có nhãn tiếng Việt + fallback về chuỗi gốc cho enum mới.
- [x] RULE-2 vẫn thỏa: `source_ref` đầy đủ vẫn còn trong DOM (`title` attribute), không xoá, chỉ đổi cách hiển thị chính.

**Ticket:** `FE-13` ✅ mục 4.1 đã làm (2026-08-15) · Ước lượng: 2 ngày

### 4.2 Mật độ trích dẫn nguồn không đồng đều giữa các món (màn D)

Chưa có bằng chứng code cụ thể — chưa trace tới trường `citation`/`source_ref` dài ở từng món. Cần kiểm tra dữ liệu seed trước khi lên ticket. Nếu xác nhận là thiếu dữ liệu, cần trạng thái rỗng rõ ràng ("Chưa có trích dẫn chi tiết") thay vì im lặng bỏ trống, đúng RULE-2.

**Ticket:** `FE-14` — `BLOCKED`, chờ R2/data xác nhận nguyên nhân. Chủ trì điều tra: data. Hạn: sprint kế.

### 4.3 Icon buổi ăn dùng sai ngữ nghĩa (màn D)

**Bằng chứng code** (`meal-plans/new/page.tsx`, `MealSlot`): `Icon name={slot==='snack'?'moon':slot==='dinner'?'bowl':'sun'}` — chỉ 3 icon cho 4 khung bữa, sáng và trưa cùng dùng `'sun'`.

**Đề xuất:** icon riêng cho `breakfast` khác `lunch`. Không dựa vào viền màu `--slot` để phân biệt vì đó là tín hiệu phụ.

**Tiêu chí nghiệm thu:** 4 khung bữa có 4 icon khác nhau; phân biệt được khi bỏ hết màu.

**Ticket:** `FE-13` ✅ đã làm (2026-08-15): `MEAL_ICON` — breakfast=`sun`, lunch=`bowl`, snack=`sparkle`, dinner=`moon`. Nhân tiện sửa luôn lỗi có sẵn: `moon` trước đó gán cho `snack` (15:30, giữa chiều) thay vì `dinner` (18:30) — giờ đúng ngữ nghĩa cho cả 4 khung, không chỉ tách breakfast/lunch. Build TypeScript pass; chưa chụp ảnh trực tiếp vì cần sinh 1 thực đơn demo mới có dữ liệu để render `MealSlot`.

### 4.4 Chip ràng buộc bị cắt xén ở màn hình hẹp (màn D)

**Bằng chứng code:** `.constraintCard>div{grid-template-columns:1fr 1fr}` dưới 1050px, chip `span` không có `text-overflow`/`white-space` an toàn.

**Tiêu chí nghiệm thu:** kiểm tra ở 360px, 768px, 1050px, 1440px — không chip nào bị cắt mất chữ. Chip dài tự xuống dòng hoặc ellipsis kèm tooltip đầy đủ.

**Ticket:** `FE-13` ✅ đã làm (2026-08-15): `min-width:0` + `overflow-wrap:break-word` trên `.constraintCard span` (fix chuẩn cho lỗi grid/flex item tràn khỏi cột do `min-width:auto` mặc định), icon trong chip cố định `flex:none` để không bị bóp méo. Build pass; chưa chụp ảnh trực tiếp (cần dữ liệu constraint thật để render card này).

### 4.5 Tin tốt và tin cần hành động có trọng lượng thị giác ngang nhau

**Bằng chứng code** (`weekly/page.tsx`): "BỎ BỮA" và "CHỜ ĐỐI CHIẾU" dùng chung `<article>`, chung `strong{font-size:30px}`. Cùng pattern ở màn C (3 thẻ thống kê đầu trang).

**Đề xuất:** thẻ "cần hành động" (CHỜ ĐỐI CHIẾU, BỆNH NHÂN CẦN CHÚ Ý) dùng màu nhấn + icon cảnh báo nhỏ; thẻ trung tính (BỎ BỮA: 0) giảm tông.

**Tiêu chí nghiệm thu:**
- [ ] Nhìn 2 giây, thẻ cần hành động phải là thứ được chú ý trước.
- [ ] Khi giá trị = 0, thẻ tự giảm tông (0 việc cần làm không nên trông như cảnh báo).
- [ ] Áp dụng cho cả `food-logs/page.tsx` và `weekly/page.tsx`.

**Ticket:** `FE-15` · Ước lượng: 1.5 ngày · Phụ thuộc: FE-11

### 4.6 Badge tĩnh trông giống nút bấm (nhiều màn)

**Bằng chứng code:** "Cần thêm dữ liệu" (`weekly/page.tsx`) là `<span>` không `onClick` nhưng style pill bo tròn. Cùng pattern với "Chưa gửi cho bệnh nhân" (`meal-plans/new/page.tsx:162`). Riêng "Đã có phương án" thực ra **là** nút thật chỉ đổi label — khác bản chất, cần style disabled rõ hơn thay vì chỉ đổi text.

**Đề xuất:** quy ước 2 style tách biệt — badge tĩnh (chữ nhật bo nhẹ, không hover) vs nút bấm (luôn có hover/active/disabled). "Quay về thực đơn hôm nay" (`Link` thuần) thêm gạch chân hoặc icon mũi tên rõ hơn.

**Tiêu chí nghiệm thu:**
- [ ] Có quy ước viết thành tài liệu trong `docs/`, không chỉ sửa từng chỗ.
- [x] Kiểm kê toàn app: mọi phần tử trông bấm được đều bấm được, và ngược lại — **một phần**. "Đã có phương án" (nút thật, đổi label) giờ tự động rõ ràng là không bấm được nhờ `FE-18` (rule `button:disabled` toàn cục), không cần sửa riêng ở đây. "Cần thêm dữ liệu" và "Quay về thực đơn hôm nay" (`weekly/page.tsx`) **chưa sửa** — cả hai thuộc phạm vi `FE-12` (redesign toàn màn "Tuần của bạn", đang khoá bởi `DEC-01`), sửa lẻ tẻ trước khi có mockup duyệt có nguy cơ phải làm lại.
- [x] Mọi link/nút đều có focus state — đã có từ `FE-19` (`:focus-visible` toàn cục dùng `!important`, không còn bị `outline:0` cục bộ chặn).

**Ticket:** `FE-13` — mục 4.6 còn thiếu quy ước bằng văn bản (xem khung dưới) và 2 vị trí thuộc `FE-12`.

**Quy ước badge tĩnh vs nút bấm (bổ sung 2026-08-15, áp dụng từ đây về sau):**
- Badge tĩnh (trạng thái, không tương tác): hình pill bo tròn `border-radius:999px`, không có `:hover`, không phải thẻ `<button>`/`<a>`. Ví dụ đúng: "Chưa gửi cho bệnh nhân", các badge trạng thái trong `followup.module.css`.
- Nút bấm (tương tác thật): luôn là `<button>`/`<a>`, có `:hover`, `:focus-visible`, và khi disabled dùng rule toàn cục ở `FE-18` (xám trung tính) — không đổi label để ngụy trang thành badge.
- Không dùng hình pill bo tròn cho phần tử có `onClick` thật lẫn phần tử tĩnh trong cùng 1 màn hình — nếu cả hai cùng xuất hiện, phải khác hình dạng rõ (badge = chữ nhật bo nhẹ, nút = pill hoặc có viền/nền rõ khi hover).

---

## 5. Accessibility — hạng mục mới, chưa có ở v1

Với phần mềm y tế, đây thường là yêu cầu tuân thủ chứ không phải nice-to-have. Hơi trớ trêu là §2.3 chính là một lỗi tương phản — phát hiện bằng mắt nhưng chưa hề chạy kiểm tra hệ thống.

**FE-19 — Audit accessibility cơ bản**

- [ ] Chạy axe-core hoặc Lighthouse a11y trên cả 12 màn (5 audit + 7 chưa audit), ghi lại điểm baseline.
- [ ] Toàn bộ cặp text/nền đạt WCAG AA (4.5:1 text thường, 3:1 text lớn và thành phần UI).
- [ ] Không có thông tin nào **chỉ** truyền tải bằng màu — áp dụng đặc biệt cho 4 trạng thái ở FE-12 và checklist ở FE-09.
- [ ] Điều hướng bàn phím đầy đủ: mọi hành động làm được bằng chuột đều làm được bằng bàn phím; thứ tự tab hợp lý; focus state nhìn thấy rõ.
- [ ] Vùng chạm ≥ 44×44px trên mobile.
- [ ] Form có label liên kết đúng; thông báo lỗi đọc được bằng screen reader.
- [ ] Cảnh báo lâm sàng (FE-09) có `role="alert"` để screen reader đọc ngay.

Chạy song song, không chặn ticket khác. Ước lượng: 2 ngày audit + thời gian sửa tùy kết quả.

---

## 6. Mobile / responsive — hạng mục mới, chưa có ở v1

Toàn bộ v1 suy luận theo layout desktop; chỉ §4.4 nhắc breakpoint 1050px. Ứng dụng bệnh nhân gần như chắc chắn dùng chủ yếu trên điện thoại.

**FE-20 — Xác lập chiến lược responsive**

- [ ] Chốt breakpoint chuẩn cho toàn app, viết thành tài liệu.
- [ ] Kiểm tra 12 màn ở 360px, 390px, 768px, 1024px, 1440px.
- [ ] Không có hover-only interaction nào là đường đi duy nhất tới một chức năng (áp dụng trực tiếp cho tooltip ở FE-12).
- [ ] Nút chat "Trợ lý" + toggle dark mode `position:fixed` không đè nội dung ở màn hình nhỏ hoặc trang dài (`experience-tools.module.css`).
- [ ] Bảng và lưới nhiều cột có phương án xuống dòng hoặc cuộn ngang có chủ đích, không cắt cứng.

**Cần dữ liệu:** tỷ lệ mobile/desktop thực tế ở không gian bệnh nhân. Nếu > 60% mobile, FE-20 nâng lên P1 và FE-12 phải thiết kế mobile-first.

Ước lượng: 2 ngày audit + sửa tùy kết quả.

### Kết quả audit (2026-08-15) — đã kiểm tra bằng browser thật, không suy đoán

**Kiểm kê breakpoint hiện có:** grep toàn `web-next/src` ra **39 giá trị `@media(max-width:...)` khác nhau** (360→1350px), gần như không trùng nhau, không theo thang chuẩn nào — xác nhận đúng nhận định "chưa có breakpoint chuẩn". Đề xuất thang chuẩn 5 mức khớp với các giá trị đã dùng nhiều nhất: `560 / 700 / 900 / 1050 / 1250px`. **Chưa refactor 39 chỗ này** — việc đó có rủi ro tương đương `FE-11` (đổi CSS toàn cục), nên tách thành việc riêng, không làm vội trong lượt audit này.

**Đã sửa (build pass + kiểm chứng bằng browser headless thật, không phải suy đoán):**
- ✅ Tràn ngang `.audit-row`/`.audit-row-selectable` (trang `reviews`) ở 700–1050px: grid 6 cột cố định cần tối thiểu 788px nhưng breakpoint xuống 1 cột cũ chỉ có ở `≤700px`, để hở khoảng 700–1050px luôn vỡ layout (`scrollWidth` 825px/1107px tại viewport 768px/1024px, đo được chính xác). Dời breakpoint lên `≤1050px` — hết tràn ở cả 5 mức đã test.
- ✅ Nút "Trợ lý" + dark-mode đè nội dung cuối trang khi cuộn hết (trường hợp "trang dài" nêu trong nhận xét gốc): thêm `padding-bottom:90px` cho `body` — nội dung thật không còn nằm dưới nút khi cuộn tới cuối.

**Đã sửa thêm (2026-08-15, sau khi người dùng chụp ảnh xác nhận trực tiếp thấy nút che nút "Mở bản đã lưu" ở `meal-plans/new`):**
- ✅ Nút "Trợ lý"/dark-mode đè nội dung tự nhiên ở góc dưới-phải kể cả không cuộn. Quyết định hướng sửa (không còn "chờ quyết định"): (1) `.launch` mặc định thu về icon-only 48px tròn (trước là pill 116px), chỉ mở rộng hiện chữ "Trợ lý" khi `:hover`/`:focus-visible`; (2) `.launchers` giảm còn `opacity:.55` khi không tương tác, về `1` khi hover/focus — nội dung phía sau đọc xuyên qua được thay vì bị che hoàn toàn. Xác nhận bằng browser thật: chữ "Mở bản đã lưu" đọc được rõ qua 2 nút tròn bán trong suốt.

**Còn thiếu:**
- Chưa kiểm tra hover-only interaction (chưa có gì để kiểm — tooltip đề xuất trong `FE-12` chưa được code).
- Chưa kiểm 9 màn còn lại trong 12 màn phạm vi (mới test `food-logs`, `meal-plans/new`, `reviews`).

---

## 7. Kiểm chứng người dùng — hạng mục mới

Toàn bộ tài liệu dựa trên đánh giá chuyên gia (2 vòng UX review + trace code). Chưa có kiểm chứng với người dùng thật. `FE-12` là redesign lớn màn bệnh nhân — làm xong rồi mới phát hiện sai sẽ đắt hơn nhiều so với test trước.

**FE-21 — Usability test rút gọn trước FE-12**
- 3–5 dinh dưỡng viên thật, 3–5 bệnh nhân thật, mỗi buổi 20–30 phút trên mockup (chưa cần code).
- Nhiệm vụ kiểm chứng: "tuần này bạn ghi được mấy bữa", "thứ Ba bạn ăn gì", "bữa nào đang chờ chuyên gia xác nhận", "ghi bữa chiều nay".
- Tiêu chí đạt: ≥4/5 người hoàn thành mỗi nhiệm vụ không cần gợi ý.

Làm trước khi code FE-12. Ước lượng: 3 ngày gồm tuyển người và tổng hợp.

---

## 8. Metric thành công

Không đo được thì không biết có tốt lên hay không. Ghi baseline **trước** khi bắt đầu sprint.

| Hạng mục | Metric | Baseline | Mục tiêu |
|---|---|---|---|
| FE-09 | Tỷ lệ ca có cảnh báo thuốc bị duyệt mà không xem chi tiết | chưa đo | giảm rõ rệt |
| FE-09 | Số lần override + tỷ lệ có lý do hợp lệ | chưa có | 100% có lý do |
| BE-01 | Tỷ lệ nhóm ứng viên có score trùng nhau | chưa đo | ~0 |
| FE-12 | Tỷ lệ bệnh nhân ghi ≥5/7 ngày/tuần | chưa đo | tăng |
| FE-12 | Số lần mở panel chi tiết ngày | chưa có | có sử dụng thật |
| FE-19 | Điểm Lighthouse a11y | chưa đo | ≥90 mọi màn |
| Chung | Thời gian trung bình duyệt 1 thực đơn | chưa đo | không tăng |

Metric cuối là **guardrail**: nếu cải thiện an toàn làm chuyên gia chậm đi đáng kể, cần xem lại thiết kế chứ không chấp nhận mặc định.

---

## 9. Câu hỏi mở — cần trả lời, có chủ, có hạn

| # | Câu hỏi | Chủ trì | Hạn | Trạng thái |
|---|---|---|---|---|
| Q1 | Tách design system riêng cho patient? (DEC-01) | R3 | trước sprint kế | OPEN |
| Q2 | Ngưỡng nghiêm trọng nào chặn duyệt, ai override được? (DEC-02) | R2 | trước FE-09 | OPEN |
| Q3 | Hàng chờ thực tế dài bao nhiêu ở P95? (DEC-03) | R2 + data | sprint này | OPEN |
| Q4 | Tỷ lệ mobile/desktop ở không gian bệnh nhân? | data | sprint này | OPEN |
| Q5 | Trích dẫn nguồn thiếu là do data hay do cố ý? (FE-14) | data | sprint kế | OPEN |
| Q6 | Enum `matched_on` có những giá trị nào? | backend | trước FE-13 | OPEN |

---

## 10. Thứ tự triển khai

**Sprint 1 — an toàn lâm sàng + chốt quyết định**
1. Chốt DEC-01, DEC-02, DEC-03 (chặn, làm trước)
2. `BE-01` — score trùng lặp (gốc rễ, đội backend)
3. `FE-09` — tách trạng thái checklist + nổi bật cảnh báo thuốc *(sau DEC-02)*
4. `FE-10` — mitigation score sát nhau
5. `FE-18` — trạng thái disabled
6. Ghi baseline metric + screenshot baseline 12 màn
7. `FE-19`, `FE-20` audit (song song, không chặn)

**Sprint 2 — nền tảng**
1. `FE-11` — refactor color token *(chỉ khi DEC-01 đã RESOLVED)*
2. `FE-21` — usability test trên mockup FE-12 (song song)
3. `FE-13` — dọn thuật ngữ kỹ thuật + badge/nút + icon + chip

**Sprint 3 — redesign**
1. `FE-12` — redesign weekly view *(sau FE-11, FE-21)*
2. `FE-15` — phân cấp stat card

**Sau đó:** `FE-14` (chờ Q5), `FE-16`, `FE-17` (polish).

**Cảnh báo về khối lượng:** FE-11 (4–6 ngày) + FE-12 (6–8 ngày) không lọt chung 1 sprint như v1 dự kiến. Đã tách thành 2 sprint riêng.

---

## 11. P3 — Polish

| # | Vấn đề | File | Ticket |
|---|---|---|---|
| 1 | Tab "Chờ duyệt/Tất cả quyết định/Đã duyệt/Từ chối" không song song | `reviews/page.tsx:129` | `FE-16` ✅ đổi thành "Chờ duyệt / Đã duyệt / Từ chối / Lịch sử" — dời "Lịch sử" ra cuối thay vì chen giữa 3 tab trạng thái |
| 2 | Stepper 2 tầng nhãn khó đọc lướt | `meal-plans/new/page.tsx:151` | `FE-16` ✅ đổi nhãn trạng thái sang 1 bộ từ vựng nhất quán ("Hoàn tất/Chờ tạo/Sẵn sàng tạo/Chờ duyệt/Chưa tới" thay vì trộn quá khứ/điều kiện/vị trí) |
| 3 | Nút "Tạo phương án" lệch baseline với dropdown | `meal-plans/new/page.tsx` CSS | Kiểm tra lại code hiện tại: nút và dropdown đã nằm ở 2 hàng riêng (`.generateRow` tách khỏi `.briefControls`), không còn chung hàng như mô tả gốc — coi như đã hết hiệu lực, không cần sửa. |
| 4 | Nút chat + dark-mode toggle fixed đè nội dung | `experience-tools.module.css` | ✅ đã sửa trong `FE-20` |
| 5 | Font serif/sans gán rời rạc không theo hệ thống | `globals.css` | `FE-17` ✅ đã làm (2026-08-15). Kiểm kê 16 file CSS module: `--f-serif` đã được dùng nhất quán cho h1/h2/h3/số liệu lớn — đây thực ra **đã là quy ước ngầm định**, không phải hỗn loạn hoàn toàn. Ngoại lệ duy nhất: lớp `.page-title` dùng chung trong `globals.css` (chỉ 2 trang dùng: `reviews`, `eval`) đặt sai thành sans. Sửa `.page-title` theo quy ước đa số (đổi 1 chỗ, ảnh hưởng 2 trang) thay vì đổi ngược 16 file — rủi ro thấp hơn nhiều so với lo ngại ban đầu (không cần mức thận trọng như `FE-11`, vì `FE-11` không có quy ước đa số sẵn có để hội tụ về). Xác nhận bằng browser thật: heading "Hàng chờ & nhật ký phê duyệt" đã chuyển sang serif. |
| 6 | Layout radio 2 cột lẻ hàng cuối khi 5 lựa chọn | `food-logs/page.tsx` | `FE-16` ✅ CSS `label:last-child:nth-child(odd){grid-column:1/-1}` — item lẻ cuối cùng tự giãn hết chiều ngang thay vì trôi dạt bên trái |
| 7 | Khoảng trắng thừa dưới hàng chờ, thiếu empty-state | `reviews/page.tsx` | Kiểm tra lại code hiện tại: empty-state đã tồn tại sẵn (`visible.length===0` → tiêu đề + mô tả hướng dẫn), xác nhận bằng browser thật không tái hiện được vấn đề với dữ liệu demo đầy — có thể đã được thêm sau khi bản audit gốc viết. Không cần sửa thêm. |
| 8 | ~~Thiếu chỉ báo ưu tiên trên dòng hàng chờ~~ | `reviews/page.tsx` | **chuyển thành DEC-03**, không để ở P3 |

---

## 12. Nhắc cho agent thực thi

- Trước bất kỳ ticket nào đụng ngưỡng cảnh báo lâm sàng (`FE-09`) hoặc luồng dữ liệu bệnh nhân (`FE-12`), xác nhận lại với R2 theo mục 6 của `CLAUDE.md`. **Không tự đặt ngưỡng nghiêm trọng nào chặn nút duyệt.**
- `FE-11` không được bắt đầu khi `DEC-01` còn `OPEN`.
- `FE-12` không được code khi chưa có mockup duyệt và chưa có kết quả `FE-21`.
- Mọi ticket phải pass hết checkbox tiêu chí nghiệm thu của chính nó trước khi mở PR.
- Gặp chỗ tài liệu này chưa nói rõ → dừng và hỏi, không tự suy đoán. Đặc biệt với ngưỡng lâm sàng và copy hiển thị cho bệnh nhân.
