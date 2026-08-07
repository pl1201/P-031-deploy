# Product Requirements Document (PRD) - VNutriCare

> **Đề bài:** VMEC-10 - AI20K Build Cohort 3  
> **Phiên bản:** 2.2  
> **Phạm vi:** MVP 6 tuần, sử dụng dữ liệu thực tế từ nguồn công khai (NHANES 2021-2023) để phát triển và kiểm thử  
> **Bệnh lý trọng tâm:** Đái tháo đường type 2 (ĐTĐ2)  
> **Nguồn yêu cầu chính:** `KeHoachDuAn_VNutriCare_VMEC10_v3.docx`

## 1. Mục đích tài liệu

PRD này xác định sản phẩm sẽ làm gì trong MVP: danh sách tính năng, luồng dữ liệu, tiêu chí nghiệm thu, yêu cầu phi chức năng, ràng buộc an toàn và phần để lại cho các phiên bản sau.

Đây không phải guideline điều trị và không thay thế quyết định của bác sĩ. MVP sử dụng dữ liệu bệnh nhân thực tế đã được công khai (de-identified) từ nguồn nghiên cứu có uy tín để phát triển và kiểm thử hệ thống, nhưng không được tuyên bố hiệu quả lâm sàng trên bệnh nhân thật.

## 2. Tổng quan sản phẩm

### 2.1. Định vị

- **Tên:** VNutriCare.
- **Loại sản phẩm:** AI Agent hỗ trợ chuyên gia lập và duyệt thực đơn dinh dưỡng lâm sàng.
- **Người dùng đích:** người trưởng thành đã được chuyên gia xác nhận đái tháo đường type 2; người chăm sóc; bác sĩ/chuyên gia dinh dưỡng.
- **Chế độ ăn tham chiếu:** nguyên tắc kiểm soát carbohydrate, chỉ số đường huyết (GI/GL), phân bổ bữa ăn đều và thực phẩm ít chế biến.
- **Người quyết định cuối:** bác sĩ hoặc chuyên gia dinh dưỡng.
- **Nguyên tắc kỹ thuật:** LLM chỉ chọn món và diễn đạt; Python/SQL tính định mức, tính dinh dưỡng và kiểm tra an toàn.

### 2.2. Ranh giới bệnh lý

MVP **tập trung vào đái tháo đường type 2** với các rule carbohydrate, GI/GL, phân bổ bữa ăn và HbA1c trong phạm vi nghiệm thu.

MVP không xây tính năng điều trị mới chuyên biệt cho CKD, gout, tăng huyết áp nặng hoặc đa bệnh lý phức tạp. Cơ chế đa bệnh lý hiện có vẫn áp dụng các rule đã được xác minh và chọn ngưỡng nghiêm ngặt hơn theo DEC-014; không gắn cờ chỉ vì hồ sơ có bệnh đồng mắc.

Hệ thống chỉ gắn `needs_expert_review`, không tự kết luận thực đơn an toàn và hiển thị rõ lý do khi rule thật sự xung đột (`min > max`, dải khả thi quá hẹp), rule bị vô hiệu bởi cờ an toàn, hoặc dữ liệu bắt buộc còn thiếu/chưa xác minh. Rule ngoài phạm vi chưa được xác minh không được kích hoạt như phác đồ điều trị.

## 3. Vấn đề cần giải quyết

Người đái tháo đường type 2 tại Việt Nam khó kiểm soát đường huyết vì carbohydrate tập trung trong cơm, bún, phở, bánh mì, nước ngọt và thực phẩm đóng gói. Các ứng dụng đếm calo phổ thông thường thiếu dữ liệu món Việt, không có chỉ số GI/GL, không kiểm tra tương tác thuốc - thực phẩm và không có quy trình chuyên gia duyệt.

LLM có thể tạo thực đơn tự nhiên nhưng không đủ tin cậy để tự sinh hàm lượng dinh dưỡng. VNutriCare phải tách phần sinh gợi ý khỏi phần tính số, truy vết từng giá trị về nguồn và chặn phát hành khi thiếu dữ liệu hoặc còn cảnh báo nghiêm trọng.

## 4. Mục tiêu và không mục tiêu

### 4.1. Mục tiêu MVP

1. Rút ngắn thời gian chuyên gia lập và duyệt một thực đơn ĐTĐ2 cá nhân hóa.
2. Bảo đảm 100% giá trị dinh dưỡng hiển thị có nguồn và có thể tính lại.
3. Phát hiện thực đơn vượt ngưỡng carbohydrate, năng lượng hoặc các ràng buộc ĐTĐ2 đã được xác minh.
4. Phát hiện dị ứng và tương tác thuốc - thực phẩm liên quan ĐTĐ2 trong danh mục curated.
5. Bắt buộc chuyên gia sửa, duyệt hoặc từ chối trước khi bệnh nhân nhận thực đơn.
6. Thu thập nhật ký ăn uống và phản hồi để chuyên gia xem lại.
7. Tạo bằng chứng định lượng cho RQ1 (groundedness), RQ2 (HITL) và RQ5 (tương tác thuốc).

### 4.2. Không mục tiêu

- Không chẩn đoán đái tháo đường hoặc các biến chứng.
- Không kê đơn, đổi/ngừng thuốc hoặc thay đổi liều.
- Không thay thế bác sĩ/chuyên gia dinh dưỡng.
- Không điều trị tăng huyết áp nặng, CKD, gout hoặc đa bệnh lý phức tạp trong MVP.
- Không chứng minh hệ thống làm giảm HbA1c hoặc biến chứng ĐTĐ2.
- Không ước tính dinh dưỡng trực tiếp từ ảnh.
- Không kết nối wearable, HealthKit, Health Connect, CGM hoặc bệnh án điện tử.
- Không fine-tune mô hình từ đầu.

## 5. Người dùng và quyền hạn

### 5.1. Bệnh nhân

- Xem thực đơn đã duyệt, khẩu phần, tổng dinh dưỡng và nguồn.
- Xem hướng dẫn ăn/chế biến đã được duyệt.
- Ghi nhật ký ăn thực tế và gửi phản hồi.
- Không xem bản nháp, bản bị từ chối hoặc hồ sơ người khác.

### 5.2. Người nhà/người chăm sóc

- Được cấp quyền vào một hồ sơ cụ thể.
- Xem thực đơn đã duyệt, ghi nhật ký hộ và bổ sung thông tin món có sẵn.
- Không thay đổi mục tiêu lâm sàng hoặc duyệt thực đơn.

### 5.3. Bác sĩ/chuyên gia dinh dưỡng

- Tạo/cập nhật hồ sơ, mục tiêu và ngoại lệ lâm sàng.
- Yêu cầu agent tạo thực đơn nháp.
- Xem nguồn, vi phạm, cảnh báo và lý do lựa chọn.
- Sửa món/gram, tính lại, duyệt hoặc từ chối kèm lý do.
- Xem nhật ký và lịch sử phiên bản.

### 5.4. Quản trị viên

- Quản lý tài khoản mô phỏng, vai trò và cấu hình.
- Quản lý phiên bản dataset/rule sau khi nội dung được phê duyệt.
- Xem log vận hành; không có quyền duyệt lâm sàng mặc định.

## 6. Dữ liệu đầu vào

### 6.1. Dữ liệu tri thức nền

| Nhóm | Nguồn/chiến lược | Cách dùng | Điều kiện |
|---|---|---|---|
| Thành phần thực phẩm Việt | Bảng thành phần thực phẩm Việt Nam 2007; đối chiếu bản 2017 khi tiếp cận được | Nguồn ưu tiên cho nguyên liệu, gia vị và nước chấm Việt | Mỗi giá trị có `source_ref`; kiểm tra quyền sử dụng |
| Thực phẩm bổ sung | USDA FoodData Central | Bổ sung nguyên liệu thiếu trong nguồn Việt | Lưu `fdcId`, trạng thái sống/chín và mô tả bản ghi đã ghép |
| Món ăn Việt | Công thức curated, mục tiêu tối thiểu 80 món nếu đủ nguồn lực | Tính món từ nguyên liệu và khối lượng | Chuyên gia review; LLM không tự tạo số dinh dưỡng |
| Rule lâm sàng | WHO, AHA/DASH, Bộ Y tế và nguồn được phê duyệt | Tính mục tiêu và kiểm tra thực đơn | Rule `to_verify` không được kích hoạt như rule production |
| Tương tác thuốc | Danh mục curated theo hoạt chất | Cảnh báo trước khi duyệt | Có nguồn, mức độ, cơ chế và hành động cho từng cặp |
| Guideline văn bản | Tài liệu chính thống đã ingest | RAG để giải thích | Không dùng RAG để tính số dinh dưỡng |

### 6.2. Hồ sơ bệnh nhân v1

**Nguồn dữ liệu:** NHANES (National Health and Nutrition Examination Survey) 2021-2023, dữ liệu công khai đã được de-identified từ CDC/NCHS.

**Cách sử dụng:** Dữ liệu thực tế được sử dụng để phát triển, kiểm thử và đánh giá hệ thống trong giai đoạn nghiên cứu. Dữ liệu này tuân thủ NCHS Data User Agreement và chỉ được dùng cho mục đích phân tích thống kê, không được tái định danh.

Các trường cần thu thập:

- mã hồ sơ mô phỏng;
- tuổi, giới tính, chiều cao, cân nặng;
- mức hoạt động và mục tiêu cân nặng;
- chẩn đoán ĐTĐ2 do chuyên gia nhập;
- HbA1c gần nhất, ngày đo và nguồn nhập;
- đường huyết đói/sau ăn nếu có;
- thuốc đang dùng, gồm hoạt chất và tên biệt dược nếu có;
- dị ứng/không dung nạp;
- vùng miền, sở thích, món không ăn và thực phẩm sẵn có;
- ngân sách tiền ăn mỗi ngày theo khoảng, tùy chọn;
- mục tiêu riêng do chuyên gia đặt và lý do ghi đè mặc định.

Không hỏi tổng thu nhập gia đình. Sản phẩm chỉ cần ngân sách bữa ăn tùy chọn.

### 6.3. Dữ liệu sau v1

- Số đo vòng, InBody/BIA và thành phần cơ thể theo tháng.
- Xét nghiệm nhập tự động từ cơ sở y tế.
- Wearable, HealthKit/Health Connect.
- Dữ liệu theo dõi thật để đánh giá outcome lâm sàng.

## 7. Tính năng và tiêu chí nghiệm thu

### FR-01. Đăng nhập và phân quyền

**Mô tả:** cung cấp phiên đăng nhập cho bốn vai trò; mỗi API kiểm tra vai trò và phạm vi hồ sơ.

**Luồng:** thông tin đăng nhập -> xác thực -> phiên/token -> kiểm tra quyền -> cho phép hoặc từ chối.

**Nghiệm thu:**

- Bệnh nhân không truy cập được draft/rejected hoặc hồ sơ người khác.
- Người chăm sóc chỉ thấy hồ sơ được cấp quyền.
- Chỉ chuyên gia được duyệt/từ chối.
- Truy cập trái quyền trả lỗi phù hợp và có security log không chứa secret.

### FR-02. Quản lý hồ sơ

**Mô tả:** chuyên gia tạo hồ sơ nền từ dữ liệu NHANES hoặc nhập thủ công; bệnh nhân/người chăm sóc bổ sung sở thích trong phạm vi cho phép.

**Luồng:** form -> kiểm tra schema/đơn vị -> chuẩn hóa tên thuốc -> lưu phiên bản -> audit event.

**Nghiệm thu:**

- Chặn tạo thực đơn nếu thiếu nhân trắc, mức hoạt động, bệnh trọng tâm, danh sách thuốc hoặc xác nhận dị ứng.
- HbA1c/đường huyết có đơn vị, thời điểm và nguồn.
- Biệt dược phải được ánh xạ sang hoạt chất và xác nhận; không ghép được thì chuyển review.
- Hồ sơ có bệnh ngoài phạm vi được gắn `needs_expert_review`.
- Hồ sơ từ NHANES giữ nguyên trạng thái de-identified, không chứa SEQN hoặc định danh cá nhân trong giao diện người dùng.

### FR-03. Tính định mức xác định

**Mô tả:** clinical core tính BMR/TDEE và mục tiêu theo hồ sơ, mục tiêu chuyên gia và rule ĐTĐ2 đã xác minh.

**Luồng:** hồ sơ hợp lệ + rule version -> clinical core -> `ClinicalTargets`, `rule_ids`, `guideline_refs`, cờ xung đột.

**Nghiệm thu:**

- Cùng input và rule version luôn cho cùng kết quả.
- Carbohydrate tham chiếu theo % năng lượng hoặc gram tùy theo mục tiêu HbA1c; chuyên gia chỉ ghi đè khi có lý do và nguồn.
- Năng lượng, protein, carbohydrate, chất béo, chất xơ và đường tự do có đơn vị rõ ràng.
- Không tự động khuyên tăng kali khi thiếu thông tin chức năng thận, kali máu hoặc thuốc gây tăng kali.
- Thiếu dữ liệu, rule chưa xác minh hoặc xung đột phải fail-closed/chuyển chuyên gia.
- Clinical core không gọi LLM.

### FR-04. Tra cứu thực phẩm/món ăn có nguồn

**Luồng:** truy vấn -> chuẩn hóa alias -> SQL search -> lọc độ đầy đủ và nguồn -> ứng viên.

**Nghiệm thu:**

- Mỗi ứng viên có ID, trạng thái sống/chín, đơn vị, nguồn và phiên bản.
- Không tự gộp món trùng tên nhưng khác cách chế biến.
- Gia vị, nước chấm và nước dùng phải được tính như thành phần.
- Thiếu natri thì không được kết luận món/thực đơn đạt ngưỡng natri.
- Bản ghi `estimated` có nhãn và công thức, bắt buộc chuyên gia xem.

### FR-05. Sinh thực đơn nháp

**Mô tả:** LangGraph chọn món Việt và gram từ danh sách ứng viên theo mục tiêu, sở thích, vùng miền, dị ứng và ngân sách nếu có.

**Luồng:** hồ sơ + targets + ứng viên + feedback lần trước -> LLM structured output -> ID + gram theo bữa.

**Nghiệm thu:**

- Output LLM chỉ có `food_id`/`dish_id`, gram và bữa; không có kcal/natri/protein.
- ID lạ hoặc gram ngoài giới hạn bị từ chối.
- V1 tạo thực đơn một ngày; bảy ngày là stretch.
- Không có ứng viên an toàn thì báo không có lời giải, không tự bịa món.
- Lưu model, prompt và dataset version.

### FR-06. Tính dinh dưỡng

**Luồng:** menu IDs + gram -> food/recipe DB -> quy đổi trên 100 g -> tổng theo món/bữa/ngày -> `NutritionSummary` + `sources[]`.

**Nghiệm thu:**

- 100% số hiển thị truy về được bản ghi nguồn.
- Cùng menu và dataset version cho cùng kết quả.
- Không dùng giá trị do LLM sinh trong phép tính.
- Thiếu chất cần cho hard rule phải trả `incomplete_data`, không coi là 0.
- Sửa gram phải tính lại ngay mà không gọi LLM.

### FR-07. Validator an toàn ĐTĐ2

**Mô tả:** kiểm tra năng lượng, carbohydrate, GI/GL, phân bổ bữa ăn theo rule đã duyệt, dị ứng, tương tác thuốc và dữ liệu thiếu.

**Nghiệm thu:**

- Vượt hard limit, có dị ứng hoặc tương tác nghiêm trọng thì chặn phát hành.
- Mỗi violation có actual, limit, unit, severity, message, suggestion và nguồn/rule.
- Cảnh báo kali xét thuốc ACEi/ARB/thuốc giữ kali và thông tin thận nếu có; thiếu thì chuyển review.
- Không đưa ra kết luận điều chỉnh thuốc.
- Rule ngoài phạm vi không tự kích hoạt như một phác đồ điều trị.

### FR-08. Tự điều chỉnh có giới hạn

**Luồng:** violations -> feedback có cấu trúc -> sinh lại -> tính lại -> kiểm tra lại.

**Nghiệm thu:**

- Tối đa ba lần, có thể cấu hình.
- Mỗi lần đều tính lại từ database và lưu lịch sử.
- Hết lượt còn hard violation thì `needs_expert_review`, không phát hành.
- Không được hạ ngưỡng lâm sàng để làm menu pass.

### FR-09. Duyệt Human-in-the-Loop

**Luồng:** draft -> review queue -> thao tác chuyên gia -> tính/kiểm tra lại -> approved/rejected/revision_required.

**Nghiệm thu:**

- Chỉ `approved` mới hiển thị cho bệnh nhân/người chăm sóc.
- Khóa nút duyệt nếu còn hard violation hoặc thiếu nguồn bắt buộc.
- Override cảnh báo mềm phải có lý do.
- Lưu người duyệt, thời điểm, thay đổi trước/sau và mọi phiên bản liên quan.
- Tiếp tục được phiên review sau gián đoạn; có fallback trạng thái DB.

### FR-10. Xem và giải thích thực đơn đã duyệt

**Luồng:** approved plan + sources + guideline chunks -> diễn giải có ràng buộc -> UI.

**Nghiệm thu:**

- Chỉ dùng số đã tính và nội dung guideline truy xuất được.
- Hướng dẫn nấu không đổi nguyên liệu/gram đã duyệt.
- Ưu tiên hành động cụ thể: giảm nước chấm, không chan nước dùng, đọc nhãn natri, hạn chế gia vị mặn và thực phẩm siêu chế biến.
- Disclaimer y tế luôn hiển thị.

### FR-11. Nhật ký ăn uống và phản hồi

**Luồng:** món + gram/thời gian -> tìm ID -> tính -> tổng ngày -> cảnh báo/báo cáo.

**Nghiệm thu:**

- Món trong DB tính từ ID; món ngoài DB không được tự bịa số.
- Cho phép đánh dấu không rõ khẩu phần.
- Tổng carbohydrate và đường ngày có trạng thái đầy đủ/không đầy đủ.
- Cảnh báo nghiêm trọng đi vào hàng đợi chuyên gia.
- Lưu phản hồi về độ no, khẩu vị, khả năng mua và lý do không tuân thủ.

### FR-12. Tương tác thuốc - thực phẩm

**Luồng:** biệt dược -> ứng viên hoạt chất -> xác nhận -> tra cứu xác định -> cảnh báo có cấu trúc.

**Nghiệm thu:**

- Không tự chấp nhận ánh xạ thuốc mơ hồ.
- Mỗi cảnh báo có thuốc, thực phẩm/chất, mức độ, cơ chế, hành động và nguồn.
- Recall cho tương tác nghiêm trọng cao trong red-team đạt tối thiểu 90%; đồng thời báo cáo precision.
- Luôn khuyên trao đổi với bác sĩ, không thay đổi thuốc.

### FR-13. Audit và quản lý phiên bản

**Nghiệm thu:**

- Meal plan gắn profile, rule, dataset, recipe, model và prompt version.
- Log generate, compute, validate, retry, review và publish.
- Audit event append-only ở tầng ứng dụng.
- Không ghi token, mật khẩu, API key hoặc PII thật.

### FR-14. Quản trị dữ liệu và rule

**Nghiệm thu:**

- Chặn import khi thiếu nguồn, trùng định danh hoặc giá trị ngoài miền hợp lý.
- Chỉ kích hoạt rule có `verify_status=verified` và guideline reference cụ thể.
- Thay đổi tạo phiên bản mới, không sửa ngầm kết quả lịch sử.
- Có thể quay về phiên bản trước mà không xóa audit.

## 8. Luồng nghiệp vụ end-to-end

1. Chuyên gia tạo/chọn hồ sơ mô phỏng ĐTĐ2.
2. Bệnh nhân/người chăm sóc bổ sung sở thích, dị ứng, vùng miền, thực phẩm sẵn có và ngân sách tùy chọn.
3. Hệ thống kiểm tra hồ sơ, ánh xạ thuốc sang hoạt chất và yêu cầu xác nhận.
4. Clinical core tính mục tiêu kèm rule/source.
5. Agent lấy ứng viên có đủ dữ liệu và chỉ sinh ID + gram.
6. Clinical core tính mọi giá trị; validator kiểm tra dinh dưỡng, dị ứng và tương tác.
7. Menu vi phạm được sinh lại tối đa ba lần; còn lỗi thì chuyển chuyên gia.
8. Chuyên gia xem nguồn, sửa, tính lại, duyệt hoặc từ chối.
9. Bệnh nhân chỉ nhận thực đơn đã duyệt và ghi nhật ký thực tế.
10. Hệ thống tổng hợp nhật ký để chuyên gia xem lại và cập nhật mục tiêu.

## 9. Yêu cầu phi chức năng

### NFR-01. An toàn

- Fail-closed khi thiếu dữ liệu, nguồn, rule hoặc kết quả không chắc chắn.
- Không tự động phát hành.
- Chặn chẩn đoán, kê đơn và điều chỉnh thuốc.
- Cảnh báo có mức độ và hành động rõ ràng, tránh alert fatigue.

### NFR-02. Truy vết và tái lập

- 100% số dinh dưỡng hiển thị có nguồn.
- Cùng input và phiên bản phụ thuộc tái lập cùng kết quả tính.
- Không sửa/xóa dấu vết quyết định đã phát hành.

### NFR-03. Bảo mật và riêng tư

- MVP sử dụng dữ liệu NHANES đã được de-identified từ CDC/NCHS, tuân thủ NCHS Data User Agreement.
- RBAC và least privilege cho mọi truy cập dữ liệu.
- TLS khi truyền; secret qua biến môi trường/secret manager.
- Không đưa SEQN hoặc thông tin định danh vào prompt/log.
- Trước pilot dữ liệu bệnh nhân thực tế tại Việt Nam phải có đồng ý, đánh giá đạo đức và tuân thủ Nghị định 13/2023/NĐ-CP.

### NFR-04. Hiệu năng và độ tin cậy

- API/UI thông thường: mục tiêu p95 dưới 2 giây, không tính LLM.
- Tạo menu nháp: mục tiêu dưới 30 giây trong điều kiện demo.
- Sửa gram tính lại không cần LLM.
- Retry có giới hạn và idempotency; lỗi LLM/DB/RAG không tạo trạng thái approved.

### NFR-05. Khả dụng và kiểm thử

- Giao diện tiếng Việt, đơn vị quen thuộc, cảnh báo không chỉ dựa vào màu.
- Unit test clinical core; integration test graph/API/RBAC/HITL.
- Data validation trong CI.
- Red-team ép bịa số, bỏ qua dị ứng, chẩn đoán và đổi thuốc.

## 10. KPI và đánh giá

| Mã | Chỉ số | Mục tiêu | Cách đo |
|---|---|---:|---|
| RQ1-M1 | Giá trị dinh dưỡng có nguồn hợp lệ | 100% | Toàn bộ output/log eval |
| RQ1-M2 | Menu pass rule lần đầu | >= 70% | Bộ hồ sơ mô phỏng chuẩn hóa |
| RQ1-M3 | Menu pass sau tối đa 3 lần | >= 95% | Agent/validator log |
| RQ1-M4 | Sai lệch năng lượng so với mục tiêu | trong +/-10% | Clinical core |
| RQ2-M1 | Duyệt không sửa hoặc sửa nhẹ dưới 10% gram | >= 70% | So sánh draft/approved |
| RQ2-M2 | Thời gian duyệt trung bình | <= 2 phút | Tối thiểu 10 lượt trên UI |
| RQ5-M1 | Recall tương tác nghiêm trọng cao | >= 90% | Red-team gắn nhãn |
| SAFE-M1 | Phát hiện dị ứng trong test | 100% | Test tự động |
| SAFE-M2 | Chặn chẩn đoán/đổi thuốc | >= 95% | Prompt red-team |

Kết quả thực tế phải ghi tại `eval/results/report.md`, gồm cỡ mẫu, phiên bản dữ liệu/rule/model, case thất bại và giới hạn. Không thay mục tiêu bằng kết quả khi chưa đo.

## 11. Phạm vi phát hành

### 11.1. V1 bắt buộc

- Hồ sơ từ NHANES 2021-2023 và RBAC.
- Clinical core ĐTĐ2 với rule carbohydrate, GI/GL và phân bổ bữa ăn.
- Food DB có nguồn, ưu tiên carbohydrate/cơm/bún/phở/bánh.
- Menu một ngày, compute, validate và retry.
- Dị ứng và tương tác thuốc ĐTĐ2 curated.
- Dashboard HITL và màn hình bệnh nhân xem bản approved.
- Nhật ký ăn uống có tổng carbohydrate và đường.
- Audit, eval và deploy demo.

### 11.2. Stretch

- Phân rã mâm cơm bằng mô tả text, đối chiếu tối thiểu năm kịch bản chuyên gia.
- Ràng buộc ngân sách với giá thực phẩm có ngày/nguồn.
- Thực đơn bảy ngày, shopping list và biểu đồ xu hướng.

### 11.3. V2/V3

- Ảnh và ước tính khẩu phần; voice/TTS; đọc đơn thuốc từ ảnh.
- InBody/BIA, wearable, HealthKit/Health Connect và bệnh án điện tử.
- Dữ liệu bệnh nhân thật, nghiên cứu outcome và pilot tại bệnh viện.
- Hỗ trợ đái tháo đường type 2, CKD, gout và đa bệnh lý.

## 12. Lộ trình 6 tuần

| Tuần | Kết quả bắt buộc |
|---|---|
| 1 | Schema, nguồn, rule ĐTĐ2, dữ liệu NHANES, CI và health-check deploy |
| 2 | Clinical core, validator, dữ liệu carbohydrate/GI, API hồ sơ/targets và unit test |
| 3 | LangGraph, output ID + gram, compute, retry, guardrail và audit |
| 4 | HITL, RBAC, nhật ký và demo end-to-end |
| 5 | Tương tác thuốc, RAG giải thích và hoàn thiện UI; stretch chỉ khi luồng chính ổn định |
| 6 | Eval, red-team, expert review, sửa lỗi, deploy, video, pitch và code freeze |

## 13. Rủi ro chính

| Rủi ro | Biện pháp |
|---|---|
| Dữ liệu món Việt thiếu/sai carbohydrate và GI/GL | Ưu tiên cơm, bún, phở, bánh và nước ngọt; nguồn từng dòng; data/expert review |
| Dữ liệu NHANES không đại diện dân số Việt Nam | Ghi rõ limitation; bổ sung sở thích món Việt và vùng miền; không tuyên bố đại diện |
| Rule chưa xác minh | Chỉ kích hoạt rule verified; ghi phiên bản guideline; fail-closed |
| LLM bịa số/ID | Schema chỉ ID + gram; reject ID lạ; mọi số do Python/SQL tính |
| Ánh xạ sai tên thuốc | Xác nhận hoạt chất; không match thì review; bảng curated có nguồn |
| Nguy cơ tăng kali do thuốc/bệnh thận | Không mặc định tăng kali; kiểm tra thuốc/renal flag; chuyển chuyên gia |
| Cảnh báo quá nhiều | Severity có nghĩa, hành động cụ thể, interaction được curate |
| Không đủ thời gian | Ưu tiên generate-compute-validate-review-publish; cắt stretch trước |
| Tuyên bố quá mức | Chỉ báo cáo kết quả trên dữ liệu NHANES; không tuyên bố giảm HbA1c; ghi rõ không đại diện dân số Việt |

## 14. Definition of Done

MVP chỉ hoàn thành khi:

- FR-01 đến FR-13 chạy end-to-end trên API/UI; FR-14 có quy trình validate/kích hoạt tối thiểu.
- Không có đầu vào, output, rule hoặc màn hình nào mô tả tăng huyết áp nặng, CKD nặng, hoặc gout như bệnh được MVP hỗ trợ.
- Bệnh nhân không thể xem thực đơn chưa `approved`.
- Mọi số dinh dưỡng hiển thị có nguồn và tái lập được.
- Không hard violation nào được phát hành.
- Eval có kết quả thật, case thất bại và giới hạn; không còn placeholder.
- `make check` và data validation chạy thành công trong CI.
- Backend/frontend deploy được, health check hoạt động và tài liệu demo phản ánh đúng phạm vi.
- Dữ liệu NHANES được ghi rõ nguồn, ngày tải, và tuân thủ NCHS Data User Agreement.

## 15. Tài liệu liên quan

- `KeHoachDuAn_VNutriCare_VMEC10_v3.docx`: bối cảnh, luồng đối tượng/dữ liệu, RQ, bằng chứng và lộ trình.
- `brief.md`: định vị ĐTĐ2 và phạm vi cắt gọn.
- `docs/ARCHITECTURE.md`: kiến trúc và hợp đồng kỹ thuật.
- `docs/NGHIEN_CUU_BO_SUNG.md`, `docs/NGHIEN_CUU_BO_SUNG_v2.md`: bằng chứng, dataset và điểm cần xác minh.
- `data/README.md`: trạng thái dữ liệu, nguồn và quy trình nhập.
- `docs/TICKETS.md`: backlog triển khai.
- `UI_flow.md`: luồng màn hình; cần cập nhật riêng nếu không còn khớp PRD này.
