# Kế hoạch đưa VNutriCare từ bản demo lên production

Ngày cập nhật: 2026-08-13  
Người điều phối: R1 / Full-stack  
Người phê duyệt nội dung lâm sàng: R2

## Tài liệu này dùng để làm gì?

VNutiCare hiện đã có giao diện, backend, database và luồng sinh–duyệt thực đơn. Tuy nhiên, “chạy được” chưa đồng nghĩa với “đủ an toàn để một cơ sở y tế sử dụng thật”. Tài liệu này giải thích con đường từ trạng thái hiện tại đến production bằng ngôn ngữ dễ hiểu.

Năm tài liệu chuyên sâu vẫn được giữ lại để tra cứu:

- [Kế hoạch xử lý feedback mentor](./KE_HOACH.md) nói về cá nhân hóa, dữ liệu món ăn, nhiều phương án và giao diện.
- [Kế hoạch UX sinh thực đơn Việt Nam](./MEAL_GENERATION_VIETNAMESE_UX_PLAN.md) mô tả bữa sáng, mâm cơm, vai trò món và đơn vị bát/thìa.
- [Kế hoạch chăm sóc theo ngoại lệ](./MARKET_RESEARCH_EXCEPTION_BASED_CARE_PLAN.md) mô tả việc tái sử dụng thực đơn và báo cáo tuần.
- [Báo cáo R2 audit](./R2_AUDIT_EXCEPTION_BASED_CARE_RULES.md) quy định cách kiểm tra các luật dinh dưỡng và an toàn.
- [Kim chỉ nam trải nghiệm bệnh nhân](./PATIENT_EXPERIENCE_MASTER_PLAN.md) đặc tả chi tiết từng tính năng phía người dùng (F1–F8): luồng màn hình, mermaid, ràng buộc an toàn của mỗi tính năng.
- [Phân công toàn lộ trình và checkpoint](./PRODUCTION_ASSIGNMENT_MASTER_PLAN.md) chia bảy chặng dưới đây thành **10 checkpoint**, giao việc cho từng người theo vùng tệp để không giẫm chân nhau, kèm bằng chứng phải có ở mỗi cổng.
- 🆕 [Tổng hợp hội thảo t-DNA/DSF 16/08/2026](./docs/HOI_THAO_TDNA_DSF_2026-08-16.md) và [Kế hoạch tri thức lâm sàng R2](./docs/KE_HOACH_TRI_THUC_LAM_SANG_R2.md) — nguồn lâm sàng mới nhất, 17 khoảng trống tri thức và cách xử lý từng cái.

Tài liệu này ghép năm hướng trên thành một thứ tự triển khai chung. Ba mục trả lời trực tiếp câu hỏi “làm tính năng nào, làm lúc nào”: **Ứng dụng di động** (trong mục 4), **Nguyên tắc chọn ưu tiên tính năng** (mục 5) và **Danh mục tính năng gắn vào từng chặng** (mục 6).

---

## 1. Hiện tại hệ thống đang ở đâu?

Hệ thống hiện có thể làm được luồng cơ bản sau:

```text
Nhập hồ sơ bệnh nhân
        ↓
Tính mục tiêu dinh dưỡng
        ↓
Sinh thực đơn bằng CP-SAT, có thể dùng Gemini hỗ trợ
        ↓
Backend tính lại dinh dưỡng và kiểm tra an toàn
        ↓
Chuyên gia duyệt hoặc từ chối
        ↓
Bệnh nhân chỉ nhìn thấy thực đơn đã duyệt
```

Đây là nền móng đúng. Điểm tốt nhất là hệ thống không giao toàn bộ quyết định cho LLM. CP-SAT và code Python xử lý con số; LLM chỉ nên hỗ trợ chọn, xếp hạng hoặc diễn đạt món ăn. Chuyên gia vẫn là người quyết định cuối cùng.

Với kiến trúc này, project không cần viết lại từ đầu. Cần củng cố những phần còn yếu xung quanh lõi hiện có.

### 🆕 Định vị sản phẩm đã được xác nhận từ bên ngoài (17/08/2026)

Hội thảo *"Điều trị cá thể hoá cho người bệnh Đái tháo đường"* (Hà Nội, 16/08 — BV Nội tiết TW, Bạch Mai, Thanh Nhàn) trình bày **t-DNA — Transcultural Diabetes Nutrition Algorithm**: thuật toán dinh dưỡng đái tháo đường **thích ứng theo văn hoá địa phương**.

Đây gần đúng nguyên văn định vị của VNutriCare. Ba điều đáng chú ý:

- t-DNA đã được triển khai và kiểm chứng tại **Ấn Độ, Canada, Malaysia, Brazil, Mexico, Venezuela**, và **có bản Việt Nam** do Hội Nội tiết – Đái tháo đường Việt Nam phát hành. Đội không đang đi một con đường chưa ai đi.
- Kết quả công bố: **HbA1c giảm 1,1%** và **cân nặng giảm 6,9 kg** sau 6 tháng (Chee 2017, BMJ Open Diab Res Care).
- Bản t-DNA Việt Nam gồm 6 phần, trong đó **4 phần trùng đúng phạm vi sản phẩm đội đang xây**: chế độ ăn theo chiều cao/giới/mức lao động · thực đơn 7 ngày · bảng chuyển đổi thực phẩm · ghi chú nhật ký ăn uống.

Ý nghĩa thực tế cho lộ trình: phần khó nhất của một sản phẩm y tế — *chứng minh cách tiếp cận là hợp lý về lâm sàng* — đã có tiền lệ quốc tế để dẫn. Phần còn lại là làm cho đúng và đủ an toàn, tức đúng nội dung tài liệu này.

Chi tiết: [`docs/HOI_THAO_TDNA_DSF_2026-08-16.md`](./docs/HOI_THAO_TDNA_DSF_2026-08-16.md).

### Hệ thống đang dùng những thành phần nào?

```text
Next.js trên Vercel
    làm giao diện bệnh nhân và chuyên gia

FastAPI trên Render
    cung cấp API, đăng nhập và xử lý nghiệp vụ

PostgreSQL trên Supabase
    lưu hồ sơ, món ăn, thực đơn và lịch sử duyệt

LangGraph + CP-SAT + Gemini
    điều phối quá trình tạo và kiểm tra thực đơn
```

Đây được gọi là một “modular monolith”: backend vẫn là một ứng dụng lớn, nhưng bên trong được chia thành module rõ ràng. Với quy mô hiện tại, cách này phù hợp hơn microservice vì dễ vận hành và ít tốn chi phí.

---

## 2. Vì sao chưa thể gọi đây là production?

### Database hiện chạy được nhưng lịch sử migration chưa đáng tin cậy

Database thật đang ghi rằng nó ở phiên bản `c95f302a587e`, nhưng code hiện tại không có file migration tương ứng. Code cũng đang có hai đầu Alembic song song thay vì một đầu duy nhất.

Nói đơn giản: ngôi nhà đang đứng, nhưng bản vẽ ghi lại cách xây ngôi nhà bị thiếu vài trang. Nếu tạo một database mới từ đầu hoặc nâng cấp database sau này, quá trình có thể thất bại.

### Dữ liệu trong code và dữ liệu trên Supabase không giống nhau

Supabase đang có khoảng 7.403 thực phẩm và 2.747 món, trong khi file seed hiện tại chỉ có khoảng 547 thực phẩm và 100 món. Phần lớn món cũ trên Supabase là dữ liệu FNDDS, không phải món Việt đã được duyệt.

Điều nguy hiểm không nằm ở số lượng lớn hay nhỏ. Vấn đề là agent có lúc đọc CSV, API có lúc đọc database. Hai nơi có thể đưa ra hai câu trả lời khác nhau.

### Các luật lâm sàng vẫn chưa được xác minh

Các rule về carbohydrate, chất xơ, natri, protein, kali và tương tác thuốc vẫn còn trạng thái `to_verify`. Có nghĩa là code đã biết cách chạy rule, nhưng chuyên gia lâm sàng chưa xác nhận đầy đủ nội dung, đối tượng áp dụng và nguồn trích dẫn.

Vì vậy hệ thống có thể dùng để demo quy trình an toàn, nhưng chưa được phép tuyên bố một thực đơn là an toàn cho bệnh nhân thật chỉ dựa trên những rule này.

### Quyền đăng ký tài khoản còn một lỗ hổng

API đăng ký hiện cho client gửi role `patient` hoặc `dietitian`. Nếu giữ nguyên, một người có thể tự đăng ký thành chuyên gia. Production phải đổi sang cách: người dùng công khai chỉ đăng ký được tài khoản bệnh nhân; chuyên gia phải được admin hoặc tổ chức mời.

### Chưa có khái niệm tổ chức hoặc cơ sở y tế

Nếu hai phòng khám cùng mua sản phẩm, database hiện chưa có ranh giới rõ để nói bệnh nhân thuộc phòng khám nào và chuyên gia nào được xem hồ sơ nào. Đây là yêu cầu bắt buộc của sản phẩm B2B.

### Job sinh thực đơn có thể bị mất

Hiện việc sinh thực đơn chạy trong `BackgroundTasks` của chính FastAPI. Nếu Render restart, deploy phiên bản mới hoặc process bị dừng giữa chừng, job có thể biến mất.

Production cần một hàng đợi bền vững: API ghi nhận yêu cầu, worker riêng nhận việc, và nếu worker chết thì job vẫn còn để chạy lại.

### Chưa có dữ liệu theo dõi sau khi phát hành thực đơn

Các bảng `food_logs`, `patient_observations` và `clinical_notes` đã tồn tại nhưng gần như chưa có dữ liệu. Do đó ý tưởng báo cáo tuần hiện mới có cấu trúc, chưa có đủ đầu vào để đánh giá hiệu quả thực tế.

### 🆕 Thực đơn đạt ngưỡng cả ngày vẫn có thể dồn carbohydrate lệch bữa

Hệ thống hiện chỉ ràng buộc **tổng dinh dưỡng cả ngày**. Đây là quyết định kỹ thuật có lý do: bản đầu tiên chia định mức ngày cho 4 bữa theo tỉ lệ cố định rồi giải từng bữa riêng, và cách đó làm bữa nhỏ dễ vô nghiệm.

Nhưng hệ quả là hiện **không có ràng buộc nào về phân bố carbohydrate trong ngày**, trong khi hướng dẫn quốc tế coi *thời điểm nạp carbohydrate* quan trọng ngang *chất lượng* và *số lượng* — ADA 2026: *"consistent carbohydrate patterns may reduce hypoglycemia risk"*.

Ca lâm sàng trình bày tại hội thảo cho thấy điều này không phải lý thuyết: một bệnh nhân **HbA1c 9,1%** — tức đường huyết trung bình rất cao — **nhưng glucose lúc đói 3,6 mmol/L**, tức đang hạ đường huyết. Nguyên nhân là bỏ bữa rồi ăn bù ngẫu nhiên. Chỉ số trung bình đạt "cao" đã che mất các cơn hạ đường huyết, mà hạ đường huyết nặng liên quan tới **tăng gấp 1,8 lần nguy cơ tử vong**.

Một hệ thống chỉ tối ưu tổng ngày không phát hiện được kiểu vấn đề này. Ngưỡng phân bố cụ thể (sáng 20–25%, trưa 30–35%, phụ 5–10%, tối 30–35%) và cách cài đặt không lặp lại lỗi cũ được đặc tả ở [`docs/KE_HOACH_TRI_THUC_LAM_SANG_R2.md`](./docs/KE_HOACH_TRI_THUC_LAM_SANG_R2.md) §6.1.

### 🆕 Hồ sơ bệnh nhân chưa có chỉ số xét nghiệm nào

`PatientProfile` hiện có tuổi, giới, nhân trắc, bệnh đồng mắc, thuốc, dị ứng — nhưng **không có HbA1c**, không có đường huyết, mỡ máu hay vòng eo.

Điều này giới hạn "cá thể hoá" của sản phẩm ở mức nhân trắc và bệnh đồng mắc. Trong khi đó, **bước 1 của thuật toán t-DNA là phân tầng theo BMI *và* HbA1c**, và mục tiêu điều trị khác nhau tuỳ bệnh nhân: `< 7,0%` với người mới chẩn đoán, nhưng `< 7,5%` với người cao tuổi, có bệnh tim mạch hoặc từng hạ đường huyết.

> ⚠️ Có HbA1c trong hồ sơ **không** đồng nghĩa hệ thống được tự đặt mục tiêu điều trị. Đặt mục tiêu HbA1c cho một bệnh nhân cụ thể là quyết định của bác sĩ điều trị, không phải của phần mềm dinh dưỡng — đúng ranh giới `CLAUDE.md` §3. Giai đoạn đầu, các chỉ số này chỉ để **hiển thị cho chuyên gia** và **phân tầng cảnh báo**.

---

## 3. Sản phẩm production cuối cùng sẽ hoạt động ra sao?

### Lần đầu tạo thực đơn

Chuyên gia chọn bệnh nhân và yêu cầu tạo thực đơn. Worker lấy đúng phiên bản hồ sơ, dữ liệu món và rule đã được duyệt. CP-SAT tạo một hoặc vài phương án. Backend tự tính lại dinh dưỡng, kiểm tra dị ứng, tương tác và các ràng buộc. Sau đó chuyên gia duyệt một phiên bản cụ thể.

Quyết định duyệt phải gắn với:

- đúng bệnh nhân;
- đúng phiên bản món và số gram;
- đúng kết quả dinh dưỡng;
- đúng phiên bản hồ sơ và rule;
- người duyệt và thời điểm duyệt;
- thời hạn hiệu lực.

Nếu món hoặc gram thay đổi sau khi duyệt, hash sẽ thay đổi và quyết định duyệt cũ không còn áp dụng.

### Những lần sử dụng tiếp theo

Hệ thống không tạo một thực đơn mới rồi tự duyệt. Nhưng "tiếp tục áp dụng đúng thực đơn đã được duyệt" **không có nghĩa là bệnh nhân ăn y hệt một thực đơn suốt cả tuần** — đó chỉ là phương án đơn giản nhất khi chuyên gia không bật gì thêm. Có một tầng thứ hai, quan trọng hơn, để vừa giảm số lần phải duyệt vừa giữ được món ăn đa dạng.

Ngay sau khi duyệt thực đơn ngày đầu tiên, chuyên gia được hỏi có muốn mở một **phạm vi thay thế** cho ca này không — chọn một trong ba mức: ổn định, linh hoạt, hoặc linh hoạt cao, tương ứng với mức dao động dinh dưỡng cho phép và số ngày áp dụng. Nếu bật, mỗi đêm hệ thống tự tìm một tổ hợp món khác nằm trong **cả** ngưỡng lâm sàng gốc **lẫn** dải dao động đã chọn — nghĩa là món có thể đổi ngày này qua ngày khác, nhưng tổng dinh dưỡng luôn nằm trong phạm vi đã được duyệt trước. Kết quả này vẫn phải được backend tính lại từ đầu, không tin thẳng vào bộ giải; chỉ tự phát hành khi đồng thời còn hạn, không vi phạm ngưỡng nào, không có nguyên liệu nào chưa rõ nguồn, và chưa vượt số lần được phép tự động — thiếu một điều kiện thì rơi thẳng vào hàng chờ duyệt như bình thường.

Cơ chế tính toán cho tầng thứ hai này **đã có sẵn trong code** — bộ giải tương đương và bảng lưu phạm vi thay thế đều đã hoạt động, kể cả phần audit riêng cho mỗi lần tự động phát hành. Phần còn thiếu là ba việc thuộc về sản phẩm, không phải thuật toán: chưa có gì chạy mỗi đêm để thật sự gọi tới bộ giải đó, chưa có giao diện cho chuyên gia bật phạm vi thay thế hay cho bệnh nhân xem kết quả, và chưa có bảng nối một ngày cụ thể với đúng phiên bản thực đơn đang áp dụng cho ngày đó.

Bộ giải tương đương hiện chỉ lọc theo dị ứng và sở thích, **chưa lọc theo vùng miền**. Vùng miền chỉ được tôn trọng ở bước sinh thực đơn đầu tiên, nơi mô hình ngôn ngữ nhìn thấy vùng miền như một gợi ý trong văn bản; bước tự động sinh biến thể mỗi đêm hoàn toàn không đi qua mô hình ngôn ngữ nên gợi ý đó không có tác dụng. Một thực đơn gốc đúng vùng miền có thể bị đổi sang món trái vùng ở lần tự động kế tiếp mà không ai nhận ra. Đây là một điều kiện lọc còn thiếu, không phải một tính năng mới cần thiết kế lại.

Nếu một trong các yếu tố quan trọng — thuốc, dị ứng, bệnh lý, mục tiêu hoặc rule liên quan — thay đổi, hệ thống dừng tái sử dụng ở cả hai tầng và đưa ca đó về cho chuyên gia.

### Khi bệnh nhân ăn hằng ngày

Bệnh nhân ghi nhanh một trong các trạng thái: ăn đúng, ăn một phần, đổi món, bỏ bữa hoặc không nhớ rõ khẩu phần. Hệ thống giữ nguyên lời mô tả của bệnh nhân.

Nếu không có nguồn để đổi “một bát” hoặc “một thìa” thành gram, hệ thống phải nói chưa đủ dữ liệu. Nó không được tự đoán một con số để làm giao diện trông đầy đủ hơn.

Màn hình bệnh nhân dùng để làm việc này là một **thời khoá biểu bữa ăn** — lưới bốn buổi ăn nhân bảy ngày, đọc giống thời khoá biểu học sinh. Mỗi ô là một bữa, hiện luôn tên món nên nhìn là biết ăn gì, không phải bấm từng mục mới thấy nội dung. Bấm vào ô trống mở form ghi nhận đã điền sẵn đúng ngày và buổi, kể cả với ngày đã trôi qua.

Bệnh nhân có thể đính kèm ảnh bữa ăn. **Ảnh chỉ là bằng chứng để chuyên gia xem bằng mắt.** Hệ thống không nhận diện món trong ảnh, không dùng ảnh để huấn luyện mô hình, và khi hiển thị cho chuyên gia phải ghi rõ ảnh chưa được hệ thống xác minh nội dung. Quyết định này giữ nguyên phạm vi đã cắt trong `CLAUDE.md` mục 7; nếu sau này muốn làm thị giác máy tính, đó là một quyết định mở rộng phạm vi riêng, không lồng vào luồng ghi nhật ký.

### Khi bệnh nhân có câu hỏi

Bệnh nhân hỏi trong một khung chat duy nhất. Trợ lý tự động trả lời các câu hỏi an toàn — chủ yếu là diễn giải thực đơn đã duyệt, kèm nguồn số liệu. Trợ lý **không** được tự đổi món, tự tính lại dinh dưỡng hay tự phát hành thay đổi; nếu bệnh nhân muốn đổi món, trợ lý hướng dẫn gửi yêu cầu đi qua đúng luồng sinh và duyệt.

Khi câu hỏi vượt ranh giới chuyên môn hoặc có dấu hiệu nguy hiểm, hệ thống tự động chuyển cho chuyên gia phụ trách thay vì cố trả lời. Nguyên tắc là an toàn thắng tiện lợi: khi không chắc thì leo thang, không mặc định tự trả lời. Bệnh nhân vẫn nhìn thấy toàn bộ trong cùng một khung chat, chỉ khác tên và ảnh đại diện của người trả lời.

Mục đích của tính năng này không phải để thay chuyên gia, mà để chuyên gia chỉ phải trả lời những câu thật sự cần chuyên môn.

### Khi chuyên gia thiếu thông tin để quyết định

Hiện tại chuyên gia chỉ có hai lựa chọn duyệt hoặc từ chối. Trong production cần lựa chọn thứ ba: **yêu cầu bổ sung thông tin**. Chuyên gia đặt câu hỏi cho bệnh nhân, hồ sơ chuyển sang trạng thái chờ bệnh nhân phản hồi, và khi có trả lời thì tự quay lại hàng chờ với nhãn đã phản hồi.

Không có lựa chọn này, chuyên gia buộc phải từ chối cả thực đơn chỉ vì thiếu một thông tin nhỏ, hoặc nhắn tin ngoài hệ thống và làm mất dấu vết kiểm toán.

### Cuối tuần

Backend tính các chỉ số từ nhật ký thật. Nếu dữ liệu quá ít, kết quả là `insufficient_data`, nghĩa là “chưa đủ dữ liệu”, chứ không phải “ổn định”.

Các trường hợp thông thường được gom thành báo cáo tuần. Các dấu hiệu an toàn nghiêm trọng đã được R2 xác minh phải tạo cảnh báo sớm, không chờ đến cuối tuần.

Dashboard của chuyên gia nên tập trung vào câu hỏi “hôm nay cần xử lý ai và vì sao?”, thay vì bắt chuyên gia đọc từng bữa của mọi bệnh nhân.

---

## 4. Kiến trúc cần bổ sung

Kiến trúc cốt lõi vẫn giữ nguyên, chỉ bổ sung các phần cần thiết:

```text
Người dùng
    ↓
Next.js  (desktop cho chuyên gia · mobile-first cho bệnh nhân)
    ↓
FastAPI
    ├── PostgreSQL
    ├── Object storage cho ảnh bữa ăn
    ├── Hàng đợi công việc
    │       ↓
    │     Worker sinh thực đơn và báo cáo tuần
    └── Monitoring và cảnh báo lỗi
```

### Ứng dụng di động

Bệnh nhân dùng điện thoại là chính, chuyên gia dùng máy tính là chính. Hai nhu cầu này khác nhau đủ để phải thiết kế riêng, nhưng **không** đủ để tách thành hai codebase.

Đề xuất: làm **web responsive mobile-first, đóng gói dạng PWA** — không viết ứng dụng native riêng. Ba lý do:

- Đúng stack hiện có. Không thêm dependency mới, không vi phạm quy tắc “dependency mới cần lý do trong PR và được duyệt” trong `CLAUDE.md` mục 7.
- Một codebase là một nơi duy nhất để thực thi ba rule an toàn. Tách app native đồng nghĩa phải bảo đảm lại toàn bộ ranh giới RULE-1/2/3 ở codebase thứ hai, và mỗi lần sửa rule phải sửa hai chỗ.
- Đội hiện tại nhỏ. Chi phí vận hành hai kênh phát hành (App Store, Play Store) kèm quy trình review của họ lớn hơn giá trị nhận được ở giai đoạn này.

Nếu sau này thật sự cần native — ví dụ vì thông báo đẩy mạnh hơn mức PWA cho phép — đó là một quyết định kiến trúc riêng, cần viết ADR riêng, không gộp vào lộ trình tính năng.

Ràng buộc thiết kế mobile áp cho mọi màn hình bệnh nhân:

- Điều hướng chính là **thanh tab dưới đáy**, không phải sidebar trái như bản desktop.
- Hành động ghi nhận bữa ăn phải nằm trong tầm ngón cái, luôn thấy được, không nấp sau menu.
- Thời khoá biểu bữa ăn **không ép đủ bảy cột trên điện thoại**. Mặc định hiện một ngày với bốn ô buổi ăn xếp dọc, có dải chọn ngày ngang phía trên. Bảng đầy đủ bảy cột chỉ dành cho tablet, desktop hoặc khi xoay ngang.
- Form nhập liệu ưu tiên chạm hơn gõ. Dùng bộ chọn hoặc thanh trượt cho khẩu phần thay vì bắt gõ số, vì người dùng có nhiều bệnh nhân lớn tuổi.
- Biểu đồ trên màn hình hẹp cuộn ngang trong khung riêng, không tự co nhỏ tới mức không đọc được số.

### Lưu trữ ảnh bữa ăn

Ảnh nhật ký cần một object storage riêng, không nhét vào cột nhị phân trong PostgreSQL. Mỗi ảnh gắn với một dòng `food_logs` và thừa hưởng đúng ranh giới quyền của dòng đó: chỉ bệnh nhân sở hữu và chuyên gia được phân công trong cùng tổ chức mới xem được.

Ảnh bữa ăn nhạy cảm hơn dữ liệu NHANES đã khử định danh mà hệ thống đang dùng, vì ảnh có thể lộ khuôn mặt hoặc không gian sống. Vì vậy phạm vi sử dụng phải được nói rõ trong consent: ảnh chỉ dùng để chuyên gia đối chiếu, không dùng cho mục đích khác. Đây là phần business hoặc người có thẩm quyền phải duyệt, không phải quyết định kỹ thuật.

### Ranh giới tổ chức

Database cần biết:

```text
Tổ chức/phòng khám
    ├── thành viên và vai trò
    ├── chuyên gia
    ├── bệnh nhân
    └── phân công chăm sóc
```

Mọi truy vấn bệnh nhân, thực đơn và báo cáo đều phải kiểm tra tổ chức. Chuyên gia của phòng khám A không được biết bệnh nhân của phòng khám B tồn tại.

### Hàng đợi và worker

API chỉ nhận yêu cầu và trả về mã job. Worker chịu trách nhiệm chạy CP-SAT, gọi LLM khi cần và lưu kết quả. Mỗi job có trạng thái, số lần thử lại, timeout và lỗi cuối cùng.

Nếu worker bị dừng, một worker khác có thể tiếp tục. Nếu cùng một request bị gửi hai lần, hệ thống phải nhận ra và không tạo hai thực đơn trùng nhau.

### Theo dõi hệ thống

Team cần nhìn thấy:

- API nào đang chậm;
- database có hết connection không;
- hàng đợi còn bao nhiêu job;
- bước nào trong agent tốn nhiều thời gian;
- LLM gọi bao nhiêu lần và lỗi gì;
- có bao nhiêu thực đơn bị P0/P1;
- chuyên gia override rule nào nhiều nhất.

Log phải đủ để điều tra nhưng không chứa token, mật khẩu hoặc thông tin bệnh nhân không cần thiết.

---

## 5. Những quyết định phải thống nhất trước khi sửa lớn

Trước khi thêm bảng mới, team cần viết ngắn gọn bảy quyết định kiến trúc.

### Dữ liệu nào là bản gốc?

Đề xuất: dữ liệu đã được đóng gói thành release có version trong repository là bản được kiểm duyệt; database là bản triển khai của release đó. Dữ liệu trong `reference` và `quarantine` không được agent dùng cho bệnh nhân.

### Một quyết định duyệt được lưu ở đâu?

Hiện `meal_plans` và `meal_plan_review_events` đã lưu một phần thông tin duyệt. Kế hoạch mới đề xuất thêm `plan_approvals`.

Đề xuất: `plan_approvals` lưu artifact đã duyệt và không sửa lại; `meal_plan_review_events` lưu lịch sử hành động; `meal_plans` chỉ giữ trạng thái hiện tại để truy vấn nhanh. Như vậy không có hai nơi cùng tự nhận là nguồn chân lý.

### Bệnh nhân thuộc tổ chức nào?

Đề xuất thêm `organizations` và `organization_members`. Mọi hồ sơ phải thuộc một tổ chức. Chuyên gia chỉ xem bệnh nhân được tổ chức hoặc care team phân công.

### Job chạy ở đâu?

Team chọn một hàng đợi dùng PostgreSQL hoặc Redis. Không nên thêm nhiều dịch vụ nếu PostgreSQL-backed queue đã đáp ứng quy mô ban đầu. Quan trọng nhất là job phải bền, chạy lại được và không tạo kết quả trùng.

### Rule nào được đưa lên production?

Chỉ rule nằm trong một `clinical rule release` đã được R2 ký mới được tác động đến bệnh nhân. Rule chưa xác minh bị vô hiệu hóa hoặc chỉ chạy shadow mode.

### Dữ liệu nào được gửi sang LLM?

Chỉ gửi dữ liệu tối thiểu cần thiết và không có tên, email, số điện thoại hoặc mã định danh trực tiếp. Hệ thống lưu model và phiên bản prompt để audit, nhưng không lưu raw prompt chứa dữ liệu sức khỏe nếu không thật sự cần.

### 🆕 Sản phẩm dinh dưỡng y tế thương mại được xử lý thế nào?

Hội thảo 16/08 dành một nửa thời lượng cho **DSF** (Diabetes-Specific Nutrition Formula) — sữa dinh dưỡng chuyên biệt cho đái tháo đường, dùng thay thế bữa ăn. Khuyến nghị nghe rất thuyết phục và có bảng chỉ định theo BMI/HbA1c rõ ràng.

Hai điều đội cần biết trước khi ai đó đề xuất đưa vào sản phẩm:

- Nghiên cứu được dẫn sử dụng **một sản phẩm thương mại cụ thể** (Glucerna, Abbott) làm can thiệp, và mức bằng chứng phần lớn là **grade C–D / LOE 3–4** — thấp hơn hẳn phần liệu pháp dinh dưỡng y học (MNT) vốn dẫn guideline độc lập.
- Gợi ý một sản phẩm y tế mà người bệnh **chưa dùng** là tiến gần tới việc **chỉ định** — vượt ranh giới an toàn ở `CLAUDE.md` §3.

**Quyết định giữ nguyên ranh giới hiện có** (đã cài đúng trong `src/clinical/medical_nutrition.py`, R2 kiểm ngày 17/08): sản phẩm dinh dưỡng y tế chỉ vào thực đơn khi bệnh nhân **đã tự khai đang dùng thật**; hồ sơ không khai gì thì không sản phẩm nào lọt vào (fail closed). Khi có khai, năng lượng của sản phẩm được **tính vào** tổng ngày chứ không cộng thêm — đúng nguyên tắc hội thảo nhấn mạnh (*"DSF không được cộng thêm vào chế độ ăn cũ"*).

**Hệ thống không bao giờ tự gợi ý sản phẩm thương mại nào.** Điều này áp cho cả thực đơn lẫn trợ lý trả lời câu hỏi.

### Tính năng nào được ưu tiên?

Team đã chốt: **đơn giản và dễ dùng được ưu tiên hơn tính năng gây ấn tượng.** Khi phải chọn giữa hai việc, dùng ba phép lọc sau theo đúng thứ tự:

**Thứ nhất, giảm việc cho người bận trước, làm đẹp sau.** Chuyên gia dinh dưỡng không có nhiều thời gian. Mọi tính năng giảm được số lần họ phải tự tay làm gì đó — duyệt lại, đọc từng bữa, trả lời câu hỏi lặp — xếp trên tính năng chỉ tăng mức độ hài lòng.

**Thứ hai, tính năng lâm sàng thật đứng trước tính năng giữ chân.** Cân nặng, chỉ số đo lường và ghi nhận bữa ăn là dữ liệu bác sĩ dùng để ra quyết định. Chuỗi ngày liên tục và huy hiệu chỉ có giá trị khi phần lõi đã chạy tốt và đã có dữ liệu thật.

**Thứ ba, không tính năng nào được mở đường tắt qua ba rule an toàn.** Trợ lý không tự tính số, không tự đổi thực đơn. Ảnh không tự nhận diện. Mọi câu trả lời tự động phải có đường leo thang cho người thật.

Phép lọc này giải thích vì sao thứ tự ở mục 6 không xếp theo mức độ hấp dẫn của tính năng.

---

## 6. Lộ trình hoàn thiện

Thời gian dưới đây được tính từ ngày team chọn làm T0. Với team nhỏ, toàn bộ hành trình đến production có kiểm soát nên được nhìn như chương trình khoảng 8–10 tuần, không phải một sprint cuối tuần.

### Danh mục tính năng và vị trí trong lộ trình

Bảng này là câu trả lời ngắn cho “làm tính năng nào, làm lúc nào”. Đặc tả chi tiết từng tính năng — luồng màn hình, sơ đồ, ràng buộc an toàn — nằm ở [Kim chỉ nam trải nghiệm bệnh nhân](./PATIENT_EXPERIENCE_MASTER_PLAN.md).

| Mã | Tính năng | Ưu tiên | Thuộc chặng |
|---|---|:-:|---|
| F1 | Chuyên gia yêu cầu bổ sung thông tin thay vì buộc phải từ chối | P0 | Chặng 3 |
| F2 | Tái sử dụng thực đơn — reuse y hệt cộng biến thể có kiểm soát trong phạm vi đã duyệt (bộ giải đã có sẵn) | P0 | Chặng 4 |
| F3a | Trợ lý tự động trả lời câu hỏi an toàn của bệnh nhân | P1 | Chặng 3 |
| F3b | Tự động chuyển câu hỏi cho chuyên gia khi vượt ranh giới hoặc có rủi ro | P0, bắt buộc đi kèm F3a | Chặng 4 |
| F4 | Cân nặng, chỉ số đo lường và biểu đồ theo thời gian | P1 | Chặng 4 |
| F5 | Thời khoá biểu bữa ăn và ghi nhận có ảnh đính kèm | P1 | Chặng 4 |
| F6 | Chuỗi ngày ghi nhận liên tục | P2 | Sau Chặng 4 |
| F7 | Huy hiệu và phần thưởng | P3 | Sau cùng |
| F8 | Mobile-first và PWA | Ràng buộc xuyên suốt | Áp cho mọi màn hình mới |

Hai điều cần nhớ khi đọc bảng: **F3a không được phát hành nếu F3b chưa xong** — một trợ lý biết trả lời nhưng không biết leo thang là rủi ro an toàn, không phải tính năng nửa vời vô hại. Và **F6, F7 chỉ bắt đầu sau khi F5 đã chạy ổn định**, vì chuỗi ngày và huy hiệu đo trên dữ liệu ghi nhận thật; làm sớm thì không có gì để đo.

Ngoài ra có ba khoản nợ giao diện nên trả cùng lúc với F1 vì chung một màn hình hàng chờ duyệt: nút nổi hiện bị cắt mất một nửa ngoài mép phải trên mọi trang, hàng chờ duyệt không hiện mức rủi ro P0/P1/P2 trên từng dòng, và danh sách hồ sơ bệnh nhân chỉ có phân trang mà không có lọc hay sắp xếp.

### Chặng 1 — Làm cho nền móng database đáng tin cậy

Thời gian dự kiến: tuần đầu tiên.

Team tạm ngừng thêm migration mới. R3 chụp backup production, ghi lại schema và số dòng từng bảng. Sau đó phục hồi migration `c95f302a587e`, nối hai Alembic head thành một đầu duy nhất và thử dựng một PostgreSQL trắng từ đầu.

Việc này chỉ được coi là xong khi:

- database trắng nâng cấp được tới head;
- một bản clone của production tiếp tục nâng cấp được;
- model SQLAlchemy và schema sau migration không còn lệch ngoài các cột legacy đã được giải thích;
- backup đã được khôi phục thử trên database tạm.

Trong cùng chặng, R3 sửa đăng ký công khai để chỉ tạo tài khoản bệnh nhân. Tài khoản chuyên gia chuyển sang cơ chế mời hoặc admin cấp.

### Chặng 2 — Làm sạch luật và dữ liệu

Thời gian dự kiến: một đến hai tuần tiếp theo.

R2 kiểm tra từng clinical rule. Mỗi rule phải nói rõ áp dụng cho ai, không áp dụng cho ai, dùng dữ liệu gì, nguồn nào, trang nào và khi vi phạm thì hệ thống phải làm gì. Rule sai được sửa; rule chưa chắc chắn bị vô hiệu hóa.

> 🆕 **Tin tốt cho chặng này (R2 đo ngày 17/08):** khi đối chiếu bộ rule hiện có với hội thảo 16/08, **không rule nào của dự án sai**. Sáu trong mười dòng đối chiếu kết luận "giữ nguyên"; ngưỡng natri của dự án (2.000 mg) còn **chặt hơn** khuyến nghị quốc tế (2.300 mg) nên giữ, không nới. Chỉ còn **một điểm lệch cần quyết**: tỉ lệ protein (dự án 15–20 %E theo QĐ 5481, hội thảo 20–25 %E).
>
> Nghĩa là công việc chính của chặng này nhẹ hơn dự tính: chủ yếu là **ghi lại bằng chứng đã đối chiếu** vào trường nguồn của từng rule, không phải sửa số. Bảng đối chiếu chi tiết ở [`docs/KE_HOACH_TRI_THUC_LAM_SANG_R2.md`](./docs/KE_HOACH_TRI_THUC_LAM_SANG_R2.md) §4.

Song song, team tạo một release dữ liệu món Việt có kiểm soát. Mục tiêu đầu tiên không cần hàng nghìn món. Một bộ khoảng 24 món thật sự sạch, có đủ vai trò bữa sáng, tinh bột, đạm, rau, canh và bữa phụ có giá trị hơn hàng nghìn dòng không rõ trạng thái.

> 🆕 **Hai vấn đề dữ liệu R2 đo được, cần xử lý trong bộ 24 món này:**
> - Kho hiện có **9 món cá/hải sản đã duyệt, nhưng 6 trong số đó là *canh*** — nơi cá chỉ là nguyên liệu phụ (một bát canh cá rô có 84 g cá cho 2 suất). Khuyến nghị lâm sàng "ăn cá 2–3 bữa mỗi tuần" hàm ý cá là **nguồn đạm chính của bữa**, nên bộ 24 món cần thêm món cá dạng món mặn, không phải thêm canh.
> - Có **hai cặp món trùng tên nhưng khác mã** (`Canh chua cá`, `Cá kho tộ` — mỗi món tồn tại hai dòng từ hai nguồn). Ràng buộc "không lặp món trong ngày" của bộ giải so theo mã món nên hai dòng này lách được: bệnh nhân có thể nhận cùng một món ở cả bữa trưa lẫn bữa tối. Chọn một nguồn cho mỗi món, loại dòng còn lại khỏi release.

R3 đối chiếu dữ liệu cũ trên Supabase với release mới. Dòng legacy đang được lịch sử thực đơn tham chiếu không bị xóa; chúng được đánh dấu không còn dùng cho generation. Từ thời điểm này, generator chỉ đọc dữ liệu thuộc release đang hoạt động.

Chặng này hoàn thành khi R2 đã ký rule release và data release đầu tiên, còn mọi dữ liệu chưa duyệt đều không thể lọt vào luồng bệnh nhân.

### Chặng 3 — Hoàn thiện việc sinh thực đơn Việt Nam

Thời gian dự kiến: một đến hai tuần.

Đây là giai đoạn triển khai [đặc tả UX sinh thực đơn Việt Nam](./MEAL_GENERATION_VIETNAMESE_UX_PLAN.md).

Mỗi món có vai trò như tinh bột, đạm, rau, canh hoặc bữa phụ. Bữa sáng sử dụng cấu trúc nhanh gọn; bữa trưa và tối dùng mâm cơm; bữa phụ chỉ có một đến hai thành phần phù hợp.

CP-SAT tạo tối đa ba phương án hợp lệ. Backend tính lại dinh dưỡng của từng phương án. LLM chỉ được xếp hạng hoặc diễn đạt các phương án đã qua kiểm tra.

Giao diện hiển thị dinh dưỡng theo món, theo bữa và theo ngày. Bệnh nhân thấy gram cùng đơn vị gia đình khi có nguồn quy đổi. Chuyên gia có thể xem tác động trước khi đổi món, ví dụ thay đổi kcal, carbohydrate, protein và natri.

Khi API trả `409` vì đã có plan cùng ngày, giao diện mở plan hiện có hoặc cho chọn ngày khác, không điều hướng sang một workflow không liên quan.

Mỗi lần sinh lại hoặc chỉnh món tạo phiên bản mới. Bản cũ vẫn còn trong lịch sử. Phiên bản được duyệt gắn với hash cụ thể và không bị ghi đè âm thầm.

Cùng chặng này, màn hình duyệt có thêm lựa chọn thứ ba ngoài duyệt và từ chối: **yêu cầu bổ sung thông tin (F1)**. Chuyên gia viết câu hỏi vào `clinical_notes`, hồ sơ chuyển sang trạng thái chờ bệnh nhân phản hồi, bệnh nhân nhận thông báo và trả lời ngay trong ứng dụng, sau đó hồ sơ tự quay lại hàng chờ với nhãn đã phản hồi. Bảng `clinical_notes` đã tồn tại trong database nên phần việc chủ yếu nằm ở giao diện và trạng thái.

Phần trả lời tự động của trợ lý **(F3a)** cũng bắt đầu ở chặng này, nhưng chỉ ở mức diễn giải thực đơn đã duyệt và tái dùng nguyên guardrail hai tầng đã có trong `src/agents/guardrail.py`. **Không phát hành F3a cho người dùng thật cho tới khi cơ chế leo thang F3b ở Chặng 4 hoàn tất.** Trong thời gian đó, F3a chỉ chạy nội bộ để kiểm thử chất lượng câu trả lời.

### Chặng 4 — Hoàn thiện nhật ký và chăm sóc theo ngoại lệ

Thời gian dự kiến: khoảng hai tuần.

Hệ thống thêm `plan_assignments` để biểu diễn việc một thực đơn đã duyệt — bản gốc hoặc bản biến thể vừa tự phát hành — đang được áp dụng cho bệnh nhân trong khoảng thời gian nào.

Đây là **F2**, và là câu trả lời chính thức cho lo ngại chuyên gia không đủ thời gian duyệt mỗi ngày. Cách giải quyết là **giảm tần suất phải duyệt, không bỏ việc phải duyệt, và không bắt bệnh nhân ăn lặp lại**. Ba việc cần làm, xếp theo đúng thứ tự phụ thuộc: dựng job chạy mỗi đêm gọi tới bộ giải tương đương đã có sẵn cho những hồ sơ đang mở phạm vi thay thế; thêm popup ngay sau khi chuyên gia duyệt thực đơn ngày đầu, hỏi có muốn mở phạm vi thay thế không — không đặt ở lúc bấm sinh, vì bảng phạm vi thay thế chỉ tạo được cho một thực đơn đã ở trạng thái duyệt; và vá điều kiện lọc vùng miền còn thiếu trong bộ giải, để bản tự động sinh mỗi đêm không lệch vùng miền so với thực đơn gốc. Về giao diện: phía bệnh nhân, thẻ thực đơn đang áp dụng hiện thêm hạn hiệu lực và lý do nếu bị dừng tái sử dụng; phía chuyên gia, hàng chờ chỉ hiện các ca thật sự cần quyết định mới, còn các ngày đang áp dụng theo phạm vi đã duyệt chỉ xuất hiện trong hồ sơ bệnh nhân với nhãn riêng, không tính vào việc phải xử lý.

Cũng trong chặng này, **F3b** hoàn thiện phần leo thang của trợ lý: khi guardrail phát hiện câu hỏi vượt ranh giới hoặc có dấu hiệu nguy hiểm, hệ thống tạo một luồng `clinical_notes` và đẩy cho đúng chuyên gia phụ trách, chia hai mức khẩn và không khẩn. Chuyên gia có một mục riêng cho câu hỏi cần vấn đáp, **tách khỏi hàng chờ duyệt thực đơn** — gộp chung sẽ làm loãng thứ tự ưu tiên xử lý P0. Khi F3b chạy được, F3a mới được mở cho người dùng thật.

Bệnh nhân bắt đầu ghi food log thật, qua màn hình **thời khoá biểu bữa ăn (F5)**: lưới bốn buổi nhân bảy ngày, mỗi ô hiện luôn tên món, bấm vào ô trống mở form đã điền sẵn ngày và buổi, ghi bù được cho ngày đã qua, và đính kèm được ảnh làm bằng chứng cho chuyên gia xem. Song song, **F4** mở mục chỉ số cá nhân ghi vào bảng `patient_observations` đã có sẵn: cân nặng, chỉ số khối cơ thể tính từ chiều cao trong hồ sơ, và biểu đồ theo thời gian. Biểu đồ chỉ nối điểm khi có từ hai số liệu thật trở lên; ngày trống để trống, không nội suy.

Hệ thống phân biệt món đã map được, món chưa map được và khẩu phần chưa quy đổi được. Chỉ dòng có số liệu đáng tin mới được cộng vào tổng dinh dưỡng.

Mỗi tuần, worker tạo một bản tổng hợp. Bộ tính toán xác định mức đầy đủ dữ liệu, độ tuân thủ và những pattern lặp lại. LLM, nếu được dùng, chỉ chuyển số liệu đã tính thành lời văn dễ hiểu.

Kết quả chăm sóc gồm các ý nghĩa đơn giản:

- `insufficient_data`: chưa đủ dữ liệu để kết luận;
- `stable`: dữ liệu đủ và chưa thấy pattern cần can thiệp;
- `watch`: có lệch lặp lại nhưng chưa cần xử lý ngay;
- `review_required`: chuyên gia cần xem;
- `red_flag`: rule an toàn đã được R2 xác minh yêu cầu cảnh báo sớm.

Các mức này không thay thế P0/P1/P2. P0/P1/P2 nói về mức rủi ro an toàn; care status nói về cách sắp xếp công việc cho chuyên gia.

Sau khi F5 đã chạy ổn định và có dữ liệu thật, team mới làm **chuỗi ngày ghi nhận liên tục (F6)** và **huy hiệu (F7)**. Ở đây có một ranh giới dễ vi phạm: chuỗi ngày đo **hành vi ghi nhật ký đều đặn**, không phải mức độ tuân thủ điều trị và cũng không phải tình trạng sức khoẻ. Vậy là hệ thống có ba khái niệm khác nhau — mức rủi ro P0/P1/P2, care status, và chuỗi ghi nhận — cả ba phải dùng màu và chữ khác nhau, không được trộn. Chữ đi kèm chuỗi ngày phải trung tính, ví dụ “bạn đã ghi nhật ký năm ngày liên tục”, tuyệt đối không viết thành “năm ngày ăn uống tốt”.

### Chặng 5 — Bổ sung nền tảng B2B và độ bền hệ thống

Thời gian dự kiến: một đến hai tuần.

R3 thêm tổ chức, thành viên tổ chức và phân công care team. Toàn bộ endpoint được kiểm tra lại để bảo đảm không truy cập chéo tổ chức.

Generation và weekly summary được chuyển sang worker bền vững. Team thử tắt worker giữa job rồi khởi động lại. Job phải hoàn thành tiếp hoặc kết thúc với trạng thái lỗi rõ ràng, không mất và không tạo bản trùng.

CI được mở rộng để kiểm tra cả backend, migration và frontend. Một lần merge chỉ được phép đi tiếp khi lint, type check, pytest, data validation, Next.js build và Playwright smoke test đều qua.

Team thiết lập theo dõi lỗi, metrics và cảnh báo. Đồng thời xây runbook cho database lỗi, LLM timeout, job backlog và rule bị thu hồi.

### Chặng 6 — Chạy thử trong shadow mode

Thời gian tối thiểu: hai tuần.

Trong shadow mode, hệ thống tạo báo cáo tuần và đề xuất care status nhưng chưa tự gửi hoặc tự thay đổi việc chăm sóc. Chuyên gia xem kết quả của hệ thống và tự đánh giá song song.

Mục tiêu của giai đoạn này là trả lời:

- hệ thống có bỏ sót trường hợp nguy hiểm không;
- có tạo quá nhiều cảnh báo không;
- trường hợp nào thường bị chuyên gia override;
- báo cáo có giúp giảm thời gian đọc từng bữa không;
- generation mất bao lâu và timeout ở đâu;
- bệnh nhân có ghi đủ dữ liệu không.

Pilot phải dừng ngay nếu phát hiện bỏ sót P0, lộ dữ liệu giữa hai tổ chức, mất quyết định duyệt, mất job hoặc không thể giải thích vì sao một bệnh nhân xuất hiện trong hàng chờ.

### Chặng 7 — Mở production có kiểm soát

Production không mở toàn bộ tính năng cùng lúc. Team deploy schema tương thích trước, sau đó backend/worker, rồi frontend. Các tính năng reuse, weekly alert và LLM có feature flag riêng.

Ban đầu chỉ mở cho một cohort nhỏ. Sau khi theo dõi error rate, timeout, queue và phản hồi chuyên gia, team mới mở rộng.

Nếu có sự cố, feature flag được tắt mà không cần xóa dữ liệu. Code có thể rollback, nhưng schema không nên bị downgrade vội. Vì vậy migration phải ưu tiên kiểu thêm mới và tương thích ngược.

---

## 7. Ai chịu trách nhiệm việc gì?

R1 chịu trách nhiệm kiến trúc tổng thể, agent, worker và đánh giá chất lượng generation. Khi có tranh luận kỹ thuật, R1 chốt hướng sau khi tham khảo R2 và R3.

R2 chịu trách nhiệm clinical rule, dữ liệu thực phẩm/món, test case lâm sàng và quyết định dữ liệu nào đủ điều kiện chạm tới bệnh nhân. Test kỹ thuật không thể thay thế chữ ký của R2.

R3 chịu trách nhiệm FastAPI, database, Alembic, bảo mật, tenant isolation, CI/CD, monitoring, backup và deployment. Một chức năng chạy được trên máy local không được coi là đã vận hành production.

R4 chịu trách nhiệm giao diện, trạng thái loading/empty/error, accessibility cơ bản, Playwright và tài liệu hướng dẫn người dùng. UI không tự tính số và không tự suy diễn chữ “Đạt”. R4 cũng là người giữ ràng buộc mobile-first cho toàn bộ không gian bệnh nhân: một màn hình mới chỉ được coi là xong khi đã dùng được thoải mái trên điện thoại, không phải khi chạy đẹp trên màn hình rộng.

Bạn phụ trách Full-stack integration: ghép contract giữa các phần, chạy staging từ đầu đến cuối và chuẩn bị gói bằng chứng để quyết định Go/No-Go.

Ngoài team kỹ thuật, business hoặc người có thẩm quyền phải phê duyệt consent, retention, phạm vi tuyên bố của sản phẩm và thỏa thuận pilot. Developer không thể tự quyết định phần pháp lý chỉ bằng disclaimer.

---

## 8. Làm sao biết hệ thống đã sẵn sàng production?

Không dùng một checklist hình thức. Quyết định production dựa trên năm câu hỏi lớn.

### Có dựng lại được hệ thống không?

Một người mới clone repository phải tạo được database mới, chạy migration, seed đúng release và khởi động ứng dụng. Team cũng phải khôi phục được backup production trên môi trường tạm.

Nếu database hiện chạy nhưng không thể tái tạo, câu trả lời vẫn là chưa sẵn sàng.

### Có giải thích được mọi quyết định không?

Từ một thực đơn hoặc cảnh báo, team phải truy ngược được bệnh nhân nào, hồ sơ phiên bản nào, rule nào, nguồn dữ liệu nào, generator nào và ai đã duyệt.

Nếu chỉ nhìn thấy một con số nhưng không biết nó đến từ đâu, chức năng đó chưa được phát hành.

### Có giữ được ranh giới an toàn không?

LLM không được tự tính dinh dưỡng hoặc quyết định P0. Rule production đã được R2 duyệt. Thiếu dữ liệu không được gọi là ổn định. Bệnh nhân chỉ thấy plan đã duyệt và không thể xem dữ liệu của người khác.

Với các tính năng tương tác mới, thêm bốn điểm phải kiểm: trợ lý không tự đổi thực đơn qua khung chat; mọi trường hợp trợ lý không chắc đều leo thang cho người thật thay vì tự trả lời; ảnh nhật ký không đi vào bất kỳ pipeline nhận diện hay huấn luyện nào; và chuỗi ngày ghi nhận không được trình bày như một kết luận về sức khoẻ.

🆕 Thêm ba điểm nữa sau khi rà nguồn lâm sàng mới (17/08):

- **Hệ thống không gợi ý sản phẩm dinh dưỡng y tế thương mại nào** mà bệnh nhân chưa tự khai đang dùng — cả trong thực đơn lẫn trong câu trả lời của trợ lý.
- **Chỉ số xét nghiệm (HbA1c, đường huyết, mỡ máu) không được dùng để hệ thống tự đặt mục tiêu điều trị.** Chúng chỉ để hiển thị cho chuyên gia và phân tầng cảnh báo. Đặt mục tiêu điều trị là việc của bác sĩ.
- **Tài liệu có bản quyền hoặc có tài trợ thương mại không được đưa vào kho trích dẫn của trợ lý.** Trợ lý trích dẫn một slide hội thảo có logo hãng cho bệnh nhân là vừa sai bản quyền vừa quảng cáo gián tiếp.

### Hệ thống có chịu được lỗi không?

Restart không làm mất job. LLM timeout không làm request treo vô hạn. Database lỗi tạo cảnh báo cho người vận hành. Backup đã được khôi phục thử. Mỗi sự cố phổ biến đều có người nhận và cách xử lý.

### Pilot có chứng minh giá trị không?

Shadow pilot phải cho thấy hệ thống không bỏ sót vấn đề an toàn đã xác định, không làm chuyên gia ngập trong cảnh báo và thực sự giảm thời gian theo dõi. Nếu chưa có bằng chứng này, sản phẩm vẫn chỉ là một hệ thống kỹ thuật có tiềm năng, chưa phải một quy trình chăm sóc đã được kiểm chứng.

Khi cả năm câu hỏi đều có bằng chứng rõ ràng và R1, R2, R3 cùng business owner đồng ý, hệ thống mới được mở production. Nếu một phần chưa đạt, phần đó phải bị tắt bằng feature flag hoặc quyết định là No-Go.

---

## 9. Kế hoạch 72 giờ đầu tiên

Trong ngày đầu, team chọn ngày T0, điền tên owner thật và tạm khóa mọi migration mới. R3 ghi lại chính xác branch/commit đang chạy trên Render và Vercel, sau đó tạo backup production.

Trong ngày thứ hai, R1 và R3 phục hồi lịch sử Alembic, xác định nguồn của revision `c95f302a587e` và thiết kế cách nối hai head. Song song, R3 vá API đăng ký để người dùng công khai không thể chọn role chuyên gia.

Trong ngày thứ ba, team viết sáu quyết định kiến trúc ở mục 5. R2 bắt đầu từ các hard rule có rủi ro cao nhất và chọn bộ món Việt đầu tiên cho data release. R4 thêm frontend lint/build vào CI.

Chỉ sau khi migration có một head và các quyết định về dữ liệu, approval và tenant đã được chốt, team mới bắt đầu thêm `plan_approvals`, `plan_assignments` hoặc bảng tổ chức.

Bản phân công cụ thể cho tuần đầu — ai làm việc gì, sở hữu vùng file nào, checkpoint kiểm tra bằng lệnh gì — nằm ở [Sprint 1 tuần](./SPRINT_1_TUAN_PHAN_CONG.md).

---

## 10. Kết quả cuối cùng cần đạt

Khi kế hoạch hoàn thành, VNutriCare không chỉ “sinh được một thực đơn”. Sản phẩm phải chứng minh được toàn bộ vòng đời:

```text
Dữ liệu có nguồn và đã được duyệt
        ↓
Rule đã được chuyên gia xác minh
        ↓
Sinh thực đơn Việt Nam có cấu trúc hợp lý
        ↓
Tính toán và kiểm tra tất định
        ↓
Chuyên gia duyệt một phiên bản cụ thể
        ↓
Bệnh nhân dùng trên điện thoại và ghi nhận thực tế
    (thời khoá biểu bữa ăn · ảnh đính kèm · cân nặng)
        ↓
Bệnh nhân hỏi khi cần, trợ lý trả lời phần an toàn
    và chuyển cho chuyên gia phần vượt ranh giới
        ↓
Thực đơn đã duyệt được tái sử dụng khi hồ sơ chưa đổi
        ↓
Hệ thống tổng hợp theo tuần
        ↓
Chuyên gia chỉ xử lý những trường hợp cần thiết
        ↓
Mọi bước đều truy vết, khôi phục và kiểm toán được
```

Đó là ranh giới giữa một bản demo AI và một sản phẩm B2B có thể vận hành lâu dài.
