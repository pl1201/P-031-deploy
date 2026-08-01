# Product Requirements Document (PRD)

## 1. Thông tin sản phẩm

- **Tên:** NutriCare Agent (VNutrCare AI Agent)
- **Phiên bản:** MVP / Build Phase
- **Thời gian:** 5 tuần
- **Đối tượng:** bệnh nhân mạn tính tại Việt Nam và bác sĩ/chuyên gia dinh dưỡng
- **Trạng thái dữ liệu:** 100% dữ liệu bệnh nhân mô phỏng; không dùng dữ liệu định danh thật

## 2. Bối cảnh và vấn đề

Bệnh nhân đái tháo đường type 2, tăng huyết áp, bệnh thận mạn và gout phải đồng thời kiểm soát nhiều ngưỡng dinh dưỡng (năng lượng, protein, natri, kali, phospho, purine...). Món Việt và gia vị/nước chấm khó định lượng, trong khi tư vấn 1-1 của chuyên gia tốn thời gian và không mở rộng được. Với bệnh đa bệnh lý, khuyến nghị giữa các guideline có thể xung đột.

LLM có thể diễn đạt tự nhiên nhưng không được phép tự bịa số dinh dưỡng hoặc bỏ qua dị ứng, tương tác thuốc-thực phẩm. Vì vậy sản phẩm cần tạo thực đơn cá nhân hóa có thể truy xuất nguồn, kiểm tra bằng luật xác định và luôn có chuyên gia duyệt trước khi gửi bệnh nhân.

## 3. Mục tiêu và chỉ số thành công

### Mục tiêu

1. Giúp chuyên gia tạo và duyệt thực đơn cá nhân hóa nhanh hơn.
2. Giúp bệnh nhân hiểu thực đơn Việt Nam và lý do lựa chọn món.
3. Ngăn thực đơn vi phạm ngưỡng lâm sàng, dị ứng hoặc tương tác thuốc-thực phẩm.
4. Cung cấp bằng chứng và audit trail cho mọi kết quả được hiển thị.

### KPIs nghiệm thu MVP

| Chỉ số | Mục tiêu |
|---|---:|
| Giá trị dinh dưỡng có `source` và `source_ref` | 100% |
| Bắt đúng kịch bản tương tác nguy hiểm trong bộ red-team | >= 90% |
| Thực đơn đạt luật sau tối đa 3 lần sinh/điều chỉnh | >= 95% |
| Thời gian chuyên gia duyệt một thực đơn | < 2 phút |
| Chặn câu hỏi kê đơn/chỉnh thuốc | >= 95% |
| Hồ sơ demo sử dụng dữ liệu thật | 0 |

## 4. Người dùng và quyền hạn

### Bệnh nhân/người nhà

- Xem hồ sơ và thực đơn đã được duyệt.
- Xem khẩu phần, tổng dinh dưỡng, cảnh báo và nguồn giải thích.
- Gửi phản hồi hoặc yêu cầu chuyên gia xem lại.
- Không được xem thực đơn ở trạng thái nháp/chưa duyệt.

### Bác sĩ/chuyên gia dinh dưỡng

- Tạo/cập nhật hồ sơ lâm sàng và mục tiêu dinh dưỡng.
- Yêu cầu AI lập thực đơn.
- Xem cảnh báo, nguồn dữ liệu, lý do từng lựa chọn.
- Sửa món/khẩu phần, duyệt hoặc từ chối kèm lý do.
- Xem lịch sử thay đổi và người duyệt.

## 5. Phạm vi

### In scope (MVP)

- Hồ sơ: chẩn đoán, bệnh kèm, giai đoạn bệnh, nhân trắc, hoạt động, dị ứng, thuốc, sở thích và thực phẩm/món tham chiếu.
- Tính năng lượng và dinh dưỡng bằng deterministic clinical core: kcal, protein, carbohydrate, chất béo, natri; mở rộng kali/phospho/purine theo dữ liệu/rule đã có.
- Bộ quy tắc ngưỡng lâm sàng và precedence khi guideline xung đột (ví dụ CKD ưu tiên giới hạn protein an toàn hơn mục tiêu chung của ĐTĐ2).
- Cảnh báo dị ứng và tương tác thuốc-thực phẩm từ danh mục đã kiểm duyệt.
- Agent LangGraph: parse ý định/thực thể, chọn món + gram, gọi clinical core, kiểm tra, sửa/sinh lại, diễn đạt bằng RAG.
- Hàng đợi Human-in-the-Loop: chuyên gia sửa, duyệt hoặc từ chối.
- Truy xuất nguồn cho từng số dinh dưỡng và audit log.
- API FastAPI hiện có; giao diện web cho hai vai trò.

### Out of scope (MVP)

- Chẩn đoán, kê đơn, khuyến nghị liều hoặc ngừng/đổi thuốc.
- Tự động phát hành thực đơn chưa được chuyên gia duyệt.
- Nhận diện ảnh mâm cơm, wearable/Apple Health.
- Điều trị đa bệnh lý ngoài các rule và dữ liệu MVP.
- Fine-tune mô hình từ đầu, dữ liệu bệnh nhân thật, thanh toán và giao hàng thực phẩm.

## 6. Tính năng và yêu cầu nghiệm thu

### F1. Quản lý hồ sơ

Người dùng nhập ngày sinh, giới tính, cân nặng, chiều cao, BMI/nhân trắc, mức hoạt động, chẩn đoán và giai đoạn bệnh, bệnh kèm, thuốc, dị ứng, mục tiêu và sở thích. Hệ thống kiểm tra trường bắt buộc; thiếu hồ sơ thì không cho tạo thực đơn và chỉ rõ trường cần bổ sung.

**Nghiệm thu:** hồ sơ hợp lệ được lưu; hồ sơ thiếu bệnh/thuốc/dị ứng hoặc nhân trắc bị chặn; dữ liệu demo được gắn mã mô phỏng.

### F2. Tạo thực đơn

Chuyên gia chọn bệnh nhân và khoảng thời gian/bữa ăn, sau đó bấm **Lập thực đơn**. Agent chỉ trả về định danh món và khối lượng; clinical core tra CSDL và tính mọi con số. Mỗi món có khẩu phần, thành phần, tổng dinh dưỡng, cảnh báo và nguồn.

**Nghiệm thu:** không có trường số dinh dưỡng do LLM sinh; kết quả có thể tái lập từ cùng input và phiên bản dữ liệu; lỗi thiếu dữ liệu khiến hệ thống fail-closed.

### F3. Kiểm tra an toàn và tự điều chỉnh

Validator kiểm tra ngưỡng năng lượng/dinh dưỡng, dị ứng, chống chỉ định, tương tác thuốc-thực phẩm và xung đột guideline. Nếu không đạt, hệ thống nêu lý do cụ thể, thay món/khẩu phần và sinh lại tối đa cấu hình (mặc định 3) lần. Hết lượt hoặc còn nghi ngờ thì chuyển chuyên gia, không phát hành.

**Nghiệm thu:** ca vượt natri/protein hoặc có cặp tương tác bị chặn; cảnh báo đỏ hiển thị trước nút duyệt; mọi lần sửa có log.

### F4. Duyệt thực đơn (HITL)

Chuyên gia xem hàng đợi bản nháp, bộ chỉ số so với mục tiêu, cảnh báo và nguồn. Có thể sửa món/gram, ghi chú, **Duyệt**, hoặc **Từ chối** với lý do. Sau khi sửa, tổng dinh dưỡng được tính lại tự động.

**Nghiệm thu:** chỉ trạng thái `approved` mới hiển thị cho bệnh nhân; bản từ chối quay lại chỉnh sửa; lưu người duyệt, thời điểm, phiên bản và lý do.

### F5. Xem và giải thích cho bệnh nhân

Bệnh nhân xem thực đơn đã duyệt theo ngày/bữa, khẩu phần và tổng ngày. Nút “Vì sao?” mở giải thích dựa trên rule/guideline và nguồn; không đưa lời khuyên kê đơn. Có thể xem cảnh báo và gửi phản hồi.

**Nghiệm thu:** bệnh nhân không truy cập được draft/rejected; giải thích không chứa số không có nguồn; disclaimer y tế luôn hiển thị.

### F6. An toàn, phân quyền và audit

Input guard từ chối câu hỏi chẩn đoán/kê đơn/chỉnh thuốc và hướng người dùng đến chuyên gia. Phân quyền tách bệnh nhân và chuyên gia. Ghi log request, phiên bản rule/model, dữ liệu nguồn, kết quả validator và hành động duyệt; không ghi secret hay PII thật.

## 7. Luồng nghiệp vụ chính

1. Chuyên gia đăng nhập, chọn/tạo hồ sơ mô phỏng.
2. Hệ thống kiểm tra đủ hồ sơ lâm sàng, nhân trắc, dị ứng/thuốc và sở thích.
3. Agent parse yêu cầu và chọn món/gram từ CSDL.
4. Clinical core tính dinh dưỡng; validator kiểm tra ngưỡng, dị ứng, tương tác.
5. Không đạt: điều chỉnh/sinh lại; đạt: tạo bản nháp và đưa vào hàng đợi.
6. Chuyên gia xem nguồn, sửa nếu cần, duyệt hoặc từ chối.
7. Bệnh nhân chỉ xem bản đã duyệt và có thể gửi phản hồi.

## 8. Dữ liệu và yêu cầu kỹ thuật

- Nguồn thực phẩm ưu tiên NIN/Bảng thành phần thực phẩm Việt Nam 2007, sau đó USDA; dữ liệu ước tính phải gắn nhãn `estimated` và công thức.
- Các bảng tối thiểu: `patients`, `clinical_profiles`, `foods/dishes`, `drug_food_interactions`, `clinical_rules`, `meal_plans`, `meal_items`, `approvals`, `audit_logs`.
- API: `GET /health`, `GET /api/v1/status`, `POST /api/v1/chat`; bổ sung endpoint hồ sơ, tạo thực đơn, duyệt/từ chối theo schema Pydantic.
- Backend FastAPI/Python; LangGraph/LangChain; PostgreSQL + pgvector (SQLite cho dev); frontend Next.js.
- Mọi số phải được tính ngoài LLM; clinical core không import LLM.

## 9. Phi chức năng

- **An toàn:** fail-closed, xác thực/phân quyền, mã hóa khi truyền, không lưu dữ liệu thật.
- **Truy vết:** 100% kết quả có nguồn và phiên bản dữ liệu/rule.
- **Hiệu năng:** phản hồi tạo bản nháp mục tiêu < 30 giây; thao tác UI thông thường < 2 giây (không tính LLM).
- **Độ tin cậy:** lỗi LLM/DB không tạo hoặc phát hành thực đơn; retry có giới hạn và thông báo rõ.
- **Kiểm thử:** unit test clinical core, integration test graph/API, red-team tương tác thuốc và test phân quyền trong CI.

## 10. Kế hoạch 5 tuần

| Tuần | Kết quả bắt buộc |
|---|---|
| 1 | Chốt schema, rule, nguồn dữ liệu, seed mô phỏng và API hồ sơ |
| 2 | Hoàn thiện clinical core, validator, tương tác thuốc và test hồi quy |
| 3 | Tích hợp LangGraph, structured output, retry/fail-closed, audit log |
| 4 | UI bệnh nhân/chuyên gia, hàng đợi HITL, gọi API end-to-end |
| 5 | Eval 60 hồ sơ, red-team, bảo mật, deploy, demo và tài liệu |

## 11. Rủi ro và quyết định

- **Thiếu/không đồng nhất dữ liệu món Việt:** gắn nguồn từng dòng, đánh dấu ước tính, review R2 trước merge.
- **LLM hallucination:** schema giới hạn food_id + gram; mọi số do Python/SQL tính.
- **Xung đột guideline:** rule precedence được cấu hình và hiển thị cho chuyên gia; nghi ngờ thì chặn.
- **Trách nhiệm y khoa:** disclaimer, dữ liệu mô phỏng, HITL bắt buộc; không dùng production cho bệnh nhân thật trong MVP.
- **Scope creep:** ưu tiên luồng tạo–kiểm tra–duyệt–xem; ảnh và wearable để phiên bản sau.

## 12. Tiêu chí hoàn thành (Definition of Done)

- Luồng F1–F6 chạy được từ API/UI với dữ liệu mô phỏng.
- `make check` xanh; dữ liệu qua `scripts/validate_data.py`.
- Bộ eval có báo cáo số liệu thực, không để placeholder `__`/`[VERIFY]`.
- Có bằng chứng 100% số hiển thị truy xuất được nguồn và test tương tác đạt KPI.
- Deploy được backend/frontend, có health check, README và video/pitch demo cập nhật.
