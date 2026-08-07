# RULE 50 — QUY TRÌNH LÀM VIỆC

> Owner: **R3** (quy trình kỹ thuật) + **R1** (nhịp làm việc)

---

## R50.1 — Vòng đời một ticket

```
Backlog → In Progress → In Review → Done
```

- Chỉ nhận **1 ticket In Progress** mỗi người tại một thời điểm. Ba việc dở dang bằng không việc nào xong.
- Nhận ticket → tự gán mình trên GitHub Issue → tạo branch `feature/<MÃ>-mô-tả`.
- Ticket chỉ Done khi đủ DoD (`PLAN.md` §5).

## R50.2 — Branch & commit

```bash
git checkout develop && git pull
git checkout -b feature/CLN-04-bounds-checker
git commit -m "feat(clinical): thêm bounds checker cho Na và K (CLN-04)"
```

- `type(scope): mô tả (MÃ-TICKET)`
- type: `feat|fix|docs|test|refactor|chore`
- scope: `agent|api|clinical|web|data|ops`
- Commit ít nhất 1 lần/ngày làm việc. Commit to đùng cuối tuần khiến worklog trông tệ và review bất khả thi.

## R50.3 — Pull Request

Mô tả PR gồm 4 phần: **Thay đổi gì · Vì sao · Cách test · Checklist**.

Checklist bắt buộc:
- [ ] `make check` xanh
- [ ] Có test cho logic mới
- [ ] Không secret, không `print()`, không `except:` trần
- [ ] Đã cập nhật `.env.example` nếu thêm biến
- [ ] Đã cập nhật tài liệu nếu đổi kiến trúc/API
- [ ] Đã ghi DEVLOG

PR > 400 dòng thay đổi → tách nhỏ, trừ khi là seed dữ liệu.

## R50.4 — Review

- Review trong **12 giờ**. Quá hạn thì tag trực tiếp trong nhóm chat.
- Review là đọc thật, không bấm Approve cho xong. Ít nhất kiểm: có test không, có vi phạm 3 rule đỏ không, có secret không.
- Bình luận theo kiểu đề xuất, không phán xét. `nit:` cho góp ý nhỏ không chặn merge.
- Tác giả **không tự merge PR của mình** vào `main`.

## R50.5 — CI là luật

CI đỏ = không merge. Không có ngoại lệ "để sau sửa". Nếu CI hỏng do hạ tầng, R3 sửa hạ tầng, không tắt check.

## R50.6 — Nghi thức hằng tuần

| Khi nào | Việc | Ai |
|---|---|---|
| Hằng ngày 21:00 | Standup async (3 dòng/người) | Cả đội |
| Thứ 2 20:00 | Sprint planning 45 phút, chốt ticket tuần | Cả đội |
| Thứ 7 20:00 | Demo nội bộ 30 phút — mỗi người demo phần mình | Cả đội |
| Thứ 7 sau demo | Retro 15 phút — 1 giữ, 1 bỏ | Cả đội |
| Cuối mỗi buổi làm | Ghi DEVLOG | Mỗi người |

Standup async 3 dòng: *hôm qua làm gì · hôm nay làm gì · đang vướng gì*.

## R50.7 — Leo thang khi bị chặn

| Thời gian bị chặn | Hành động |
|---|---|
| 90 phút | Đăng vào nhóm chat kèm lỗi cụ thể |
| 4 giờ | Tag owner của module liên quan |
| 1 ngày | Đưa lên standup, cân nhắc đổi cách tiếp cận |
| 2 ngày | R1/R3 quyết định: đổi phương án, dùng fallback, hoặc cắt scope |

## R50.8 — Quy tắc AI Logging

- Chạy `bash scripts/setup_hooks.sh` một lần trên mỗi máy.
- Dùng ChatGPT/Claude.ai/web tool → log thủ công: `bash scripts/_pyrun.sh scripts/log_manual.py --tool chatgpt --prompt "..."`.
- **Không sửa, không xoá file trong `.ai-log/`. Không dùng `git push --no-verify`.**
- Hook lỗi → báo instructor, không tự bypass.

## R50.9 — Quản lý chi phí API

- Dev dùng model rẻ (`gpt-4o-mini` / Haiku). Chỉ dùng model mạnh khi chạy eval cuối.
- Cache kết quả LLM cho dữ liệu tĩnh (phân rã công thức món ăn).
- R3 kiểm tra chi tiêu hằng tuần và báo vào nhóm.
- Không chạy vòng lặp gọi LLM mà không có giới hạn — mọi loop phải có `max_iterations`.

## R50.10 — Định nghĩa "báo động đỏ"

Kích hoạt khi: bỏ lỡ milestone tuần, một người mất tích > 3 ngày, hoặc Live URL chết > 24 giờ.
Xử lý: họp 30 phút trong 24 giờ → xác định nguyên nhân → cắt scope theo `PLAN.md` §9 → ghi vào DEVLOG. **Không im lặng hy vọng mọi chuyện tự tốt lên.**

## R50.11 — Code freeze

Từ 04/09 23:59: chỉ sửa bug P0 (chặn demo). Mọi thay đổi sau freeze cần R1 + R3 cùng đồng ý. Ưu tiên còn lại dồn cho slide, video, tổng duyệt.

## R50.12 — Trước mỗi buổi demo

Warm up Live URL (Render free tier ngủ sau 15 phút không dùng), kiểm tra tài khoản demo còn đăng nhập được, chuẩn bị **video backup** phòng khi mạng hỏng. Demo live thất bại mà không có backup là lỗi có thể tránh được.
