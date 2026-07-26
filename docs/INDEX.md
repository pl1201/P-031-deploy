# INDEX — Bộ tài liệu dự án VMEC-10

> Sinh ngày 26/07/2026. Đọc theo thứ tự này nếu bạn mới vào dự án.

## Thứ tự đọc

| # | File | Ai bắt buộc đọc | Thời gian |
|---|---|---|---|
| 1 | `docs/00_ASSESSMENT.md` | Cả đội | 15 phút |
| 2 | `docs/PLAN.md` | Cả đội | 15 phút |
| 3 | `docs/TEAM.md` | Cả đội | 10 phút |
| 4 | `docs/ARCHITECTURE.md` | R1, R2, R3, R4 | 20 phút |
| 5 | `docs/TICKETS.md` | Cả đội (đọc phần của mình kỹ) | 20 phút |
| 6 | `CLAUDE.md` | Cả đội | 10 phút |
| 7 | `docs/rules/*` | Theo vai trò | 10 phút/file |
| 8 | `DEVLOG.md` | Cả đội — và ghi mỗi ngày | 2 phút/ngày |

## Cấu trúc

```
├── CLAUDE.md                       # Rule gốc cho AI coding agent + cả đội
├── DEVLOG.md                       # ⭐ File log duy nhất (Deliverable #8 + #9)
├── docs/
│   ├── INDEX.md                    # file này
│   ├── 00_ASSESSMENT.md            # Đánh giá đề án + research, quyết định cắt scope
│   ├── PLAN.md                     # Kế hoạch 6 tuần, milestone, eval, sổ rủi ro
│   ├── ARCHITECTURE.md             # ⭐ Kiến trúc + Mermaid + DB + API (Deliverable #3)
│   ├── TEAM.md                     # Phân vai, RACI, phân quyền, ai nói phần nào ở Demo Day
│   ├── TICKETS.md                  # ⭐ 52 ticket, giao việc từng người
│   └── rules/
│       ├── 00-core.md              # Ưu tiên, fail closed, truy vết
│       ├── 10-clinical-safety.md   # ⭐ Quan trọng nhất — guardrail, ngưỡng, dị ứng
│       ├── 20-backend-agent.md     # LangGraph + FastAPI
│       ├── 30-frontend.md          # Next.js, hiển thị nguồn, cảnh báo
│       ├── 40-data-rag.md          # SQL vs RAG, nguồn dữ liệu, OOV
│       └── 50-workflow.md          # Git, PR, standup, code freeze
└── .claude/skills/
    ├── README.md                   # Danh mục skill + skill nên viết thêm
    ├── clinical-targets/SKILL.md
    ├── vn-food-data/SKILL.md
    ├── menu-safety-check/SKILL.md
    ├── langgraph-node/SKILL.md
    └── ticket-workflow/SKILL.md
```

## Việc cần làm ngay (48 giờ đầu)

| Thứ tự | Việc | Ai | Ticket |
|---|---|---|---|
| 1 | Điền tên thật vào `TEAM.md` §1 và `DEVLOG.md` §1 | Cả đội | — |
| 2 | Clone template, init repo, push, copy bộ tài liệu này vào | R3 | SET-01, SET-06 |
| 3 | Chạy `bash scripts/setup_hooks.sh` trên mọi máy | Cả đội | SET-02 |
| 4 | Chốt nguồn Bảng thành phần thực phẩm VN + đăng ký key USDA | R2 | DAT-01 |
| 5 | Deploy hello-world lấy Live URL | R3 | SET-05 |
| 6 | Verify số liệu trong nghiên cứu → `REFERENCES.md` | R2 | DAT-00 |
| 7 | Chia 150 dòng thực phẩm cho 5 người nhập | Cả đội | DAT-02 |

## Ba câu cần thuộc lòng

1. **LLM chọn món — Python tính số.**
2. **Không con số nào không có nguồn.**
3. **Không có đường tắt tới bệnh nhân.**

Ba câu này vừa là kiến trúc, vừa là câu trả lời cho câu hỏi khó nhất mà giám khảo sẽ hỏi.
