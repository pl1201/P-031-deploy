# Mổ xẻ thiết kế VelaPath và phương án nâng cấp VNutriCare

> Ngày khảo sát: 2026-08-20  
> Website tham chiếu: <https://c4-velapath-059.duckdns.org/>  
> Phạm vi quan sát: landing page desktop/mobile, màn đăng nhập Patient Web và Nurse Web công khai. Các màn sau đăng nhập không được truy cập.  
> Mục tiêu: học nguyên tắc thiết kế, không sao chép thương hiệu, minh họa hoặc bố cục nguyên bản.

## 1. Kết luận nhanh

VelaPath mạnh nhất ở **câu chuyện sản phẩm và cảm giác được chăm sóc**, không phải ở dashboard dữ liệu. Thiết kế tạo niềm tin bằng bốn lớp:

1. Một thông điệp cảm xúc rất rõ.
2. Minh họa con người và bối cảnh gia đình nhất quán.
3. Mỗi khu vực chỉ có một ý chính và một hành động chính.
4. An toàn, vai trò và giới hạn AI được diễn đạt bằng ngôn ngữ thông thường.

VNutriCare không nên đổi toàn bộ sang phong cách landing page này. Web của chúng ta là ứng dụng dinh dưỡng lâm sàng đã đăng nhập, có hai nhóm người dùng khác nhau:

- Bệnh nhân cần đơn giản, nhẹ nhàng, hành động rõ.
- Chuyên gia cần mật độ thông tin, truy vết và xử lý nhanh.

Hướng phù hợp là **“Warm clinical editorial”**: lấy nhịp kể chuyện, sự ấm áp, phân cấp nội dung và progressive disclosure của VelaPath; giữ bảng màu xanh dương VNutriCare, dữ liệu thật, Safety Gate và tính vận hành của dashboard hiện tại.

## 2. Design DNA của VelaPath

### 2.1. Ý tưởng trung tâm

Thông điệp xuyên suốt là “hồi phục tại nhà nhưng không đơn độc”. Mọi thành phần đều phục vụ thông điệp này:

- Hình người bệnh lớn tuổi trong không gian gia đình.
- Điện thoại luôn hiển thị việc nhỏ có thể hoàn thành.
- Đường cong nối nhà – bệnh viện – đội ngũ chăm sóc.
- Tiến độ 14 ngày thay vì các dashboard chỉ số trừu tượng.
- Câu chữ tránh thuật ngữ kỹ thuật.

Điểm đáng học: thiết kế không bắt người dùng hiểu sản phẩm trước; nó cho người dùng thấy một ngày sử dụng trông như thế nào.

### 2.2. Hệ màu

Các token quan sát được:

| Vai trò | Màu |
|---|---|
| Ink | `#191c1d` |
| Muted text | `#3e4948` |
| Border | `#bdc9c7` |
| Canvas | `#f8fafa` |
| Brand teal | `#00645f` |
| Brand deep | `#00504c` |
| Navy | `#183b56` |
| Blue tint | `#e7f2fc` |
| Urgent | `#ba1a1a` |
| Review | `#b54708` |
| Routine | `#00663c` |
| Done | `#41617e` |

Nguyên tắc:

- Nền trung tính chiếm phần lớn diện tích.
- Teal chỉ nhấn CTA, trạng thái tích cực và các điểm kết nối.
- Navy dành cho khu vực an toàn/nguyên tắc quan trọng.
- Peach và xanh nhạt tạo nhịp cảm xúc giữa các section.
- Màu cảnh báo tách biệt với màu thương hiệu.

Đây là điểm VNutriCare nên giữ: màu macro, màu thương hiệu và màu rủi ro lâm sàng phải là ba hệ khác nhau.

### 2.3. Typography

Landing dùng Inter/system sans:

- `h1`: khoảng 53px, weight 700, line-height khoảng 1.08.
- `h2`: khoảng 40px, weight 700.
- Body: khoảng 15–16px, line-height khoảng 1.6 ở lead.
- Eyebrow: uppercase, tracking rộng, màu brand.
- CTA: khoảng 14px, weight 800.

Điểm mạnh:

- Heading ngắn, tương phản kích thước mạnh.
- Dòng xuống có chủ đích.
- Eyebrow giúp người đọc biết ngữ cảnh trước khi đọc tiêu đề.

Điểm chưa tốt:

- Body desktop khoảng 15px hơi nhỏ với nhóm người bệnh lớn tuổi.
- Một số đoạn chữ phụ trong mockup điện thoại quá nhỏ nếu coi là nội dung thật.
- Weight CTA 800 hơi nặng.

VNutriCare nên giữ Plus Jakarta Sans hiện tại thay vì sao chép Inter. Scale 16px body và 12px tối thiểu của chúng ta phù hợp hơn với người dùng non-tech.

### 2.4. Layout và nhịp trang

Landing desktop dài khoảng 14.188px, gồm 17 section; mobile dài khoảng 16.737px.

Nhịp chủ đạo:

```text
Hero cảm xúc
→ giới thiệu sản phẩm bằng mockup
→ ba lời hứa tin cậy
→ sứ mệnh
→ video
→ ba bước sử dụng
→ hành trình 14 ngày
→ nhập liệu đơn giản
→ an toàn
→ tiến bộ
→ khác biệt
→ kết nối bệnh nhân/đội ngũ
→ bệnh viện
→ privacy
→ CTA
→ FAQ
```

Mỗi section thường có:

- Eyebrow.
- Heading hai dòng.
- Một đoạn giải thích ngắn.
- Một minh họa hoặc mockup lớn.
- Tối đa hai CTA.

### 2.5. Composition

- Hero chia 2 cột, copy trái – minh họa phải.
- Các điện thoại được đặt lệch cao thấp để tạo chiều sâu.
- Section alternates giữa trắng, mint, blue tint, peach và navy.
- Đường cong và blob đóng vai trò liên kết hành trình.
- Card ít viền, nhiều khoảng thở; shadow chỉ dùng cho phone/CTA.
- Mobile biến mọi composition phức tạp thành một dòng kể chuyện dọc.

### 2.6. Motion

Các cơ chế quan sát từ DOM/CSS hook:

- `data-reveal`: section reveal khi đi vào viewport.
- `data-parallax`: mockup điện thoại dịch chuyển với tốc độ khác nhau.
- `data-draw`: đường cong được vẽ theo tiến trình.
- Dot tiến độ có animation delay nối tiếp.
- Video có nút âm thanh và poster rõ.
- Theme/lang được áp trước hydration để tránh nháy giao diện.

Điểm đáng học: motion gắn với ý nghĩa “hành trình/tiến độ”, không chỉ trang trí.

### 2.7. Responsive

Desktop:

- Header đầy đủ điều hướng, theme, ngôn ngữ, đăng nhập, CTA.
- Hero và phần giải thích dùng 2–3 cột.
- Mockup điện thoại được bố trí như poster.

Mobile:

- Header thu về logo, theme/lang và nút menu.
- CTA hero xếp full-width.
- Minh họa xuống dưới copy.
- Các bước chuyển thành sequence dọc 01/02/03.
- Hai phía “tại nhà / đội ngũ” chuyển thành stack có đường nối.
- Footer chuyển thành các nhóm link dọc.

Mobile không chỉ co desktop; nó kể lại cùng câu chuyện theo thứ tự đọc tự nhiên.

## 3. Đánh giá từng bề mặt

## 3.1. Landing page

### Điểm tốt

- Value proposition rõ ngay màn đầu.
- Hình minh họa có bản sắc và phù hợp đối tượng.
- Product mockup xuất hiện sớm, không bắt người dùng tưởng tượng.
- CTA chính/phụ nhất quán.
- Nội dung an toàn và giới hạn AI được nói rõ.
- Section màu tạo nhịp mà không cần quá nhiều card.
- Mobile có chất lượng gần desktop.

### Điểm yếu

- 17 section là quá dài; nhiều phone mockup lặp lại cùng nội dung.
- Một số thông điệp “đồng hành/an toàn” được nhắc nhiều lần.
- Header desktop chứa nhiều control và link nhỏ.
- Cùng một mockup “Hôm nay của bạn” xuất hiện quá thường xuyên.
- Phần video chiếm diện tích lớn nhưng phụ thuộc media tải thành công.
- Landing đẹp nhưng có nguy cơ làm người xem mệt trước CTA cuối.

Đánh giá: **8,5/10 về storytelling; 7/10 về hiệu quả thông tin**.

## 3.2. Patient sign-in

### Điểm tốt

- Hai cột cân bằng: cảm xúc bên trái, tác vụ bên phải.
- Minh họa nối trực tiếp với ngữ cảnh sau xuất viện.
- Form rộng, input cao, CTA rõ.
- Ghi nhớ đăng nhập được giải thích bằng ngôn ngữ an toàn.
- Activation flow được đặt đúng cạnh đăng nhập.
- Gradient/curve nền mềm nhưng không làm mất tập trung.

### Điểm yếu

- Mascot nằm “thò” trên card dễ tạo cảm giác sản phẩm trẻ em nếu dùng quá nhiều.
- Nhãn “PATIENT WEB” là thuật ngữ nội bộ, không cần cho bệnh nhân.
- Password icon mascot không trực quan bằng eye icon chuẩn.

Đánh giá: **8/10**.

## 3.3. Nurse sign-in

### Điểm tốt

- Rất trực tiếp và ít nhiễu.
- Có cảnh báo phiên tự khóa 15 phút.
- Form trung tâm rõ.

### Điểm yếu

- Không có logo/nhận diện VelaPath.
- Serif heading lệch hoàn toàn patient/landing.
- Khoảng trắng quá lớn nhưng không tạo cảm xúc hay ngữ cảnh.
- Không có help/recovery/security cues.
- Cảm giác giống màn prototype hơn sản phẩm cùng hệ thống.

Đánh giá: **5,5/10** và là ví dụ không nên mang sang VNutriCare.

## 4. So với VNutriCare hiện tại

| Khía cạnh | VelaPath | VNutriCare hiện tại | Hướng xử lý |
|---|---|---|---|
| Cảm xúc | Rất mạnh | Có welcome card nhưng còn thiên dashboard | Tạo một “daily care moment” rõ |
| Dữ liệu | Ít, chọn lọc | Nhiều macro/plan/review | Progressive disclosure |
| Minh họa | Hệ illustration riêng | Chủ yếu icon, ring, card | Thêm 2–3 artwork có mục đích |
| CTA | Một CTA chính/section | Một số màn có nhiều hành động cạnh tranh | Mỗi trạng thái một primary action |
| Layout | Editorial/storytelling | Dashboard/sidebar | Patient editorial, dietitian operational |
| Typography | Heading mạnh, body hơi nhỏ | Scale vừa được nâng | Giữ scale VNutriCare |
| Màu | Teal/mint/navy/peach | Blue + macro + clinical | Giữ blue, bổ sung warm neutrals |
| Motion | Theo hành trình | Có hover/welcome motion | Chỉ motion cho tiến độ và cập nhật |
| Safety copy | Plain language | Có nhưng rải rác | Gom theo đúng thời điểm quyết định |
| Responsive | Kể lại theo mobile | Có tabbar nhưng nhiều trang vẫn desktop-first | Thiết kế mobile state riêng |

## 5. Concept đề xuất cho VNutriCare

## “Bữa ăn hôm nay, một bước chăm sóc”

Một hệ editorial lâm sàng ấm áp:

- **Bệnh nhân:** yên tĩnh, thân thiện, từng bước, tập trung vào hôm nay.
- **Chuyên gia:** gọn, sắc nét, risk-first, phục vụ quyết định.
- **Điểm nối:** cùng token, cùng ngôn ngữ trạng thái, cùng provenance.

Điểm đáng nhớ của VNutriCare không nên là một mascot hay dashboard nhiều card, mà là **dải hành trình dinh dưỡng trong ngày**: kế hoạch → đã ăn → còn lại → chia sẻ khác biệt.

## 6. Phương án nâng cấp giao diện

## 6.1. Patient Home — ưu tiên cao nhất

### Cấu trúc mới

```text
1. Daily care header
   “Hôm nay mình chăm cơ thể bằng những bữa ăn vừa sức.”
   Ngày + thông báo nhẹ

2. Daily nutrition journey
   Đã ăn / Kế hoạch / Còn lại
   Macro tóm tắt, không mở toàn bộ chi tiết mặc định

3. Meal timeline
   Bữa hiện tại nổi bật
   Bữa đã ghi thu gọn
   Bữa sau chỉ hiện giờ + tên

4. One next action
   “Ghi lại bữa trưa” hoặc “Hôm nay đã đủ”

5. Honest logging prompt
   Ăn món khác · Ăn một phần · Bỏ bữa

6. Care news
   Tối đa 2 item có liên quan trong ngày
```

### Thay đổi cụ thể

- Welcome card hiện tại giảm chiều cao, bỏ cảm giác banner marketing.
- Calorie ring chuyển thành dải “đã ăn / kế hoạch / còn lại”; ring chỉ là visual phụ.
- Macro mặc định hiển thị 3 số ngắn; chi tiết mở bằng disclosure.
- Meal card giảm metadata lặp; trạng thái bằng động từ rõ: `Ghi lại`, `Đã ghi`, `Xem lại`.
- Bữa hiện tại có một accent rail; các bữa khác trung tính.
- “Bạn có ăn món khác...” thành một action sheet thay vì đoạn gợi ý cuối danh sách.
- Bản tin chăm sóc không chiếm card đậm; dùng danh sách editorial nhỏ ở cuối rail.

## 6.2. Nutrition Report

- Đổi tiêu đề từ báo cáo kỹ thuật sang “Nhìn lại dinh dưỡng của bạn”.
- Đặt completeness ngay dưới date picker, không chiếm card riêng bên phải.
- Khi thiếu dữ liệu, thay bảng chấm tròn bằng empty state có hành động: “Ghi thêm bữa để xem xu hướng”.
- Mỗi nutrient chỉ mở trend khi đủ dữ liệu; không hiển thị hàng “Chưa tính được” lặp sáu lần.
- Sidebar phải là “Điểm đáng chú ý” và “Bạn có thể làm gì tiếp”, không phải các card giải thích chung.
- Dùng chart chỉ khi có ít nhất 3 điểm hợp lệ; nếu không, dùng câu chữ.

## 6.3. Weekly Journey

Học từ section 14 ngày của VelaPath nhưng áp vào dinh dưỡng:

```text
Thứ 2 ─ Thứ 3 ─ Thứ 4 ─ Hôm nay ─ ...
  ✓       ✓       ○        ●
```

- Không dùng “streak” gây phán xét.
- Dùng “ngày có dữ liệu” thay vì “ngày thành công/thất bại”.
- Highlight một insight có ích: bữa nào thường bị bỏ, thời điểm nào ghi đều.
- Cho phép xem lại từng ngày từ timeline.

## 6.4. Food logging

- Chuyển thành wizard tối đa ba bước:
  1. Bạn đã ăn thế nào?
  2. Món/khẩu phần.
  3. Xác nhận.
- Bốn lựa chọn đầu tiên bằng plain language: đúng kế hoạch, một phần, món khác, bỏ bữa.
- Free text nằm sau “món khác”, không phơi input kỹ thuật ngay từ đầu.
- Sau submit có optimistic feedback và số kcal cập nhật tại chỗ.
- Không dùng màu đỏ cho bỏ bữa; đỏ chỉ dành cho safety.

## 6.5. Patient authentication/onboarding

- Áp bố cục 2 cột tương tự nguyên tắc VelaPath: giá trị/trấn an bên trái, form bên phải.
- Không sao chép minh họa. Tạo artwork riêng về bữa cơm gia đình Việt và chuyên gia đồng hành.
- Một heading: “Bắt đầu chăm sóc dinh dưỡng của bạn”.
- Demo role phải được ghi rõ là demo, không trộn với flow production.
- Mobile chỉ hiển thị logo + form + một câu trấn an; ẩn artwork lớn.

## 6.6. Dietitian workspace

Không áp phong cách minh họa mềm của patient vào màn chuyên gia.

- Giữ sidebar và density.
- Header gọn còn: tìm kiếm, notification, account; theme/lang vào menu cá nhân nếu không dùng thường xuyên.
- Queue dùng risk-first grouping P0/P1/P2 và SLA/time waiting.
- Patient 360 dùng một summary band thay vì nhiều tile nhỏ.
- Meal plan generation giữ flow ba bước nhưng tăng visual hierarchy, bỏ nhãn 8–10px còn sót.
- Review screen sticky action rail: Reject / Save edit / Approve.
- Citation và provenance xuất hiện cạnh finding, không dồn xuống cuối.
- Empty/loading/error state dùng cùng ngôn ngữ toàn hệ thống.

## 7. Design system đề xuất

### 7.1. Color

Giữ blue brand hiện tại, bổ sung nền ấm:

```css
--brand-600: #0069ad;
--brand-700: #00568c;
--ink-900: #292827;
--ink-700: #52504f;
--canvas: #f7f9f9;
--surface-warm: #fbf7f2;
--surface-care: #edf5f3;
--surface-info: #eaf3fb;
--line: #d9e0e2;

--macro-carb: #0072bc;
--macro-protein: #b02bc3;
--macro-fat: #d98700;

--risk-p0: #b42318;
--risk-p1: #a15c00;
--risk-p2: #41617e;
```

Không dùng gradient blue–purple generic. Mỗi trang chỉ có một màu surface chủ đạo và một màu accent.

### 7.2. Typography

- Giữ Plus Jakarta Sans Vietnamese.
- Body patient: 16px/1.6.
- Body chuyên gia: 14–16px tùy density, không dưới 12px.
- Page title: 32–38px patient; 28–32px dietitian.
- Section title: 24px.
- Card title: 18px.
- Eyebrow: 12px/600, tracking 0.06em; không quá 0.08em.
- Số liệu: sans + `tabular-nums`, không dùng monospace tràn lan.
- Weight tối đa thông thường 700.

### 7.3. Shape và elevation

- Page section: radius 24px.
- Functional card: radius 16px.
- Input/button: radius 12px; CTA pill chỉ dùng ở marketing hoặc filter chip.
- Border quan trọng hơn shadow.
- Shadow lớn chỉ dành cho overlay, drawer và hero artwork.

### 7.4. Motion

- Page load: stagger tối đa 240ms cho 3 vùng chính.
- Data update: number crossfade/short count, không bounce.
- Current meal: pulse một lần khi trạng thái đổi, không chạy vô hạn.
- Progress line có fill transition.
- Drawer 220–260ms.
- `prefers-reduced-motion` tắt toàn bộ transform/parallax.

## 8. Wireframe Patient Home

```text
┌───────────────────────────────────────────────────────────────┐
│ KHÔNG GIAN CHĂM SÓC                         Thứ Năm, 20/08   │
│ Hôm nay, mình ăn vừa đủ và ghi lại thật lòng.                 │
│ Một vài khác biệt nhỏ cũng giúp chuyên gia hiểu bạn hơn.      │
└───────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────┬────────────────────────┐
│ HÔM NAY                              │ TIẾP THEO              │
│ 820 đã ăn   2.643 kế hoạch  1.823 còn│ Ghi lại bữa trưa       │
│ ███████░░░░░░░░░░░░░░                │ 12:00 · Bánh chay       │
│ Carb 31%  Đạm 28%  Béo 26%           │ [Ghi bữa này]           │
├──────────────────────────────────────┴────────────────────────┤
│ 07:00  Bữa sáng                           ✓ Đã ghi             │
│ 12:00  Bữa trưa                           Ghi lại  →           │
│ 18:30  Bữa tối                            Sắp tới              │
│ 21:00  Bữa phụ                            Sắp tới              │
├───────────────────────────────────────────────────────────────┤
│ Không giống kế hoạch hôm nay?                                 │
│ [Ăn một phần] [Ăn món khác] [Bỏ bữa]                          │
└───────────────────────────────────────────────────────────────┘

BẢN TIN CHĂM SÓC
• Báo cáo tuần của bạn đã sẵn sàng                         →
• Kết nối thiết bị sức khỏe để bổ sung bước chân           →
```

Desktop dùng rail phải; mobile đưa “Tiếp theo” lên ngay sau summary, rồi timeline và action sheet.

## 9. Những thứ không nên sao chép

- Không đổi brand VNutriCare sang teal.
- Không dùng hình người già/băng chân nếu không đúng ngữ cảnh dinh dưỡng.
- Không đưa mockup điện thoại trang trí vào ứng dụng đã đăng nhập.
- Không tạo landing dài 17 section cho dashboard.
- Không lặp một CTA ở quá nhiều vị trí.
- Không dùng mascot trong mọi input/action.
- Không biến dietitian workspace thành giao diện pastel ít dữ liệu.
- Không dùng serif rời rạc như Nurse sign-in.
- Không dùng animation để che loading thật.

## 10. Lộ trình triển khai

### Phase 0 — Chốt visual direction, 1 ngày

- Duyệt concept “Warm clinical editorial”.
- Chốt token màu/type/shape/motion.
- Chụp baseline các trang patient/dietitian ở 1440, 900, 720, 390px.

### Phase 1 — Patient Home, 2–4 ngày

- Refactor `patient/page.tsx` thành daily summary + next action + timeline.
- Sửa calorie refresh và states đồng nhất.
- Responsive mobile riêng.
- Visual QA với tài khoản demo.

### Phase 2 — Report và Weekly, 2–3 ngày

- Gộp completeness vào header.
- Empty state có hành động.
- Weekly journey timeline.

### Phase 3 — Logging/auth/onboarding, 2–4 ngày

- Wizard logging.
- Auth hai cột desktop, một cột mobile.
- Onboarding giảm thuật ngữ kỹ thuật.

### Phase 4 — Dietitian consistency, 3–5 ngày

- Typography dưới 12px còn sót.
- Queue risk-first.
- Patient 360 và review action hierarchy.
- Đồng bộ login chuyên gia với design system.

### Phase 5 — QA, 2 ngày

- Keyboard/focus/screen reader.
- Contrast và 200% zoom.
- `prefers-reduced-motion`.
- Visual regression 4 breakpoint.
- Test loading/empty/error/long Vietnamese text.

## 11. File dự kiến chịu ảnh hưởng

- `web-next/src/app/globals.css`
- `web-next/src/components/workspace-shell.tsx`
- `web-next/src/components/calorie-ring.tsx`
- `web-next/src/components/macro-trio.tsx`
- `web-next/src/components/notification-bell.tsx`
- `web-next/src/app/patient/page.tsx`
- `web-next/src/app/patient/patient.module.css`
- `web-next/src/app/patient/diary/page.tsx`
- `web-next/src/app/patient/weekly/page.tsx`
- `web-next/src/app/patient/onboarding/page.tsx`
- `web-next/src/app/login/**`
- `web-next/src/app/dietitian/**`

## 12. Tiêu chí nghiệm thu

- Patient Home trả lời trong 5 giây: hôm nay ăn gì, đã ghi gì, bước tiếp theo là gì.
- Mỗi state chỉ có một primary CTA.
- Không có body text dưới 12px; patient body chính 16px.
- Không dùng màu đơn độc để truyền trạng thái.
- Mobile không tràn ngang ở 390px và 200% zoom.
- Calories/macros cập nhật ngay sau ghi bữa.
- Loading/empty/error không làm layout nhảy mạnh.
- P0/P1/P2 không trùng màu macro.
- Patient không thấy thuật ngữ workflow/agent/validator.
- Dietitian vẫn xem được provenance, finding và review actions trong một viewport hợp lý.

## 13. Thứ tự khuyến nghị

Không redesign toàn bộ cùng lúc. Làm một vertical slice hoàn chỉnh:

```text
Patient Home
→ ghi bữa
→ calories cập nhật
→ xem report trong ngày
→ responsive + accessibility
```

Sau khi slice này được duyệt bằng ảnh chụp thật, mới nhân design system sang Weekly, Onboarding và Dietitian. Cách này tránh tình trạng đổi màu/font hàng loạt nhưng trải nghiệm cốt lõi vẫn không rõ hơn.

