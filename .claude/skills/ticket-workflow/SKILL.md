---
name: ticket-workflow
description: Thực hiện một ticket từ đầu đến cuối theo quy trình của đội, gồm tạo branch, viết code kèm test, mở PR đúng chuẩn, và ghi DEVLOG. Dùng khi bắt đầu làm một ticket có mã như SET-01, DAT-02, CLN-04, AGT-06, HIT-03, khi chuẩn bị mở pull request, hoặc khi cần ghi nhật ký phát triển cuối buổi làm việc.
---

# Làm một ticket từ đầu đến cuối

## Bước 1 — Đọc ticket

Mở `docs/TICKETS.md`, tìm đúng mã. Chú ý: **Owner**, **Deps** (phụ thuộc đã xong chưa?), **AC** (acceptance criteria — đây là định nghĩa "xong", không phải cảm giác chủ quan).

Nếu ticket không thuộc mình → báo owner trước khi làm.
Nếu Deps chưa xong → không bắt đầu, chọn ticket khác.

## Bước 2 — Đọc rule liên quan

| Ticket bắt đầu bằng | Đọc |
|---|---|
| `CLN-`, `DAT-` | `docs/rules/10-clinical-safety.md`, `40-data-rag.md` |
| `AGT-`, `BE-`, `HIT-` | `docs/rules/20-backend-agent.md` |
| `FE-` | `docs/rules/30-frontend.md` |
| `SET-`, `OPS-`, `EVL-`, `DEL-` | `docs/rules/50-workflow.md` |

Luôn đọc `CLAUDE.md` §2 (ba rule đỏ) nếu ticket đụng tới con số dinh dưỡng.

## Bước 3 — Branch

```bash
git checkout develop && git pull origin develop
git checkout -b feature/CLN-04-bounds-checker
```

## Bước 4 — Code + test cùng lúc

Không viết code trước rồi hứa test sau. Với ticket có logic:
- 1 test happy path
- ≥1 test edge case
- Module `src/clinical/` cần coverage ≥ 80%

## Bước 5 — Commit

```bash
git commit -m "feat(clinical): thêm bounds checker cho Na và K (CLN-04)"
```

Format: `type(scope): mô tả (MÃ-TICKET)`
type: `feat|fix|docs|test|refactor|chore` · scope: `agent|api|clinical|web|data|ops`

Commit ít nhất 1 lần mỗi ngày làm việc.

## Bước 6 — Kiểm tra trước khi mở PR

```bash
make check   # ruff + format + mypy + pytest
```

Đỏ thì sửa, đừng mở PR. Tự kiểm nhanh:
- Không `print()`, không `except:` trần
- Không secret trong code
- Đã cập nhật `.env.example` nếu thêm biến
- Đã cập nhật tài liệu nếu đổi API/kiến trúc

## Bước 7 — Mở PR

Tiêu đề = commit message. Mô tả gồm 4 phần:

```markdown
### Thay đổi
- …

### Vì sao
- Ticket CLN-04 …

### Cách test
1. `make test`
2. `pytest tests/unit/test_bounds.py -v`

### Checklist
- [x] make check xanh
- [x] Có test
- [x] Không secret / print / except trần
- [x] Đã cập nhật tài liệu
- [x] Đã ghi DEVLOG
```

CODEOWNERS sẽ tự gán reviewer. PR > 400 dòng thì tách nhỏ.

## Bước 8 — Ghi DEVLOG (đừng bỏ bước này)

Thêm vào `DEVLOG.md` §2:

```markdown
### [2026-08-05] · Nguyễn Văn A · R2 Clinical & Data
- **Làm:** CLN-04 bounds checker
- **Kết quả:** 8 test pass, PR #23 chờ review
- **Vướng:** ngưỡng phospho CKD G4 chưa rõ đơn vị → đang tra KDIGO
- **Tiếp theo:** CLN-05 kiểm tra dị ứng
- **Thời gian:** 3h
```

Nếu ticket dẫn tới một quyết định kỹ thuật đáng kể → thêm dòng vào §3 Decision Log theo mẫu *bối cảnh → phương án → quyết định → hệ quả*.
Nếu có sự cố → ghi §4, kể cả sự cố do chính mình gây ra.

## Bước 9 — Sau khi merge

- Đóng issue trên GitHub
- Xoá branch
- Cập nhật bảng deliverables trong DEVLOG §6 nếu liên quan
- Nhận ticket tiếp theo (chỉ 1 ticket In Progress mỗi lúc)

---

## Khi bị chặn

| Thời gian | Việc cần làm |
|---|---|
| 90 phút | Đăng nhóm chat: đang làm gì, đã thử gì, lỗi gì |
| 4 giờ | Tag owner module liên quan |
| 1 ngày | Đưa lên standup |
| 2 ngày | R1/R3 quyết: đổi phương án, dùng fallback, hoặc cắt scope |

Không ai bị đánh giá vì hỏi sớm. Bị đánh giá vì im lặng hai ngày.
