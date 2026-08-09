# Architecture Evaluation

Thư mục này lưu bằng chứng đánh giá kiến trúc theo từng release. Người chịu trách nhiệm là **R1 — Architecture Owner**; R2 và R3 đồng duyệt các cổng clinical safety, correctness và security.

## Cách thực hiện

1. Copy `scorecard-template.md` thành `YYYY-MM-DD-<release>.md`.
2. Chấm 0–5 cho từng tiêu chí và gắn đường dẫn tới test/report/log/ADR.
3. Tính điểm có trọng số theo `docs/ARCHITECTURE_GOVERNANCE.md`.
4. Ghi residual risks, owner và hạn xử lý.
5. Không phát hành nếu vi phạm quality gate.

Evaluation này đo chất lượng **kiến trúc hệ thống**. Nó không thay thế bộ eval chất lượng thực đơn/AI trong `eval/results/`.
