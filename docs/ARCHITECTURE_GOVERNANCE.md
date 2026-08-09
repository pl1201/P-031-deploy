# Architecture Governance — VNutriCare

## 1. Người chịu trách nhiệm

**Architecture Owner: R1 — Tech Lead / Agent Engineer.**

R1 là người chịu trách nhiệm cuối cùng (Accountable) về tính nhất quán của kiến trúc tổng thể. R1 không tự quyết các nội dung lâm sàng hoặc vận hành chuyên môn:

- R2 phải đồng duyệt quyết định liên quan clinical rules, dữ liệu dinh dưỡng, nguồn và tiêu chí an toàn.
- R3 phải đồng duyệt quyết định liên quan database, API, authentication, deployment, secrets và reliability.
- R4 phải được tham vấn đối với API contract, luồng HITL và thay đổi ảnh hưởng UX.

Architecture Owner có trách nhiệm:

1. Duy trì `docs/ARCHITECTURE.md` đúng với code đang chạy.
2. Viết hoặc yêu cầu ADR trước mọi thay đổi kiến trúc đáng kể.
3. Chạy architecture evaluation ở mỗi mốc release và trước demo chính thức.
4. Chặn merge khi vi phạm invariant an toàn, dù chức năng vẫn chạy.
5. Ghi rõ trade-off, rủi ro được chấp nhận, người phê duyệt và ngày xem xét lại.

## 2. Khi nào bắt buộc có ADR

ADR là bắt buộc nếu thay đổi thuộc một trong các nhóm sau:

- Thêm hoặc thay thế framework, database, vector store, model provider hoặc dịch vụ cloud.
- Thay đổi ranh giới giữa LLM và deterministic clinical core.
- Thay đổi schema hoặc API contract ảnh hưởng từ hai module trở lên.
- Thay đổi luồng phê duyệt HITL, RBAC, audit hoặc cách dữ liệu bệnh nhân đi qua hệ thống.
- Phát sinh chi phí vận hành định kỳ hoặc thêm một service phải deploy/monitor.
- Chấp nhận một rủi ro an toàn, bảo mật hoặc reliability chưa xử lý ngay.

Không cần ADR cho bug fix cục bộ, refactor không đổi behavior hoặc thay đổi UI thuần trình bày.

## 3. Quy trình quyết định

1. Người đề xuất tạo ADR ở trạng thái `Proposed` từ template trong `docs/adr/000-template.md`.
2. Architecture Owner kiểm tra ít nhất hai phương án khả thi và bằng chứng đo được.
3. R2/R3/R4 tham gia theo phạm vi tác động ở mục 1.
4. Architecture Owner chuyển ADR thành `Accepted`, `Rejected` hoặc `Deferred`.
5. PR triển khai phải liên kết ADR; sau khi deploy, cập nhật bằng chứng và các sai lệch thực tế.
6. ADR không bị sửa lại để che lịch sử. Quyết định mới thay thế quyết định cũ bằng ADR mới có liên kết `Supersedes`.

## 4. Architecture Evaluation Scorecard

Mỗi tiêu chí chấm từ 0–5. Điểm quy đổi bằng `điểm / 5 × trọng số`.

| Tiêu chí | Trọng số | Bằng chứng tối thiểu |
|---|---:|---|
| Clinical safety & fail-closed | 25% | Test dị ứng/ngưỡng; draft không đi thẳng tới bệnh nhân; số dinh dưỡng không do LLM sinh |
| Correctness & data provenance | 15% | Test calculator; mỗi giá trị truy được về food/dish/source; migration nhất quán |
| Security & privacy | 15% | RBAC/IDOR test; không log secret/PHI; secret chỉ nằm trong environment |
| Reliability & recoverability | 10% | Health check; timeout/retry có giới hạn; migration/rollback hoặc recovery procedure |
| Testability & evaluation evidence | 10% | Unit/integration/E2E; eval có dataset/model/config/git SHA; phân biệt fail, blocked và N/A |
| Maintainability & simplicity | 10% | Module ownership rõ; dependency có lý do; không thêm service nếu Postgres/code hiện tại đủ dùng |
| Observability & auditability | 5% | Trace ID; audit actor/action/time; lỗi có thể điều tra từ logs mà không lộ PHI |
| Performance & cost | 5% | p95 hoặc thời gian sinh thực đơn; số lần gọi model; chi phí/request ước tính hoặc đo được |
| Deployability & cost | 3% | Docker tái lập được; CI gate; rollback; cấu hình các môi trường rõ ràng |
| UX/API operability | 2% | API state rõ; loading/error/empty state; responsive; trạng thái không chỉ biểu đạt bằng màu |

### Quality gates

- **Pass:** tổng điểm ≥ 80/100.
- **Conditional pass:** 75–79, phải có risk owner và hạn xử lý.
- **Fail:** < 75, không phát hành.
- Bất kể tổng điểm, hệ thống **fail ngay** nếu Clinical safety, Correctness hoặc Security dưới 3/5.
- Hệ thống cũng **fail ngay** nếu có đường bypass HITL, hard clinical violation lọt qua, truy cập chéo dữ liệu bệnh nhân, số dinh dưỡng không có nguồn hoặc migration production không có phương án khôi phục.

Điểm không được tự khai nếu thiếu bằng chứng. Không có test/log/report tương ứng thì tiêu chí tối đa 2/5.

## 5. Nhịp đánh giá

- Trước khi merge một ADR có tác động lớn: đánh giá phần bị ảnh hưởng.
- Cuối mỗi sprint: Architecture Owner cập nhật rủi ro và technical debt.
- Trước release/demo: chấm toàn bộ scorecard và lưu vào `eval/architecture/`.
- Sau incident hoặc migration lỗi: tạo ADR/record mới và đánh giá lại tiêu chí liên quan.

## 6. Kiến trúc hiện tại và lý do lựa chọn

| Lựa chọn | Lý do | Phương án không chọn / trade-off |
|---|---|---|
| Next.js frontend | Một codebase cho hai portal, deploy Vercel đơn giản, phù hợp MVP | Native app cho UX mobile tốt hơn nhưng tăng hai codebase |
| FastAPI backend | Hợp hệ sinh thái Python của calculator, validation và agent; OpenAPI rõ | Node backend giảm lệch ngôn ngữ FE nhưng làm tách clinical core |
| PostgreSQL/Supabase | Transaction, relational integrity, audit và dữ liệu có cấu trúc; một database giảm vận hành | Nhiều datastore chuyên biệt có thể scale riêng nhưng quá phức tạp cho MVP |
| SQL cho số liệu dinh dưỡng | Exact lookup và truy vết nguồn; không làm sai số qua semantic retrieval | Vector search chỉ phù hợp guideline phi cấu trúc |
| Một LangGraph workflow | State/retry/HITL rõ, dễ audit hơn nhiều agent tự hội thoại | Multi-agent linh hoạt hơn nhưng khó kiểm soát và đánh giá |
| LLM chọn món, Python tính số | Giữ sáng tạo ở phần phù hợp và tính quyết định ở clinical core | Cho LLM sinh toàn bộ nhanh hơn nhưng không đủ an toàn |
| HITL bắt buộc | Chuyên gia là cổng cuối trước khi bệnh nhân nhìn thấy kế hoạch | Auto-publish nhanh hơn nhưng không phù hợp rủi ro lâm sàng MVP |
| Render + Vercel + Supabase | Triển khai nhanh, chi phí thấp, phù hợp tải demo | Cold start và phụ thuộc ba nhà cung cấp; chấp nhận trong MVP và phải có UX retry |

Các lý do trên là giả thuyết kiến trúc hiện hành. Chúng chỉ được giữ lại nếu scorecard và bằng chứng runtime tiếp tục ủng hộ.

## 7. Definition of Done cho quyết định kiến trúc

Một thay đổi kiến trúc chỉ hoàn thành khi:

- ADR được chấp nhận và liên kết từ PR.
- Diagram/API/schema liên quan được cập nhật.
- Có test hoặc phép đo cho claim quan trọng.
- Có owner cho mọi residual risk.
- Architecture evaluation không vi phạm quality gate.
- Deployment và rollback/recovery path được ghi lại nếu thay đổi production.
