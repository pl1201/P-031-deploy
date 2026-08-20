# Gói bàn giao R2 — 2026-08-20

Đóng gói trong lúc chờ push GitHub (PR #119 đang xử lý conflict). **Đây là chữa cháy tạm
— sau khi merge xong, đối chiếu lại bằng `git diff`/`git log`, đừng để hai bên tự chỉnh
tay rồi lệch nhau với repo chính.**

## Việc mới nhất — đọc trước

- **`R2_KE_HOACH_TICH_HOP_WEARABLE.md`** — kế hoạch tích hợp Google Fit/Apple Health,
  kèm market research + đánh giá rủi ro. Kết luận: nên làm, nhưng chỉ hiển thị tham khảo,
  không tự động hoá bất kỳ chỉ định nào — nhất là calo tiêu hao (sai 20-90% theo nghiên
  cứu Stanford).
- **`prototype_uiux_wearable.html`** — mở bằng trình duyệt bất kỳ. Mockup 4 màn hình
  minh hoạ nội dung/nhãn dữ liệu (R2 phác thảo), không phải thiết kế thị giác cuối (R4
  quyết định layout/màu thật).

## `cho_R1_R4_conflict/` — gửi cho người đang xử lý PR #119

9 file `data/seeds/*.csv` đã sửa trong 7 commit chưa push (ký release 199/211 món, vá
sugar_g, sửa quy đổi khẩu phần...) + 5 file `src/clinical/*.py` sửa/mới (energy.py,
rules.py, nutrition.py, khau_phan.py, doc_khau_phan.py) + 3 file HANDOFF đã viết sẵn giải
thích chi tiết từng thay đổi.

## `cho_R3_supabase/` — gửi cho người đồng bộ Supabase

Script `dong_bo_seed_len_supabase.py` (mặc định dry-run, chỉ upsert không xoá dòng lạ) +
4 CSV nó cần đọc + biên bản ký release để biết đang đồng bộ đúng phạm vi nào.

## Không có trong gói này

Test (`tests/test_r2_*.py`) và tài liệu nội bộ R2 khác (`R2_BENCHMARK_*`,
`R2_KE_HOACH_KCAL_OUT_*`, `R2_AUDIT_*`, `R2_12_MON_*`, `R2_RESEARCH_*`, `R2_TEST_PLAN_*`)
— không ai khác cần chạy trước khi push xong; nằm sẵn trong repo, lấy qua git khi merge
xong.
