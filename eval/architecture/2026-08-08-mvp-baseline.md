# Architecture Evaluation — MVP baseline

- Date: 2026-08-08
- Evaluator: R1 — Architecture Owner
- Review basis: workspace hiện tại; chưa gắn production commit SHA
- Result: **FAIL — 61/100**

Đây là baseline để chỉ ra khoảng trống cần đóng, không phải đánh giá năng lực thành viên. Điểm chỉ được cấp khi có bằng chứng trong repo; claim trong tài liệu nhưng chưa khớp code không được tính là đã hoàn thành.

| Tiêu chí | Trọng số | Điểm 0–5 | Điểm quy đổi | Bằng chứng / lý do |
|---|---:|---:|---:|---|
| Clinical safety & fail-closed | 25 | 4 | 20.0 | Có deterministic core, validator, guardrail, trạng thái `pending_review` và patient query chỉ lấy `approved`; cần chứng minh E2E không có đường bypass |
| Correctness & data provenance | 15 | 3 | 9.0 | Có test clinical/dish và nguyên tắc nguồn; pgvector/schema production còn TODO, migration history từng drift |
| Security & privacy | 15 | 3 | 9.0 | Có auth/RBAC tests; chưa có evidence hoàn chỉnh về token lifecycle, log redaction và production secret audit |
| Reliability & recoverability | 10 | 2 | 4.0 | Có health/deploy; chưa có durable Postgres checkpoint, backup/restore evidence và rollback migration được kiểm chứng |
| Testability & evaluation evidence | 10 | 3 | 6.0 | Có unit/API/graph/E2E và dataset 60 case; hai report eval đang khác scope/kết quả và chưa có canonical git SHA/config |
| Maintainability & simplicity | 10 | 3 | 6.0 | Single graph và một relational DB là hợp lý; diagram/cây module/RAG mô tả chưa khớp code hiện tại |
| Observability & auditability | 5 | 2 | 2.0 | Có audit intent/model; chưa có evidence trace xuyên FE → API → graph và bất biến append-only ở DB |
| Performance & cost | 5 | 2 | 2.0 | Chưa có p95, cost/request, cold-start budget hoặc load evidence |
| Deployability & cost | 3 | 3 | 1.8 | Docker + Render + Vercel + Supabase đã deploy; config docs còn lẫn Neon/Supabase và chưa có rollback gate |
| UX/API operability | 2 | 3 | 1.2 | Hai portal và trạng thái review rõ; loading/cold-start/mobile/accessibility chưa được đánh giá có hệ thống |
| **Tổng** | **100** |  | **61.0** | **FAIL** |

## Vì sao kiến trúc hiện tại vẫn là lựa chọn đúng cho MVP

Điểm thấp chủ yếu do thiếu bằng chứng production và docs-code drift, không phải do cần thay toàn bộ stack:

- **Next.js + FastAPI** giữ UI độc lập với clinical core Python và đã deploy được.
- **PostgreSQL/Supabase** phù hợp dữ liệu quan hệ, transaction, audit và giảm số hệ cần vận hành.
- **Single LangGraph workflow** dễ kiểm soát state/retry/HITL hơn multi-agent.
- **CP-SAT/deterministic core trước, LLM fallback sau** giảm chi phí và hallucination; mọi số dinh dưỡng vẫn phải do Python/SQL tính.
- **Dish là đơn vị người dùng, ingredient là đơn vị tính** đúng với UX món ăn và vẫn giữ provenance.
- **HITL bắt buộc** là ranh giới an toàn phù hợp MVP lâm sàng.

Do đó khuyến nghị là làm kiến trúc hiện tại khớp với lời hứa, không migration sang stack mới.

## Automatic-fail audit

| Gate | Trạng thái baseline |
|---|---|
| Không bypass HITL | Chưa đủ evidence E2E production — phải xác minh |
| Không hard clinical violation lọt qua | Có test cục bộ; cần canonical safety run |
| Không cross-patient access | Có API auth tests; cần ghi rõ case IDOR trong report |
| Không số dinh dưỡng thiếu nguồn | Chưa có completeness report toàn bộ dishes/ingredients |
| Migration khôi phục được | Chưa có restore/rollback drill |

## Việc Architecture Owner phải giao trước release

| Ưu tiên | Việc | Responsible | Accountable | Điều kiện hoàn thành |
|---|---|---|---|---|
| P0 | Chốt canonical eval report có git SHA, dataset và config | R2 | R1 | Một report duy nhất, tái chạy được |
| P0 | Xác minh E2E patient không xem được draft/pending/rejected | R3 | R1 | Integration test pass |
| P0 | Kiểm tra provenance completeness toàn bộ món/nguyên liệu | R2 | R1 | 100% record phát hành có source |
| P0 | Chốt migration/backup/restore với Supabase | R3 | R1 | Có runbook và một lần drill thành công |
| P1 | Quyết định PostgresSaver hay bỏ claim durable graph checkpoint | R1 | R1 | ADR + code/doc khớp nhau |
| P1 | Sửa CODEOWNERS từ `/web/` sang `/web-next/` | R3 | R1 | PR frontend tự request đúng reviewer |
| P1 | Chốt RAG thuộc MVP hay N/A và cập nhật metric | R2 | R1 | ADR + architecture/eval thống nhất |
| P1 | Đo p95, cold start và số lần gọi model/request | R3 | R1 | Report có sample size và môi trường |

## ADR backlog bắt buộc

1. CP-SAT-first và LLM fallback.
2. Dish là đơn vị UX, ingredient là đơn vị tính/provenance.
3. Supabase Postgres, pooler/SSL và Alembic ownership.
4. Durable checkpoint và cách resume HITL.
5. Canonical eval/release gates.
6. RAG in/out MVP.
7. Auth/session lifecycle.
8. Audit immutability và retention.
9. Data classification, PHI redaction và prohibited fields.

Baseline phải được chấm lại sau khi hoàn thành các mục P0. Mục tiêu release là ít nhất 75/100 và không có automatic fail.
