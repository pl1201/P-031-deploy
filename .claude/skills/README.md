# SKILLS — Bộ kỹ năng cho AI coding agent

> Đặt thư mục này ở `.claude/skills/` trong repo. Claude Code tự nạp.
> Với Cursor: copy nội dung sang `.cursor/rules/`. Với Gemini CLI / Codex: tham chiếu từ file cấu hình tương ứng.

## Skill đã viết sẵn (5)

| Skill | Kích hoạt khi | Ai dùng nhiều nhất |
|---|---|---|
| **`clinical-targets`** | Làm việc với `src/clinical/`, thêm/sửa ngưỡng, xử lý đa bệnh lý | R2, R1 |
| **`vn-food-data`** | Nhập dữ liệu thực phẩm/món ăn, xử lý OOV, phân rã món phức hợp | R2 |
| **`menu-safety-check`** | Review PR chạm agent/guardrail, debug thực đơn bị chặn, viết test red-team, trước khi demo | Cả đội |
| **`langgraph-node`** | Thêm node/tool/edge, structured output, checkpointer, HITL interrupt | R1 |
| **`ticket-workflow`** | Bắt đầu bất kỳ ticket nào, mở PR, ghi DEVLOG | Cả đội |

## Skill nên viết thêm khi dự án tiến triển

| Skill đề xuất | Viết ở tuần | Nội dung chính |
|---|---|---|
| `fastapi-endpoint` | W2 | Mẫu route + dependency phân quyền + envelope response + integration test |
| `nextjs-screen` | W4 | Mẫu màn hình: 3 trạng thái, chip nguồn, phân cấp cảnh báo, dark mode |
| `rag-ingest` | W3 | Chunking cho văn bản y tế tiếng Việt, metadata bắt buộc, hybrid search |
| `eval-runner` | W5 | Chạy bộ 60 case, tính 5 nhóm metric, xuất báo cáo |
| `demo-prep` | W6 | Checklist trước demo: warm up URL, seed lại data, kịch bản, video backup |
| `pitch-writer` | W6 | Cấu trúc 10 slide + quy tắc mỗi số liệu phải có nguồn |

## Cách viết skill mới cho đội

Một skill tốt trong dự án này có 4 phần:

1. **Frontmatter** — `name` + `description` mô tả *khi nào kích hoạt*, không phải *nó là gì*. Description càng nêu rõ tình huống cụ thể (tên thư mục, mã ticket, tên bảng DB) thì càng dễ trigger đúng.
2. **Nguyên tắc trước khi làm** — những ràng buộc không được vi phạm, đặt lên đầu.
3. **Quy trình từng bước** — kèm mẫu code thật của repo, không phải code generic.
4. **Checklist kết thúc** — để tự kiểm trước khi mở PR.

Giữ mỗi skill dưới ~150 dòng. Skill dài không được đọc kỹ, giống như PR 1000 dòng không được review kỹ.
