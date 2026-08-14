# So sánh hai website và kế hoạch cải thiện VNutriCare

**Phiên bản đánh giá:** 14/08/2026  
**Website nhóm P-031:** [VNutriCare](https://p-031-deploy.vercel.app/)  
**Website đối chiếu:** [VMEC-10](https://deployvin.vercel.app/)  
**Phạm vi:** Landing page, đăng nhập, trải nghiệm người bệnh, trải nghiệm chuyên gia, dữ liệu demo và an toàn lâm sàng.

## Phương pháp, độ chính xác và giới hạn

### Mức độ bằng chứng

| Loại nhận định | Cách hiểu |
|---|---|
| **Quan sát live** | Nội dung, route hoặc trạng thái thấy trực tiếp trên bản deploy tại ngày đánh giá |
| **Xác minh code VNutriCare** | Đối chiếu với code local đã pull `origin/main` vào branch làm việc |
| **Suy luận có điều kiện** | Nhận định UX từ điều quan sát được; không khẳng định backend của website đối chiếu |
| **Đề xuất** | Mục tiêu cải thiện cho VNutriCare, chưa phải chức năng hiện có |

Báo cáo không có quyền truy cập mã nguồn VMEC-10. Vì vậy các dashboard có dữ liệu được mô tả là “hiển thị dữ liệu mẫu/quan sát được”, không khẳng định dữ liệu đó được hard-code hay lấy từ backend thật. Tương tự, một menu xuất hiện không được tính là feature hoàn chỉnh nếu chưa kiểm tra được hành động end-to-end.

### Nhóm người dùng của hai website

| Nhóm | VNutriCare | VMEC-10 trên giao diện live | Lưu ý so sánh |
|---|---|---|---|
| Người bệnh | Role kỹ thuật `patient`; xem dữ liệu của mình và ghi nhật ký | Gọi là “Bệnh nhân”; có dashboard kế hoạch và theo dõi | Cùng nhóm sử dụng chính nhưng phạm vi live khác nhau |
| Chuyên môn | Role kỹ thuật `dietitian`; chuyên gia dinh dưỡng/tiết chế | Gọi là “Bác sĩ” trên dashboard | Không đồng nhất hai chức danh khi so quyền/chuyên môn |
| Quản trị | Role kỹ thuật `admin`, chưa xác minh workspace frontend hoàn chỉnh | Chưa xác minh role admin từ giao diện đã xem | Không đưa vào chấm UI nếu không có bằng chứng |
| Data steward | Chưa có role; là đề xuất trong báo cáo backend | Chưa xác minh | Chỉ là nhu cầu quản trị dữ liệu của VNutriCare |
| Người chăm sóc | Chưa có role | Chưa xác minh | Cần consent trước khi đề xuất triển khai |
| Người xem demo | Session/tài khoản demo | Lối vào demo theo vai trò | Không phải role production |

### Phân chia nhu cầu người dùng cho VNutriCare

**Người bệnh:** cần biết hôm nay ăn gì, ghi lại đúng thứ đã ăn, hiểu dữ liệu nào được tính và nhận hướng dẫn khi thiếu thông tin.  
**Chuyên gia dinh dưỡng:** cần review dựa trên bằng chứng, ưu tiên rủi ro và không bị giao các câu hỏi chỉ người bệnh trả lời được.  
**Admin:** cần vận hành, quyền và audit, không nên dùng chung dashboard chuyên gia như một mặc định nghiệp vụ.  
**Data steward đề xuất:** cần quản trị alias, món chuẩn, nguồn và conversion; không phê duyệt thực đơn cho bệnh nhân.

### Bảng điểm đủ và điểm thiếu của VNutriCare

| Hạng mục | Điểm đủ/nền tảng đã có | Điểm thiếu quan sát được | Nguồn bằng chứng |
|---|---|---|---|
| Định vị | T2DM, món Việt, đường huyết, HITL | Cần chứng minh sâu hơn bằng workflow live | Landing + code |
| Người bệnh | Có tổng quan và nhật ký | Mobile menu lỗi; route/menu chưa hoàn chỉnh; food ambiguity chưa chọn được | Live + code |
| Chuyên gia | Có patient/review/create/food-log queue | Một số KPI chưa có dữ liệu; queue food log phân công chưa đúng | Live + code |
| Dữ liệu có nguồn | Có source/source_ref và nguyên tắc không bịa số | Citation chưa trở thành trải nghiệm đồng đều ở mọi màn | Code + UI |
| An toàn | Có approval gate, review packet và fail-closed ở nhiều luồng | Cần E2E chứng minh version/audit/release trên deploy | Code; chưa đủ bằng chứng live |
| Demo | Có tài khoản và dữ liệu demo trong dự án | Chưa một chạm và chưa bảo đảm mọi route có dữ liệu | Live + cấu hình dự án |
| Mobile | Có breakpoint CSS | Patient layout thiếu control mở sidebar | Code |

Các phần sau dùng “chưa có hoặc chưa thể hiện rõ” có chủ ý: nếu code có nền tảng nhưng bản deploy không chứng minh được, báo cáo ghi là **chưa thể hiện rõ**, không kết luận sai rằng hoàn toàn không tồn tại.

## Phần I. So sánh sự khác biệt giữa hai website

Phần này đối chiếu những gì người dùng có thể quan sát trực tiếp trên hai bản deploy. Mục đích là xác định cách mỗi website trình bày sản phẩm, phạm vi chức năng và trải nghiệm demo; không kết luận về chất lượng mã nguồn hoặc backend chỉ từ giao diện.

### 1. So sánh tổng quan

| Tiêu chí | VNutriCare - P-031 | VMEC-10 |
|---|---|---|
| Định vị | Dinh dưỡng lâm sàng cho người đái tháo đường type 2 | Dinh dưỡng AI cho bệnh nhân mắc bệnh mạn tính |
| Giá trị nổi bật | Thực đơn món Việt, mục tiêu đường huyết, dữ liệu có nguồn và chuyên gia phê duyệt | Cá nhân hóa thực đơn, theo dõi tuân thủ và quản lý bệnh nhân |
| Đối tượng chuyên môn | Chuyên gia dinh dưỡng/tiết chế và người bệnh | Bác sĩ và bệnh nhân |
| Phạm vi bệnh lý | Tập trung sâu vào T2DM | Bao phủ nhiều bệnh mạn tính hơn |
| Cách thể hiện AI | AI hỗ trợ, không tự quyết định | AI gợi ý, con người phê duyệt theo mô hình HITL |
| Landing page | Ngắn gọn, tập trung vào thông điệp và độ an toàn | Nhiều khối nội dung, mô tả vấn đề, quy trình và tính năng |
| Truy cập demo | Đi qua trang đăng nhập và mục xem tài khoản demo | Có lựa chọn demo theo vai trò ngay trên trang đăng nhập |
| Dashboard người bệnh | Cấu trúc theo thực đơn, nhật ký, tiến độ và tài khoản; dữ liệu phụ thuộc session/API | Hiển thị sẵn bữa ăn, kcal, muối, mức tuân thủ và cảnh báo mẫu |
| Dashboard chuyên môn | Tập trung vào bệnh nhân, tạo thực đơn, review, nguồn dữ liệu và đánh giá hệ thống | Tập trung vào bệnh nhân, kế hoạch chờ duyệt, tuân thủ, cảnh báo và tin nhắn |
| Minh bạch dữ liệu | Đưa “dữ liệu có nguồn” thành thông điệp cốt lõi | Nhấn mạnh RAG trên cơ sở dữ liệu Việt Nam |
| Cảm giác khi xem nhanh | Chuyên biệt, thận trọng và định hướng lâm sàng | Đầy đủ dữ liệu mẫu và giàu hình ảnh dashboard |

### 2. Khác biệt trên landing page

#### VNutriCare

VNutriCare mở đầu bằng thông điệp:

> Thực đơn món Việt, vừa khẩu vị, đúng mục tiêu đường huyết.

Website xác định ngay bệnh lý trọng tâm là đái tháo đường type 2. Phần mô tả đề cập carbohydrate, GI/GL, thuốc đang dùng và thói quen ăn uống. Hero còn hiển thị một bữa ăn mẫu với lượng carbohydrate, GL và trạng thái đã được chuyên gia duyệt.

Trang giới thiệu được tổ chức gọn, tập trung vào ba giá trị:

- Số liệu có nguồn.
- Kiểm tra an toàn.
- Chuyên gia phê duyệt.

#### VMEC-10

VMEC-10 mở đầu bằng thông điệp dinh dưỡng AI chuẩn lâm sàng cho bệnh nhân mạn tính. Phạm vi mô tả rộng hơn và landing page được chia thành nhiều khối:

- Thách thức khi quản lý dinh dưỡng.
- Quy trình khai báo hồ sơ, AI gợi ý, bác sĩ duyệt và theo dõi.
- RAG trên dữ liệu Việt Nam.
- HITL, cảnh báo dị ứng, theo dõi tự động và biểu đồ tiến độ.
- Nội dung riêng cho bệnh nhân và bác sĩ.

#### Khác biệt chính

VNutriCare ưu tiên **độ chuyên biệt và thông điệp an toàn**, còn VMEC-10 ưu tiên **mô tả phạm vi sản phẩm và số lượng tính năng**. VNutriCare giúp người xem nhận ra bài toán T2DM và món Việt nhanh hơn; VMEC-10 giúp người xem hình dung một nền tảng quản lý rộng hơn.

### 3. Khác biệt trong đăng nhập và demo

#### VNutriCare

Trang đăng nhập cho phép chọn vai trò “Người bệnh” hoặc “Chuyên gia”, sau đó nhập email và mật khẩu. Tài khoản mẫu được đặt trong lựa chọn “Xem tài khoản demo”. Cách này gần với luồng đăng nhập thật nhưng yêu cầu người xem thực hiện thêm thao tác.

#### VMEC-10

Trang đăng nhập hiển thị trực tiếp hai lựa chọn truy cập nhanh theo vai trò. Người xem biết ngay có hai hành trình và có thể mở dashboard mẫu nhanh hơn.

#### Khác biệt chính

VNutriCare thiết kế demo như một phần của luồng xác thực; VMEC-10 tách demo thành hành động nổi bật. Sự khác biệt này ảnh hưởng trực tiếp đến tốc độ trải nghiệm trong buổi thuyết trình.

### 4. Khác biệt trong trải nghiệm người bệnh

#### VNutriCare

Điều hướng người bệnh gồm:

- Tổng quan.
- Thực đơn.
- Nhật ký ăn uống.
- Tiến độ.
- Tin nhắn.
- Tài khoản.

Nội dung dashboard được thiết kế để lấy thực đơn đã phê duyệt và số liệu dinh dưỡng từ hệ thống. Khi truy cập không có session hoặc dữ liệu phù hợp, người xem chưa quan sát được đầy đủ hành trình.

#### VMEC-10

Dashboard mẫu hiển thị ngay:

- Ba bữa trong ngày và giờ ăn.
- Tên món, mô tả, kcal và lượng muối.
- Tỷ lệ tuân thủ trong tuần.
- Cảnh báo vượt ngưỡng dinh dưỡng.
- Các lối vào trợ lý AI, thực đơn, thông báo và lịch sử trao đổi.

#### Khác biệt chính

VNutriCare nhấn mạnh **thực đơn đã được phê duyệt và dữ liệu từ workflow**, còn VMEC-10 nhấn mạnh **khả năng quan sát nhanh qua dữ liệu mẫu đã điền sẵn**. VNutriCare có cấu trúc phù hợp cho quy trình thật nhưng cần dữ liệu demo ổn định để giá trị đó hiện rõ trên bản deploy.

### 5. Khác biệt trong trải nghiệm chuyên gia

#### VNutriCare

Khu vực chuyên gia có:

- Tổng quan.
- Danh sách bệnh nhân.
- Hàng chờ duyệt.
- Tạo thực đơn.
- Nhật ký ăn uống.
- Nguồn dữ liệu.
- Đánh giá hệ thống.
- Kiểm soát phát hành thực đơn.

Cấu trúc này thể hiện rõ chu trình tạo bản nháp, kiểm tra, phê duyệt và phát hành.

#### VMEC-10

Khu vực bác sĩ mẫu có:

- Danh sách bệnh nhân cần chú ý.
- Các chỉ số đường huyết và trạng thái.
- Kế hoạch chờ duyệt.
- Cảnh báo lâm sàng.
- Biểu đồ tuân thủ.
- Lịch sử và tin nhắn.

Dashboard được điền sẵn dữ liệu để thể hiện số lượng bệnh nhân, kế hoạch và cảnh báo.

#### Khác biệt chính

VNutriCare nhấn mạnh **workflow phê duyệt, nguồn dữ liệu và kiểm soát phát hành**. VMEC-10 nhấn mạnh **tổng quan vận hành, số lượng công việc và theo dõi nhiều bệnh nhân**.

### 6. Khác biệt về an toàn và minh bạch

VNutriCare đưa thông điệp “AI không tự quyết định” lên ngay landing page, đồng thời nhấn mạnh kiểm tra thuốc, dị ứng, rủi ro dinh dưỡng và dữ liệu có nguồn. Đây là cách tiếp cận đặt governance vào trung tâm sản phẩm.

VMEC-10 mô tả quy trình AI gợi ý và bác sĩ duyệt, đồng thời giới thiệu HITL và cảnh báo dị ứng. Cách trình bày tập trung vào sự phối hợp giữa AI và người làm chuyên môn trong một nền tảng quản lý rộng.

Sự khác biệt cốt lõi là VNutriCare dùng **khả năng truy vết và quyền phát hành** làm thông điệp chính; VMEC-10 dùng **quy trình có con người tham gia và khả năng theo dõi** làm thông điệp chính.

### 7. Kết luận phần so sánh

Hai website có hướng trình bày khác nhau:

- VNutriCare là sản phẩm chuyên biệt cho T2DM, món Việt và quy trình chuyên gia phê duyệt.
- VMEC-10 trình bày một nền tảng dinh dưỡng mạn tính có phạm vi chức năng rộng và dữ liệu demo trực quan.
- Khoảng cách dễ thấy nhất trên bản deploy không nằm ở thông điệp của VNutriCare, mà ở mức độ sẵn có của dữ liệu demo và số bước cần thực hiện để nhìn thấy giá trị sản phẩm.

## Phần II. Những điểm VMEC-10 đã thể hiện nhưng VNutriCare chưa có hoặc chưa thể hiện rõ

Phần này chỉ đánh giá những gì quan sát được trên hai bản deploy. “Chưa có” ở đây có thể có nghĩa là chưa xuất hiện trên giao diện live, chưa có dữ liệu để chứng minh, hoặc người xem chưa thể truy cập thuận lợi; không mặc định rằng mã nguồn phía sau hoàn toàn không tồn tại.

### 1. Demo theo vai trò được đưa ra ngay lập tức

VMEC-10 hiển thị rõ hai lối vào demo cho bác sĩ và bệnh nhân ngay tại trang đăng nhập. Người xem không cần biết email, mật khẩu hoặc cấu trúc tài khoản. Đây là lợi thế lớn trong buổi thuyết trình vì giảm thời gian thao tác và giảm nguy cơ đăng nhập sai.

VNutriCare ở thời điểm đánh giá đã có lựa chọn vai trò và tài khoản demo, nhưng hành động này nằm sâu hơn trong form. Người lần đầu truy cập chưa chắc biết phải chọn vai trò nào hoặc cần mở khu vực tài khoản mẫu.

**Khoảng cách cần xử lý:**

- Thiếu CTA demo một chạm ngay trên landing page.
- Chưa có đường dẫn riêng và dễ nhớ cho từng vai trò demo.
- Chưa thể hiện rõ session demo sẽ đưa người xem đến dữ liệu nào.

**Mức độ ưu tiên:** P0, vì đây là điểm tiếp xúc đầu tiên trong buổi chấm sản phẩm.

### 2. Dashboard bệnh nhân có dữ liệu ngay khi mở

VMEC-10 cho người xem thấy ngay một ngày ăn hoàn chỉnh: bữa sáng, trưa, tối, giờ ăn, tên món, mô tả, năng lượng và lượng muối. Ngoài kế hoạch hôm nay còn có tỷ lệ tuân thủ trong tuần và một cảnh báo cụ thể.

VNutriCare có cấu trúc dashboard, thực đơn và nhật ký, nhưng giá trị phụ thuộc vào session và dữ liệu trả về từ API. Nếu không có dữ liệu phù hợp, người xem chỉ thấy khung điều hướng hoặc trạng thái chưa đủ nội dung.

**Những thành phần VMEC-10 đang thể hiện rõ hơn:**

- Kế hoạch hôm nay có nội dung cụ thể.
- Chỉ số dinh dưỡng gắn với từng bữa.
- Tỷ lệ tuân thủ được đưa lên trang tổng quan.
- Cảnh báo gần nhất có số liệu và hướng mở chi tiết.
- Dữ liệu mẫu tạo cảm giác người bệnh đã sử dụng hệ thống nhiều ngày.

**Khoảng cách cần xử lý:** VNutriCare cần một bộ dữ liệu demo xuyên suốt, không chỉ một thực đơn đơn lẻ.

### 3. Dashboard chuyên môn tạo cảm giác đang vận hành

VMEC-10 hiển thị ngay số bệnh nhân, số kế hoạch chờ duyệt, số cảnh báo và số tin nhắn. Bảng bệnh nhân có chỉ số biến động và trạng thái cần chú ý. Danh sách kế hoạch cho thấy nhiều phương án đang chờ xử lý.

VNutriCare đã có đúng các khu vực nghiệp vụ như hàng chờ, cảnh báo và kiểm soát phát hành, nhưng một số KPI trên bản live còn là dấu gạch hoặc thông báo chưa có dữ liệu tổng hợp. Điều này khiến cấu trúc tốt chưa chuyển thành cảm giác vận hành thật.

**Những thành phần VMEC-10 đang thể hiện rõ hơn:**

- KPI có số liệu ngay trên first viewport.
- Hàng chờ có nhiều bản ghi và hành động trực tiếp.
- Bệnh nhân được phân loại theo mức cần chú ý.
- Cảnh báo lâm sàng được tổng hợp thành một con số.
- Dashboard liên kết số liệu tổng quan với danh sách cần xử lý.

**Khoảng cách cần xử lý:** Mọi KPI của VNutriCare phải có dữ liệu thật hoặc trạng thái rỗng có ý nghĩa; tuyệt đối không đưa tình trạng thiếu API lên giao diện production.

### 4. Theo dõi tuân thủ được trực quan hóa

VMEC-10 thể hiện tỷ lệ tuân thủ trung bình, thay đổi so với tuần trước, mục tiêu và kết quả theo từng ngày. Dù đây có thể là dữ liệu mẫu, nó cho người xem hiểu ngay sản phẩm không dừng ở việc tạo thực đơn.

VNutriCare có menu tiến độ và nhật ký, nhưng chưa đưa một biểu đồ đủ giàu thông tin lên dashboard live để chứng minh vòng lặp theo dõi sau phát hành.

**Khoảng cách cần xử lý:**

- Thiếu xu hướng bảy ngày trên trang người bệnh.
- Thiếu bảng tổng hợp tuân thủ theo bệnh nhân cho chuyên gia.
- Thiếu liên kết giữa nhật ký thực tế và kế hoạch đã duyệt.
- Thiếu phân biệt không tuân thủ do bỏ bữa, đổi món hay sai khẩu phần.

### 5. Nhiều phương án thực đơn được trình bày như lựa chọn

VMEC-10 cho thấy nhiều phương án thực đơn cho cùng một bệnh nhân. Điều này làm rõ vai trò của AI là tạo phương án để người làm chuyên môn lựa chọn, thay vì tạo một đáp án duy nhất.

VNutriCare có workflow tạo và review thực đơn, nhưng bản deploy chưa trình bày nổi bật việc so sánh nhiều phương án trên cùng một bộ tiêu chí.

**Khoảng cách cần xử lý:**

- Chưa có chế độ so sánh song song.
- Chưa nêu rõ phương án khác nhau ở mục tiêu nào.
- Chưa giúp chuyên gia nhận ra phương án ít cảnh báo hơn.
- Chưa so sánh tính thực tế như khẩu vị, chi phí và độ dễ chuẩn bị.

### 6. Phạm vi hành trình trên giao diện rộng hơn

VMEC-10 đưa lên navigation nhiều điểm tiếp xúc: trợ lý AI, thông báo, lịch sử chat, trao đổi, tin nhắn, tuân thủ và ràng buộc lâm sàng. Điều này tạo ấn tượng về một hệ sinh thái chăm sóc liên tục.

VNutriCare tập trung vào workflow cốt lõi và chưa thể hiện đầy đủ các kênh tương tác trên bản demo. Sự tập trung này là hợp lý về kỹ thuật, nhưng trong phần trình bày cần cho thấy sản phẩm xử lý điều gì xảy ra sau khi người bệnh nhận thực đơn.

**Khoảng cách cần xử lý:**

- Chưa có trung tâm thông báo đủ rõ.
- Chưa có luồng trao đổi gắn với một cảnh báo hoặc một bữa ăn.
- Chưa có lịch sử quyết định được trình bày thân thiện.
- Chưa cho thấy cách chuyên gia phản hồi khi mức tuân thủ giảm.

Không cần sao chép toàn bộ menu. VNutriCare chỉ nên bổ sung những điểm tiếp xúc làm hoàn chỉnh workflow lâm sàng.

### 7. Luồng đăng ký tài khoản được thể hiện công khai

VMEC-10 có trang đăng ký với họ tên, thông tin liên hệ, bệnh lý nền và mật khẩu. Điều này giúp người xem hình dung cách một người dùng mới bắt đầu.

VNutriCare hiện ưu tiên đăng nhập và demo, chưa thể hiện rõ onboarding người dùng mới trên bản deploy.

**Khoảng cách cần xử lý:**

- Chưa có luồng mời người bệnh bởi chuyên gia.
- Chưa làm rõ ai có quyền tạo hồ sơ lâm sàng.
- Chưa có quy trình đồng ý sử dụng dữ liệu và xác nhận điều khoản.
- Chưa phân biệt đăng ký tài khoản với hoàn thiện hồ sơ lâm sàng.

Đối với sản phẩm lâm sàng, VNutriCare không nên chỉ thêm một form đăng ký công khai. Giải pháp chuyên nghiệp hơn là luồng chuyên gia mời người bệnh, xác minh danh tính, đồng ý xử lý dữ liệu và hoàn thiện hồ sơ theo từng bước.

### 8. Giá trị sản phẩm được kể bằng số liệu thay vì lời mô tả

VMEC-10 dùng số bệnh nhân, số cảnh báo, số kế hoạch và tỷ lệ tuân thủ để kể câu chuyện sản phẩm. Người xem không cần đọc nhiều đoạn giải thích để hiểu dashboard dùng làm gì.

VNutriCare có thông điệp chuyên môn tốt nhưng một số giá trị mới xuất hiện dưới dạng lời hứa trên landing page. Ví dụ “dữ liệu có nguồn” và “theo dõi tối ưu” cần được chứng minh bằng các tương tác có thể mở xem.

**Khoảng cách cần xử lý:**

- Chuyển “dữ liệu có nguồn” thành citation có thể nhấn.
- Chuyển “kiểm tra an toàn” thành review packet có cảnh báo cụ thể.
- Chuyển “theo dõi” thành biểu đồ và danh sách can thiệp.
- Chuyển “chuyên gia phê duyệt” thành lịch sử phiên bản và chữ ký số nội bộ.

### 9. Ma trận khoảng cách cạnh tranh

| Năng lực quan sát trên bản deploy | VMEC-10 đã thể hiện | VNutriCare hiện tại | Mục tiêu của VNutriCare |
|---|---|---|---|
| Demo theo vai trò | Có lối vào trực tiếp | Có nhưng chưa đủ nổi bật | Một chạm, session an toàn, dữ liệu reset được |
| Kế hoạch hôm nay | Có dữ liệu mẫu đầy đủ | Phụ thuộc session/API | Dữ liệu thật từ thực đơn đã phát hành |
| KPI chuyên gia | Có số liệu minh họa | Có cấu trúc nhưng một số ô chưa có số | KPI thật, có kỳ đo và drill-down |
| Tuân thủ bảy ngày | Có tỷ lệ và biểu đồ | Chưa thể hiện rõ trên live | Tính từ nhật ký, giải thích được từng sai lệch |
| Nhiều phương án | Có danh sách phương án | Chưa có so sánh nổi bật | So sánh dinh dưỡng, rủi ro, chi phí và khẩu vị |
| Cảnh báo | Có cảnh báo hiển thị | Có nền tảng quy tắc | Có rule ID, nguồn, mức độ và cách xử lý |
| Trao đổi | Có menu chat/tin nhắn | Chưa nổi bật | Hội thoại gắn với ca bệnh và audit log |
| Onboarding | Có form đăng ký | Chưa thể hiện rõ | Luồng mời, consent và hoàn thiện hồ sơ an toàn |
| Nguồn dữ liệu | Nêu RAG dữ liệu Việt | Nêu dữ liệu có nguồn | Citation đến từng món, chất và quy tắc |
| Phát hành | Có bước phê duyệt | Có kiểm soát phát hành | Versioning, audit và chỉ bản duyệt đến người bệnh |

## Phần III. Điểm mạnh của VNutriCare

### 1. Định vị chuyên biệt và dễ ghi nhớ

VNutriCare không mô tả mình như một ứng dụng dinh dưỡng chung. Sản phẩm tập trung vào đái tháo đường type 2, món Việt và mục tiêu đường huyết. Đây là phạm vi đủ cụ thể để xây dựng dữ liệu, quy tắc và kịch bản đánh giá có chiều sâu.

### 2. Phù hợp bối cảnh ăn uống Việt Nam

Việc đặt món Việt ở trung tâm giúp sản phẩm gần với nhu cầu thực tế hơn các kế hoạch ăn uống mang tính quốc tế hoặc khó áp dụng. Đây cũng là cơ sở để phát triển khẩu phần quen thuộc, món thay thế tương đương, khả năng mua nguyên liệu và mức độ dễ chế biến.

### 3. Thông điệp an toàn rõ ràng

Câu “AI không tự quyết định” xuất hiện sớm và nhất quán với workflow chuyên gia duyệt trước khi phát hành. Điều này giúp xác định đúng vai trò của hệ thống là hỗ trợ quyết định, không thay thế con người.

### 4. Chú trọng dữ liệu có nguồn

VNutriCare đưa nguồn dữ liệu thành một giá trị sản phẩm thay vì chi tiết kỹ thuật phía sau. Nếu triển khai đầy đủ citation theo món, mục tiêu và cảnh báo, đây sẽ là lợi thế lớn về độ tin cậy và khả năng giải thích.

### 5. Workflow chuyên gia có cấu trúc

Sản phẩm đã phân biệt tạo thực đơn, hàng chờ review, phê duyệt và phát hành. Cấu trúc này phù hợp với yêu cầu kiểm soát phiên bản và ngăn người bệnh nhìn thấy đề xuất chưa được kiểm tra.

### 6. Có nền tảng theo dõi sau phát hành

Khu vực người bệnh có thực đơn, nhật ký và tiến độ. Điều này cho phép sản phẩm đi xa hơn việc sinh một thực đơn một lần, hướng đến vòng lặp theo dõi, phản hồi và điều chỉnh.

### 7. Có khả năng trở thành sản phẩm minh bạch hơn

Sự kết hợp giữa nguồn dữ liệu, cảnh báo, chuyên gia phê duyệt và audit log tạo nền tảng cho một sản phẩm có thể trả lời các câu hỏi quan trọng: món ăn được chọn vì sao, quy tắc nào đã chạy, ai đã chỉnh sửa và ai đã phê duyệt.

## Phần IV. Kế hoạch cải thiện VNutriCare để vượt lên về chất lượng sản phẩm

Mục tiêu không phải là sao chép số lượng màn hình hoặc làm dashboard trông nhiều dữ liệu hơn. VNutriCare nên bắt kịp về khả năng demo nhưng vượt lên ở bốn lớp: **dữ liệu thật, giải thích được, an toàn có thể kiểm chứng và workflow hoàn chỉnh**.

### Chiến lược 1. Demo đẹp nhưng phải chạy trên workflow thật

VNutriCare cần seed dữ liệu mẫu vào chính backend và database của sản phẩm. Mọi con số trên dashboard phải có thể mở xuống bản ghi nguồn. Ví dụ, KPI “3 thực đơn chờ duyệt” phải dẫn đến đúng ba thực đơn; tỷ lệ tuân thủ phải tính từ nhật ký; cảnh báo phải đến từ rule engine.

**Kết quả cần đạt:**

- Người xem có trải nghiệm đầy đủ như một bản demo dựng sẵn.
- Đội phát triển chứng minh được dữ liệu không phải số viết cứng trong frontend.
- Mọi hành động tạo, sửa, duyệt và ghi nhật ký làm dashboard cập nhật thật.
- Có script reset để buổi demo tiếp theo luôn bắt đầu ở trạng thái chuẩn.

### Chiến lược 2. Biến dữ liệu có nguồn thành trải nghiệm nổi bật

Không dừng ở nhãn “có nguồn”. Mỗi món ăn, chất dinh dưỡng, mục tiêu và cảnh báo cần có nút mở phần giải thích. Nguồn nên hiển thị tên tài liệu, phiên bản hoặc ngày truy cập, phạm vi áp dụng và dữ liệu được lấy từ nguồn đó.

**Kết quả cần đạt:**

- Từ một con số carbohydrate, chuyên gia mở được thành phần tạo ra con số đó.
- Từ một cảnh báo, chuyên gia mở được rule, dữ liệu kích hoạt và nguồn tham chiếu.
- Dữ liệu thiếu được đánh dấu, không tự động xem như bằng 0.
- Người dùng phân biệt được dữ liệu đo, dữ liệu khai báo và dữ liệu AI suy luận.

### Chiến lược 3. Review packet tốt hơn một nút phê duyệt nhanh

VNutriCare nên tối ưu chất lượng quyết định, không tối ưu số lần bấm bằng mọi giá. Review packet phải giúp chuyên gia xem đủ mục tiêu, dinh dưỡng theo bữa, cảnh báo, nguồn, phiên bản và thay đổi trước khi phê duyệt.

**Kết quả cần đạt:**

- Cảnh báo mức cao chặn phát hành cho đến khi được xử lý.
- Cảnh báo có thể bỏ qua chỉ khi chuyên gia nhập lý do.
- Mọi thay đổi sau phê duyệt tạo phiên bản mới.
- Người bệnh chỉ nhận phiên bản đã phát hành.
- Audit log trả lời được ai làm gì, khi nào và dựa trên dữ liệu nào.

### Chiến lược 4. Cá nhân hóa theo khả năng thực hiện, không chỉ theo chỉ số

Thực đơn đạt mục tiêu dinh dưỡng nhưng quá đắt, khó mua hoặc không hợp khẩu vị vẫn khó tuân thủ. VNutriCare nên đưa tính khả thi vào tiêu chí so sánh phương án.

**Kết quả cần đạt:**

- Hồ sơ có ngân sách, thiết bị nấu, thời gian chuẩn bị và món không thích.
- Mỗi phương án có điểm phù hợp khẩu vị và độ dễ thực hiện.
- Món thay thế giữ mục tiêu dinh dưỡng trong một khoảng sai số xác định.
- Chuyên gia thấy rõ đánh đổi giữa dinh dưỡng, chi phí và tính thuận tiện.

### Chiến lược 5. Theo dõi tuân thủ phải dẫn đến hành động

Biểu đồ đẹp chưa đủ. Khi mức tuân thủ giảm, hệ thống phải giúp chuyên gia biết nguyên nhân và chọn can thiệp phù hợp.

**Kết quả cần đạt:**

- Phân biệt bỏ bữa, đổi món, sai khẩu phần và thiếu dữ liệu.
- Cho thấy bữa hoặc ngày nào làm giảm tỷ lệ tuân thủ.
- Tạo danh sách bệnh nhân cần chú ý theo quy tắc minh bạch.
- Cho phép chuyên gia gửi phản hồi gắn với nhật ký cụ thể.
- Theo dõi hiệu quả sau khi điều chỉnh thực đơn.

### Chiến lược 6. Trợ lý AI có giới hạn và đường chuyển tiếp rõ

Nếu bổ sung trợ lý hội thoại, AI không nên trở thành chatbot trả lời mọi câu hỏi sức khỏe. Trợ lý cần giới hạn trong dữ liệu thực đơn đã duyệt, hướng dẫn sử dụng và ghi nhận vấn đề để chuyển cho chuyên gia.

**Kết quả cần đạt:**

- Không tự thay đổi thực đơn đã phát hành.
- Không đưa ra chẩn đoán hoặc thay đổi thuốc.
- Trích dẫn thực đơn hoặc nguồn khi trả lời.
- Phát hiện câu hỏi vượt phạm vi và chuyển sang chuyên gia.
- Lưu hội thoại theo chính sách dữ liệu và quyền truy cập phù hợp.

### Chiến lược 7. Tạo một “khoảnh khắc chứng minh” trong buổi demo

Điểm gây ấn tượng nhất không nên là số lượng card trên dashboard. Kịch bản cần có một thời điểm hệ thống phát hiện rủi ro mà người xem dễ hiểu, chuyên gia xử lý rủi ro, rồi bản an toàn mới xuất hiện cho người bệnh.

Ví dụ:

1. AI tạo thực đơn có một món xung đột với dị ứng hoặc giới hạn đã khai báo.
2. Rule engine đánh dấu món, nêu dữ liệu kích hoạt và nguồn.
3. Hệ thống đề xuất hai món thay thế gần khẩu vị Việt.
4. Chuyên gia chọn món, điều chỉnh khẩu phần và xem tổng dinh dưỡng tính lại.
5. Chuyên gia phê duyệt phiên bản mới.
6. Người bệnh chỉ thấy phiên bản đã duyệt, kèm lý do thay đổi dễ hiểu.

Khoảnh khắc này chứng minh đồng thời năng lực AI, dữ liệu, rule engine, human-in-the-loop và kiểm soát phát hành. Đây là lợi thế khó bị thay thế bằng một dashboard có dữ liệu tĩnh.

### Chuẩn chất lượng để VNutriCare vượt lên

| Hạng mục | Mức “có tính năng” | Mức VNutriCare cần đạt |
|---|---|---|
| Demo | Có dữ liệu nhìn thấy được | Dữ liệu seed qua backend thật, reset được |
| KPI | Có con số trên card | Có kỳ đo, công thức và drill-down |
| Cảnh báo | Có màu và nội dung | Có rule ID, mức độ, nguồn và hành động |
| Thực đơn | Có danh sách món | Có lý do chọn, khẩu phần, nguồn và món thay thế |
| Nhiều phương án | Có nhiều tên phương án | So sánh định lượng và giải thích đánh đổi |
| Tuân thủ | Có phần trăm và biểu đồ | Truy ngược được đến từng nhật ký và can thiệp |
| AI assistant | Có giao diện chat | Có giới hạn, citation và escalation |
| Phê duyệt | Có nút duyệt | Có review packet, versioning và audit trail |
| Người bệnh | Xem kế hoạch | Chỉ xem bản phát hành và hiểu vì sao phù hợp |
| Chuyên gia | Xử lý hàng chờ | Ưu tiên rủi ro, ra quyết định có bằng chứng |

## 1. Mục tiêu cải thiện

VNutriCare đã có định vị rõ: hỗ trợ xây dựng thực đơn món Việt cho người đái tháo đường type 2, có kiểm tra mục tiêu dinh dưỡng, thuốc, dị ứng và sự phê duyệt của chuyên gia. Giai đoạn tiếp theo không nên mở rộng quá nhiều tính năng mà cần làm cho các giá trị hiện có rõ ràng, có dữ liệu minh họa và kiểm chứng được ngay trên bản deploy.

Các mục tiêu chính:

- Người xem hiểu sản phẩm giải quyết vấn đề gì trong 10 giây đầu.
- Người bệnh và chuyên gia vào được tài khoản demo trong một lần bấm.
- Mọi dashboard có dữ liệu mẫu nhất quán, không xuất hiện màn hình trống.
- Có một hành trình hoàn chỉnh từ hồ sơ bệnh nhân đến thực đơn được phê duyệt.
- Thể hiện rõ AI chỉ hỗ trợ, chuyên gia ra quyết định cuối cùng.
- Mỗi cảnh báo và khuyến nghị quan trọng đều có lý do và nguồn tham chiếu.
- Bản deploy ổn định, không phụ thuộc vào thao tác chuẩn bị thủ công.

## 2. Định vị và thông điệp sản phẩm

Thông điệp “Thực đơn món Việt, vừa khẩu vị, đúng mục tiêu đường huyết” là điểm mạnh và nên được giữ lại. Phần mô tả cần nói rõ hơn kết quả từng nhóm người dùng nhận được.

### Nội dung đề xuất

**Tiêu đề:**

> Thực đơn món Việt, vừa khẩu vị, đúng mục tiêu đường huyết.

**Mô tả:**

> VNutriCare hỗ trợ chuyên gia xây dựng và phê duyệt thực đơn cá nhân hóa cho người đái tháo đường type 2 dựa trên carbohydrate, GI/GL, thuốc đang dùng, dị ứng và thói quen ăn uống.

**Thông điệp an toàn:**

> AI hỗ trợ đề xuất và kiểm tra. Chuyên gia là người xem xét, chỉnh sửa và phê duyệt trước khi thực đơn được gửi đến người bệnh.

### Nội dung cần bổ sung

- Ảnh chụp dashboard thật thay vì chỉ dùng hình minh họa.
- Ví dụ cụ thể về bữa ăn, tổng carbohydrate, GL và trạng thái phê duyệt.
- Đường dẫn thực sự mở được nguồn dữ liệu hoặc phần giải thích.
- Khối mô tả quá trình sau phê duyệt: người bệnh xem thực đơn, ghi nhật ký và theo dõi mức tuân thủ.

### Nội dung cần tránh

- Không tuyên bố AI thay thế bác sĩ hoặc chuyên gia dinh dưỡng.
- Không dùng các cụm như “an toàn tuyệt đối” hoặc “chính xác tuyệt đối”.
- Không mở rộng sang mọi bệnh mạn tính nếu dữ liệu và quy tắc hiện tại chủ yếu phục vụ T2DM.
- Không đưa chi tiết kỹ thuật như API, endpoint hoặc lỗi hệ thống vào nội dung cho người dùng.

## 3. Cải thiện landing page

Landing page cần dẫn người xem đến trải nghiệm sản phẩm nhanh hơn và phân biệt rõ hai vai trò.

### Khu vực hero

Giữ cấu trúc hiện tại nhưng thay hai CTA bằng:

- **Demo người bệnh:** đăng nhập trực tiếp vào tài khoản người bệnh mẫu.
- **Demo chuyên gia:** đăng nhập trực tiếp vào tài khoản chuyên gia mẫu.

CTA phụ có thể là “Xem quy trình an toàn” và cuộn xuống phần giải thích workflow.

### Khối bằng chứng sản phẩm

Ngay dưới hero nên có một hàng thông tin ngắn:

| Thông tin | Nội dung đề xuất |
|---|---|
| Đối tượng | Người đái tháo đường type 2 |
| Dữ liệu | Món Việt và thành phần dinh dưỡng có nguồn |
| An toàn | Kiểm tra thuốc, dị ứng và giới hạn dinh dưỡng |
| Quyết định cuối | Chuyên gia phê duyệt trước khi phát hành |

### Khối quy trình

Quy trình nên thể hiện đủ sáu bước:

1. Thu thập hồ sơ lâm sàng và thói quen ăn uống.
2. Thiết lập mục tiêu dinh dưỡng cá nhân.
3. AI tạo một số phương án thực đơn.
4. Hệ thống kiểm tra quy tắc và tạo cảnh báo.
5. Chuyên gia xem xét, chỉnh sửa và phê duyệt.
6. Người bệnh thực hiện, ghi nhật ký và nhận theo dõi.

### Khối minh bạch dữ liệu

Landing page nên cho người xem mở một ví dụ nguồn dữ liệu, gồm:

- Nguồn thành phần dinh dưỡng của món ăn.
- Nguồn mục tiêu carbohydrate hoặc chất xơ.
- Ngày cập nhật dữ liệu.
- Phạm vi áp dụng và giới hạn của khuyến nghị.

## 4. Cải thiện đăng nhập và demo

Mục tiêu của luồng demo là giảm tối đa thao tác và rủi ro trong lúc trình bày.

### Yêu cầu chức năng

- Có hai nút đăng nhập nhanh theo vai trò.
- Nút demo tự tạo hoặc nạp session có thời hạn.
- Không yêu cầu người xem sao chép email và mật khẩu.
- Có cơ chế đặt lại dữ liệu demo.
- Tài khoản demo chỉ sử dụng dữ liệu giả lập.
- Hiển thị rõ đây là môi trường demo.

### Trạng thái lỗi

Nếu backend không phản hồi, giao diện nên hiển thị:

> Không thể tải dữ liệu vào lúc này. Vui lòng thử lại sau.

Không hiển thị stack trace, tên endpoint, mã lỗi nội bộ hoặc câu “chưa có API”. Cần có nút “Thử tải lại” và mã tham chiếu ngắn để đội phát triển tra log.

### Yêu cầu bảo mật

- Session demo không có quyền quản trị hệ thống.
- Không cho phép thay đổi email, mật khẩu hoặc quyền của tài khoản demo.
- Thao tác phê duyệt trong demo chỉ tác động đến dữ liệu mẫu.
- Dữ liệu demo có thể khôi phục sau mỗi buổi trình bày.

## 5. Cải thiện dashboard người bệnh

Dashboard người bệnh cần trả lời ngay bốn câu hỏi:

1. Hôm nay tôi ăn gì?
2. Vì sao thực đơn này phù hợp với tôi?
3. Tôi đang tuân thủ đến đâu?
4. Khi có vấn đề, tôi cần làm gì?

### Tổng quan hôm nay

Nên hiển thị:

- Ngày áp dụng thực đơn.
- Trạng thái “Đã được chuyên gia phê duyệt”.
- Tên chuyên gia và thời điểm phê duyệt.
- Tổng năng lượng, carbohydrate, protein, chất xơ và chỉ số liên quan.
- Tiến độ số bữa đã ghi nhận trong ngày.

### Thẻ bữa ăn

Mỗi bữa nên có:

- Tên món tiếng Việt và ảnh đúng món.
- Khẩu phần theo gram hoặc đơn vị quen thuộc.
- Năng lượng và carbohydrate.
- GI/GL khi dữ liệu đủ tin cậy.
- Thời gian ăn gợi ý.
- Món thay thế tương đương.
- Lý do món được chọn.
- Cảnh báo liên quan đến dị ứng, thuốc hoặc bệnh nền.

Không nên dùng cùng một ảnh cho nhiều bữa khác nhau. Nếu chưa có ảnh đúng món, dùng placeholder trung tính có tên món thay vì ảnh sai.

### Theo dõi tuân thủ

Cần bổ sung biểu đồ bảy ngày với:

- Tỷ lệ số bữa thực hiện đúng kế hoạch.
- Carbohydrate thực tế so với mục tiêu.
- Các ngày bỏ ghi nhật ký.
- Xu hướng đường huyết nếu có dữ liệu phù hợp.
- Nhận xét ngắn, dễ hiểu và không mang tính chẩn đoán.

Ví dụ:

> Bạn đã hoàn thành 17/21 bữa trong tuần. Hai bữa tối vượt mục tiêu carbohydrate. Hãy trao đổi với chuyên gia nếu việc tuân thủ gặp khó khăn.

### Cảnh báo và hướng xử lý

Mỗi cảnh báo cần có:

- Mức độ: thông tin, cần chú ý hoặc cần liên hệ chuyên gia.
- Nội dung ngắn gọn.
- Lý do cảnh báo xuất hiện.
- Hướng xử lý an toàn.
- Nút liên hệ chuyên gia khi cần.

Không chỉ nói “vượt ngưỡng” mà không cho biết ngưỡng nào, trong khoảng thời gian nào và người dùng nên làm gì tiếp theo.

### Nhật ký ăn uống

Luồng ghi nhật ký cần hỗ trợ:

- Chọn bữa theo thực đơn đã duyệt.
- Xác nhận ăn đủ, ăn một phần hoặc thay món.
- Chỉnh khẩu phần thực tế.
- Thêm ghi chú triệu chứng hoặc mức độ no.
- Ghi đường huyết trước/sau ăn nếu phù hợp phạm vi sản phẩm.
- Lưu thời gian và nguồn dữ liệu.

Sau khi lưu, dashboard phải cập nhật ngay mức tuân thủ và chỉ số liên quan.

## 6. Cải thiện dashboard chuyên gia

Dashboard chuyên gia nên tập trung vào công việc cần xử lý, không chỉ hiển thị số liệu tổng hợp.

### KPI cần có

- Số thực đơn đang chờ duyệt.
- Số cảnh báo mức cao chưa xử lý.
- Số bệnh nhân cần chú ý.
- Số thực đơn đã duyệt hôm nay.
- Thời gian xử lý trung vị trong khoảng thời gian xác định.

Nếu chưa có dữ liệu, dùng “Chưa có dữ liệu trong kỳ” thay vì dấu gạch hoặc câu “chưa có API tổng hợp”.

### Hàng chờ phê duyệt

Mỗi dòng cần hiển thị:

- Tên hoặc mã bệnh nhân.
- Bệnh nền và thuốc quan trọng.
- Ngày áp dụng thực đơn.
- Số cảnh báo theo mức độ.
- Người hoặc hệ thống tạo bản nháp.
- Thời điểm cập nhật gần nhất.
- Hành động “Xem xét”.

Không nên cho phép phê duyệt khi chuyên gia chưa mở review packet. Với sản phẩm lâm sàng, tốc độ không được đánh đổi bằng việc bỏ qua thông tin an toàn.

### Màn hình review

Màn hình review cần gom đủ thông tin để ra quyết định:

- Hồ sơ lâm sàng liên quan.
- Mục tiêu dinh dưỡng và nguồn thiết lập mục tiêu.
- Tổng dinh dưỡng cả ngày và theo từng bữa.
- Danh sách cảnh báo theo mức độ.
- Tương tác thuốc - thực phẩm.
- Dị ứng và thực phẩm cần tránh.
- Lý do AI chọn món.
- Nguồn dữ liệu của món và chất dinh dưỡng.
- Thay đổi so với phiên bản trước.
- Ô ghi chú bắt buộc khi sửa hoặc từ chối.

Các hành động cuối:

- **Yêu cầu chỉnh sửa**.
- **Lưu bản nháp**.
- **Phê duyệt và phát hành**.

Hệ thống cần xác nhận lần cuối trước khi phát hành và ghi đầy đủ audit log.

### So sánh phương án

Nếu AI tạo nhiều phương án, chuyên gia cần so sánh theo:

- Năng lượng.
- Carbohydrate và phân bổ theo bữa.
- Protein, chất béo và chất xơ.
- GI/GL khi có dữ liệu.
- Số cảnh báo.
- Mức phù hợp với khẩu vị và ngân sách.
- Mức độ dễ chuẩn bị.
- Tỷ lệ món có nguồn dữ liệu đầy đủ.

## 7. Nguồn dữ liệu và khả năng giải thích

“Dữ liệu có nguồn” chỉ có giá trị khi người dùng có thể kiểm tra được nguồn đó.

### Với mỗi món ăn

- Thành phần và khẩu phần chuẩn.
- Nguồn dữ liệu dinh dưỡng.
- Ngày hoặc phiên bản dữ liệu.
- Mức độ đầy đủ của các chất dinh dưỡng.
- Cách tính tổng từ nguyên liệu lên món.

### Với mỗi mục tiêu lâm sàng

- Giá trị mục tiêu.
- Đơn vị và khoảng thời gian áp dụng.
- Nguồn hướng dẫn.
- Đối tượng áp dụng.
- Điều kiện loại trừ.
- Người xác nhận mục tiêu cho bệnh nhân.

### Với mỗi cảnh báo

- Mã quy tắc.
- Mức độ nghiêm trọng.
- Dữ liệu đầu vào đã kích hoạt quy tắc.
- Nguồn tham chiếu.
- Hành động đề xuất.
- Trạng thái đã được chuyên gia xem xét hay chưa.

## 8. An toàn lâm sàng và quản trị AI

VNutriCare nên biến nguyên tắc “AI không tự quyết định” thành hành vi hệ thống có thể kiểm chứng.

### Quy tắc phát hành

- Bản nháp do AI tạo không hiển thị cho người bệnh.
- Chỉ phiên bản được chuyên gia phê duyệt mới được phát hành.
- Sau phê duyệt, mọi thay đổi tạo ra một phiên bản mới.
- Phiên bản mới phải được phê duyệt lại trước khi thay thế bản đang dùng.
- Người bệnh luôn nhìn thấy thời điểm và người phê duyệt.

### Audit log

Cần lưu:

- Ai tạo bản nháp.
- Model và phiên bản workflow đã sử dụng.
- Quy tắc nào đã chạy.
- Cảnh báo nào được tạo hoặc bỏ qua.
- Ai chỉnh sửa nội dung nào.
- Ai phê duyệt, từ chối hoặc phát hành.
- Thời gian từng hành động.

### Giới hạn trách nhiệm

Giao diện cần nói rõ:

- Sản phẩm hỗ trợ quản lý dinh dưỡng, không thay thế chẩn đoán hoặc điều trị.
- Người dùng cần liên hệ cơ sở y tế khi có triệu chứng bất thường.
- Khuyến nghị chỉ áp dụng trong phạm vi hồ sơ và dữ liệu hiện có.
- Dữ liệu thiếu hoặc không chắc chắn phải được thể hiện thay vì suy đoán.

## 9. Dữ liệu demo cần chuẩn bị

Bộ dữ liệu demo nên có ít nhất ba hồ sơ, mỗi hồ sơ minh họa một tình huống khác nhau.

### Hồ sơ 1: T2DM tương đối ổn định

- Có mục tiêu carbohydrate rõ ràng.
- Không có dị ứng.
- Có một thực đơn đạt toàn bộ mục tiêu.
- Có bảy ngày nhật ký để hiển thị tiến độ tốt.

### Hồ sơ 2: T2DM và dị ứng thực phẩm

- Có ít nhất một món bị loại do dị ứng.
- AI đề xuất món thay thế.
- Chuyên gia xem lý do và phê duyệt phương án an toàn.

### Hồ sơ 3: T2DM có thuốc hoặc bệnh nền cần chú ý

- Có một cảnh báo tương tác hoặc giới hạn dinh dưỡng.
- Bản nháp đầu tiên chưa thể phê duyệt.
- Chuyên gia chỉnh món hoặc khẩu phần.
- Phiên bản sau chỉnh sửa đạt điều kiện phát hành.

Mỗi hồ sơ cần có dữ liệu xuyên suốt: thông tin lâm sàng, mục tiêu, thực đơn, cảnh báo, review, phê duyệt, nhật ký và mức tuân thủ.

## 10. Các trạng thái giao diện cần hoàn thiện

Mỗi màn hình phải được kiểm tra ở bốn trạng thái.

### Loading

- Có skeleton hoặc spinner đúng vị trí.
- Không làm bố cục thay đổi đột ngột.
- Có giới hạn thời gian trước khi chuyển sang trạng thái lỗi.

### Empty

- Giải thích vì sao chưa có dữ liệu.
- Đưa ra hành động tiếp theo phù hợp.
- Không hiển thị dashboard đầy dấu gạch.

### Error

- Nội dung thân thiện, không lộ chi tiết kỹ thuật.
- Có nút thử lại.
- Có mã tham chiếu để tra log khi cần.

### Success

- Xác nhận thao tác hoàn thành.
- Cho biết dữ liệu nào vừa thay đổi.
- Với phê duyệt, cho biết thực đơn đã phát hành hay mới chỉ được lưu.

## 11. Khả năng sử dụng và thiết kế

### Nội dung và thuật ngữ

- Dùng nhất quán “người bệnh”, “chuyên gia dinh dưỡng” và “thực đơn”.
- Không trộn “bác sĩ”, “chuyên gia” và “tư vấn viên” nếu quyền hạn khác nhau.
- Viết đơn vị sát số liệu: `45 g carbohydrate`, `1.650 kcal/ngày`.
- Giải thích GI/GL lần đầu xuất hiện.
- Tránh từ kỹ thuật nội bộ trong nội dung cho người dùng.

### Responsive

- Dashboard dùng tốt trên màn hình laptop phổ biến.
- Người bệnh thao tác thuận tiện trên điện thoại.
- Bảng chuyên gia chuyển thành danh sách ưu tiên trên màn hình hẹp.
- CTA và nút hành động không tràn chữ hoặc chồng lên nhau.

### Accessibility

- Có label cho input và tên truy cập cho icon button.
- Màu cảnh báo không phải tín hiệu duy nhất.
- Có focus state rõ khi dùng bàn phím.
- Độ tương phản đáp ứng mức phù hợp.
- Ảnh món ăn có alt text đúng nội dung.
- Biểu đồ có phần tóm tắt bằng văn bản.

## 12. Kịch bản demo đề xuất

Một kịch bản 5-7 phút nên đi theo một ca bệnh duy nhất:

1. Mở landing và giới thiệu bài toán T2DM với món Việt.
2. Bấm “Demo chuyên gia”.
3. Mở một bệnh nhân có thuốc hoặc dị ứng cần chú ý.
4. Xem mục tiêu và các phương án thực đơn AI đề xuất.
5. Mở một cảnh báo, kiểm tra lý do và nguồn tham chiếu.
6. Thay món hoặc chỉnh khẩu phần để xử lý cảnh báo.
7. Phê duyệt và phát hành thực đơn.
8. Chuyển sang “Demo người bệnh”.
9. Chứng minh chỉ phiên bản đã phê duyệt được hiển thị.
10. Ghi một bữa ăn và quan sát mức tuân thủ cập nhật.

Kịch bản này thể hiện đủ giá trị cốt lõi: dữ liệu món Việt, cá nhân hóa, kiểm tra an toàn, human-in-the-loop và theo dõi sau phát hành.

## 13. Thứ tự ưu tiên triển khai

### P0 - Bắt buộc trước buổi trình bày

1. Tạo đăng nhập demo một chạm cho hai vai trò.
2. Seed ba hồ sơ mẫu có dữ liệu xuyên suốt.
3. Loại bỏ toàn bộ dấu gạch và câu “chưa có API” khỏi production UI.
4. Đảm bảo mọi CTA và menu chính đều hoạt động.
5. Hoàn thiện một workflow phê duyệt từ đầu đến cuối.
6. Chỉ cho người bệnh xem thực đơn đã được phê duyệt.
7. Kiểm tra sức khỏe backend trước buổi demo.
8. Chuẩn bị cơ chế đặt lại dữ liệu demo.

### P1 - Tăng sức thuyết phục

1. Thêm biểu đồ tuân thủ bảy ngày.
2. Thêm KPI công việc cho chuyên gia.
3. Hiển thị carbohydrate và GI/GL theo bữa.
4. Cho mở nguồn dữ liệu từ món và cảnh báo.
5. Thêm so sánh nhiều phương án thực đơn.
6. Hiển thị lịch sử phiên bản và audit log cơ bản.
7. Thêm ảnh đúng cho các món trong demo.

### P2 - Hoàn thiện sau demo

1. Bổ sung trao đổi giữa người bệnh và chuyên gia.
2. Theo dõi xu hướng đường huyết khi có phạm vi dữ liệu phù hợp.
3. Hoàn thiện audit log và quyền truy cập.
4. Đánh giá chất lượng đề xuất theo từng nhóm bệnh nhân.
5. Kiểm thử accessibility và responsive toàn bộ luồng.
6. Bổ sung giám sát lỗi frontend/backend trên môi trường deploy.

## 14. Tiêu chí nghiệm thu bản deploy tiếp theo

Bản deploy được coi là sẵn sàng trình bày khi đáp ứng tất cả điều kiện sau:

- Truy cập từng vai trò demo trong tối đa một lần bấm từ trang đăng nhập.
- Không có dashboard trống, KPI bằng dấu gạch hoặc thông báo kỹ thuật nội bộ.
- Có ít nhất một thực đơn chờ duyệt và một thực đơn đã phát hành.
- Có ít nhất một cảnh báo lâm sàng với lý do, nguồn và hướng xử lý.
- Có dữ liệu nhật ký tối thiểu bảy ngày để hiển thị xu hướng.
- Tất cả CTA và menu chính đều dẫn đến màn hình hoạt động.
- Người bệnh không thể xem bản nháp chưa được phê duyệt.
- Dữ liệu demo không chứa thông tin cá nhân thật.
- Ảnh và tài nguyên chính không phụ thuộc URL bên ngoài không kiểm soát.
- Có thể đặt lại dữ liệu demo mà không sửa trực tiếp database.
- Luồng chính hoạt động trên desktop và mobile.
- Không có lỗi nghiêm trọng trong console hoặc request API của hành trình demo.

## 15. Kết luận

VNutriCare không cần mở rộng thành một nền tảng quá lớn ở giai đoạn hiện tại. Giá trị khác biệt nằm ở việc giải quyết sâu bài toán thực đơn món Việt cho người đái tháo đường type 2, sử dụng dữ liệu có nguồn, kiểm tra an toàn và bắt buộc chuyên gia phê duyệt.

Ưu tiên quan trọng nhất là biến các giá trị này thành một hành trình có thể quan sát trực tiếp trên bản deploy. Khi người xem có thể vào demo trong một lần bấm, theo dõi một ca bệnh xuyên suốt, mở được nguồn cảnh báo và chứng kiến thực đơn chỉ xuất hiện sau phê duyệt, VNutriCare sẽ thể hiện rõ cả năng lực sản phẩm lẫn độ nghiêm túc về an toàn lâm sàng.
