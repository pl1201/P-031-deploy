# TICKETS — BACKLOG & GIAO VIỆC

> 54 ticket · 6 sprint · Ước tính tổng ≈ 438 giờ-người
> Ký hiệu: **P0** = chặn dự án · **P1** = cần cho MVP · **P2** = nâng cao · **P3** = có thì tốt
> Owner theo mã vai trò trong `TEAM.md` (R1–R4 · đội 4 người)

> ⚠️ **Đổi phạm vi (2026-08-05, `docs/PRD.md` v2.1):** MVP thu hẹp trọng tâm nghiệm thu/demo về **ĐTĐ2**. Các ticket/AC nhắc tới THA, CKD, Gout (chủ yếu `CLN-02`, `CLN-03`, `CLN-06`, `DAT-05`, `AGT-03`) **không bị xoá khỏi backlog, code đã build cho các bệnh này vẫn giữ nguyên và tiếp tục hoạt động đúng như thiết kế** (cơ chế phát hiện xung đột đa bệnh lý đã đối chiếu lại với tài liệu kế hoạch gốc, xác nhận đúng đặc tả — xem `CLAUDE.md` §7, DEVLOG DEC-014) — chỉ không còn là **trọng tâm phát triển tính năng mới**. Ưu tiên sprint còn lại: đường găng ĐTĐ2 trước cho việc mới, không cần mở rộng thêm phạm vi đa bệnh lý trừ khi có ticket riêng.

**Cách dùng:** copy sang GitHub Issues hoặc Notion. Tiêu đề issue = `[MÃ] Tên ticket`. Gắn label = epic + priority. Milestone = sprint.

---

## Tổng quan theo sprint

| Sprint | Tuần | Ticket | Giờ ước tính |
|---|---|---|---|
| S1 | 27/07–02/08 | SET-01→06, DAT-00→03 | 78h |
| S2 | 03/08–09/08 | DAT-04→06, DAT-11, CLN-01→05, BE-01→05 | 96h |
| S3 | 10/08–16/08 | AGT-01→08, CLN-06→07, BE-06→07 | 96h |
| S4 | 17/08–23/08 | HIT-01→05, FE-01→06, BE-08→09 | 88h |
| S5 | 24/08–30/08 | ADV-01→06, FE-07→08, EVL-01→03 | 62h |
| S6 | 31/08–06/09 | EVL-04→06, DEL-01→06 | 44h |

---

## EPIC 0 — SETUP (S1) — *Owner chính: R3*

### `SET-01` Khởi tạo repo từ template AI20K
**Owner:** R3 · **P0** · 2h · **Deps:** —
Clone `starter-code-template`, `rm -rf .git`, `git init`, push lên repo đội. Đổi `pyproject.toml` (name, description, repo URL). Tạo `develop`. Bật branch protection cho `main` + `develop` (require PR, ≥1 approval, status checks).
**AC:** Cả 5 người clone và chạy `make run` thành công · `main` không push thẳng được · `.env.example` đầy đủ biến của dự án.

### `SET-02` Cài AI Usage Logging Hooks
**Owner:** R3 · **P0** · 1h · **Deps:** SET-01
Chạy `bash scripts/setup_hooks.sh` trên máy **từng người**. Điền `AI_LOG_API_KEY` do instructor cấp vào `.env`.
**AC:** Mỗi thành viên có ít nhất 1 entry trong `.ai-log/session.jsonl` · `git push` chạy pre-push hook không lỗi · Người dùng ChatGPT/web tool biết cách chạy `log_manual.py`.
> Đây là Deliverable #4, làm 1 lần được điểm cả kỳ. Không ai được `git push --no-verify`.

### `SET-03` CODEOWNERS + PR template + Issue template
**Owner:** R3 · **P1** · 2h · **Deps:** SET-01
Tạo `.github/CODEOWNERS` (theo `TEAM.md` §4), `.github/pull_request_template.md`, 2 issue template (feature/bug).
**AC:** PR chạm `src/clinical/` tự động request review R2 · PR template có checklist DoD.

### `SET-04` CI pipeline
**Owner:** R3 · **P0** · 4h · **Deps:** SET-01
GitHub Actions: `ruff check`, `ruff format --check`, `mypy`, `pytest`, `docker build`. Chạy trên PR vào `develop`/`main`.
**AC:** CI xanh trên PR mẫu · CI đỏ khi cố tình để lỗi lint · Thời gian chạy < 5 phút.

### `SET-05` Deploy hello-world lên cloud
**Owner:** R3 · **P0** · 4h · **Deps:** SET-04
Render (backend, Docker) + Vercel (frontend) + Neon/Supabase Postgres có `pgvector`. Cấu hình secrets trên platform.
**AC:** **Live URL công khai** trả `GET /api/v1/health` → 200 · Frontend hiển thị trang chủ gọi được API · URL ghi vào README.
> ⚠️ Ticket quan trọng nhất tuần 1. Deploy sớm để tuần 6 không phải deploy lần đầu.

### `SET-06` Khởi tạo tài liệu dự án
**Owner:** R1 · **P1** · 3h · **Deps:** SET-01
README từ `README_boilerplate.md`; copy bộ `docs/` này vào repo; tạo `DEVLOG.md`; tạo `CLAUDE.md` và `docs/rules/`.
**AC:** README có: vấn đề, giải pháp, tech stack, cách chạy, thành viên, Live URL · DEVLOG có entry đầu tiên của cả 5 người.

---

## EPIC 1 — DATA & KNOWLEDGE (S1–S2) — *Owner chính: R2*

### `DAT-00` Verify toàn bộ số liệu trong nghiên cứu
**Owner:** R2 · **P0** · 6h · **Deps:** —
Kiểm chứng từng số liệu trong `nghien_cuu_dinh_duong_ai_agent.md`: các arXiv ID, con số MAE calo, F1 phân rã món ăn, hiệu lực TT 08/2024/TT-BYT, QĐ 2598 / 3777 / 9484, NĐ 13/2023, thống kê muối VN, con số "70% không tuân thủ".
**AC:** File `docs/REFERENCES.md`, mỗi số liệu 1 dòng: `số liệu | nguồn | URL | ngày truy cập | trạng thái (verified / not-found / superseded)` · Số nào `not-found` thì **xoá khỏi đề án và pitch deck**.
> Bị giám khảo hỏi nguồn mà ú ớ sẽ mất điểm nặng hơn là không nhắc tới số liệu đó.

### `DAT-01` Chốt nguồn dữ liệu thực phẩm & pháp lý sử dụng
**Owner:** R2 · **P0** · 4h · **Deps:** —
Xác định lấy Bảng TPTP Việt Nam ở đâu (bản in/PDF/website NIN), điều kiện sử dụng. Đăng ký API key USDA FoodData Central. Kiểm tra license DDID — nếu không rõ ràng thì chuyển sang phương án curate 80 cặp thủ công.
**Đã nghiên cứu bổ sung** (xem `data/README.md` mục "Nghiên cứu bổ sung nguồn dữ liệu"): **Open Food Facts** xác nhận dùng được ngay (free API, ODbL) cho nhóm thực phẩm đóng gói; **Dược thư Quốc gia VN 2022** xác nhận dùng được cho `source_ref` của DAT-05. uFiSh1.0 (FAO cá/thủy sản) cần R2 tự thử tải link trực tiếp để xác nhận nốt. PhyFoodComp/eBASIS/ASEANFOODS/WikiFCD-FoodOn đã bị loại có ghi lý do (ngoài scope lâm sàng / license không rõ / trùng lặp VFCT / over-engineering).
**AC:** `data/README.md` ghi rõ: nguồn nào dùng được, giấy phép, cách trích dẫn · Có API key USDA hoạt động · Quyết định về DDID được ghi vào DEVLOG dạng ADR.

### `DAT-02` Thiết kế schema & nhập thực phẩm — KHÔNG GIỚI HẠN TRÊN
**Owner:** R2 (cả đội hỗ trợ nhập) · **P0** · 12h+ (mở, xem ghi chú) · **Deps:** DAT-01
CSV `data/seeds/food_items.csv` với cột: `id, name_vi, name_en, aliases, unit_ref, kcal_100g, protein_g, carb_g, fat_g, fiber_g, na_mg, k_mg, p_mg, purine_mg, gi_index, source, source_ref, is_estimated`.
Ưu tiên: gạo/bún/phở/bánh mì, thịt heo/bò/gà, cá phổ biến, tôm, trứng, đậu phụ, rau, quả, dầu mỡ, gia vị (nước mắm, bột canh, hạt nêm, mì chính, đường).
**AC:** **≥150 dòng là SÀN, không phải trần** — nhập càng nhiều thực phẩm/món có nguồn thật càng tốt, không dừng lại vì đã đạt 150 · **0 dòng thiếu `source`** · Gia vị mặn có `na_mg` chính xác (trục chính của bài toán muối) · Script `make seed` nạp được vào DB.
> ⚠️ **2026-08-05: bỏ trần số lượng.** Trước đây giới hạn "≥150 dòng" bị hiểu nhầm thành mục tiêu dừng lại — thực tế hiện đã có sẵn nguồn xác minh được (NIN 2017/2007, USDA FDC bulk, Open Food Facts — xem `data/README.md`) đủ để vượt xa 150 nếu có thời gian nhập. Không đặt trần trên; chỉ giới hạn bởi **có nguồn thật hay không** (RULE-2/DEC-008), không phải bởi số lượng mục tiêu ban đầu.
> Chia người × 30 dòng/buổi tối là nhịp làm việc gợi ý, không phải mức trần.
> ✅ **2026-08-05 — đã vượt xa sàn:** `food_items.csv` từ 152 → **7.173 dòng** (7.146 có đủ số liệu) nhờ bulk import USDA SR Legacy/Foundation Foods (6.854 dòng) + trích toàn bộ bảng NIN 2017 (167 dòng mới). Xem `data/README.md` mục "DAT-12 — bỏ trần dữ liệu". **Lưu ý quan trọng:** khối USDA bulk (id ≥ 100000) chỉ là kho tham chiếu, KHÔNG dùng làm ứng viên sinh thực đơn (`retrieve_context` đã lọc — xem `src/agents/nodes/core.py`) vì làm CP-SAT chậm 30-50 lần. 152 dòng curated Việt Nam gốc + 167 dòng NIN mới là ứng viên thật cho agent.

### `DAT-03` Tích hợp USDA FoodData Central
**Owner:** R2 · **P1** · 6h · **Deps:** DAT-01
Client gọi API USDA, mapping field sang schema nội bộ, cache vào DB, đánh dấu `source='USDA'`.
**AC:** Tra được ≥ 20 thực phẩm nhập khẩu · Có retry + timeout · Có test dùng mock, không gọi API thật trong CI.

### `DAT-04` Bộ món ăn Việt + công thức nguyên liệu — KHÔNG GIỚI HẠN TRÊN
**Owner:** R2 · **P1** · 14h+ (mở) · **Deps:** DAT-02
`dishes` + `dish_ingredients`. Mỗi món: nguyên liệu + gram cho 1 khẩu phần chuẩn + vùng miền + tag (mặn/ngọt/dầu mỡ). Bao gồm món "nguy hiểm": phở bò, bún cá, canh cua, thịt kho tàu, cá kho tộ, bún riêu, mì tôm.
Quy trình: LLM sinh nháp công thức → **R2 rà soát và sửa tay** → đối chiếu tổng dinh dưỡng với nguồn tham khảo.
**AC:** **≥80 món là SÀN** — hiện `dishes.csv` mới có **3/80**, đây là ticket P1 tồn đọng lớn nhất của EPIC 1, ưu tiên làm tiếp trước khi mở rộng thêm. Không đặt trần trên; thêm món mới bất cứ khi nào có công thức đã đối chiếu được nguồn · Na của phở bò tính ra nằm trong khoảng 3,3–4,0g muối (khớp nghiên cứu) → dùng làm test hồi quy · Mỗi món ghi `verified_by`.
> ⚠️ **2026-08-05:** bỏ trần "80 món". Thực tế mới đạt 3/80 — trước khi tính chuyện "không giới hạn", việc cấp thiết là lấp cho đủ sàn 80.
> ✅ **2026-08-05 — đã vượt xa sàn (món quốc tế):** `dishes.csv` từ 3 → **2.635 món** nhờ USDA FNDDS (2.632 món quốc tế, phân rã nguyên liệu thật qua `sr_code`→SR Legacy, `verified_by="USDA FNDDS (nguồn chính thức)"` — khác `pending` của món Việt tự soạn). Xem `data/README.md` mục "DAT-12". **3 món Việt Nam gốc (phở bò, bún đậu mắm, canh rau muống) vẫn `pending`, vẫn là việc P1 cấp thiết nhất còn lại** — món quốc tế không thay thế được nhu cầu món Việt cho demo/eval của dự án này.
> ✅ **2026-08-06 — bắt đầu lấp món Việt (vẫn `pending`, chưa R2 duyệt):** +27 món Việt/bữa ăn Việt — (a) **15 bữa ăn thật** trích từ `data/Bảng xác định nhu cầu dinh dưỡng + thực đơn.xlsx` (file thực đơn nội bộ dự án, có gram thật theo "KL sống sạch"), khớp `food_id` tự động theo tên chuẩn hoá — tỷ lệ khớp thấp (~37%, 67/180 dòng nguyên liệu) vì tên nguyên liệu trong xlsx không khớp chính xác tên trong `food_items.csv` (VD "Dầu ăn" vs "Dầu ăn thực vật") — cố tình **không fuzzy-match rộng hơn** để tránh gán sai loại thực phẩm (rủi ro lâm sàng); (b) **12 món Việt tự soạn qua LLM** (phở gà, bún chả, canh chua cá, rau muống xào tỏi, đậu phụ sốt cà chua, cá kho tộ, gà kho gừng, canh cải nấu tôm, sườn xào chua ngọt, trứng chiên hành, canh su hào cà rốt thịt băm, nấm hương xào thịt bò) — gram ước lượng theo kinh nghiệm ẩm thực phổ thông, **chưa đối chiếu nguồn định lượng nào**, một số thiếu gia vị/nguyên liệu do chưa có `food_item` tương ứng (đường, dấm, nước dùng...). **Cả 27 món đều `pending` — R2 phải rà soát gram + bổ sung nguyên liệu thiếu trước khi dùng cho bệnh nhân.** Script: `scripts/extract_menu_xlsx_dishes.py`, `data/seeds/dishes.vn_llm_draft.csv`. 3 món gốc (phở bò, bún đậu mắm, canh rau muống) vẫn là ví dụ chuẩn duy nhất đã có Na đối chiếu nghiên cứu — chưa món nào trong 27 món mới đạt mức đó.
> 🔎 **2026-08-06 — research thực đơn/mâm cơm 3 miền (chưa thêm món, chỉ research):** Không tìm được nghiên cứu ẩm thực học/dinh dưỡng học thuật định lượng cấu trúc mâm cơm 3 miền (chỉ có nguồn báo/blog ẩm thực phổ thông — không dùng làm căn cứ số liệu). Đề xuất 20 món theo vùng (nguyên liệu chính + lưu ý bệnh lý sơ bộ, xem báo cáo đầy đủ trong lịch sử phiên làm việc 2026-08-06) — đa số là kiến thức ẩm thực phổ thông, CHƯA có nguồn định lượng, cần xử lý như (b) ở trên (LLM draft) khi thêm vào `dishes.csv`. **⚠️ Cảnh báo an toàn cần lưu ý khi duyệt món:** "canh chua cá lóc kiểu Huế" dùng **khế** (carambola) — y văn quốc tế ghi nhận khế chứa **caramboxin**, độc tố thần kinh chống chỉ định ở bệnh nhân suy thận (gây nấc cụt khó chữa, lú lẫn, co giật). R2/chuyên gia PHẢI xác nhận riêng trước khi món này (hoặc bất kỳ món dùng khế nào) được duyệt cho bệnh nhân CKD — không đưa vào `dishes.csv` khi chưa xác nhận. Số liệu định lượng có nguồn tìm được: natri toàn quốc trung bình 8,07 g muối/ngày năm 2020 (Lan et al. 2025, *Int J Public Health*, DOI 10.3389/ijph.2025.1608065) — không phân theo vùng miền, không dùng làm căn cứ so sánh Bắc/Trung/Nam.

### `DAT-05` Bảng tương tác thuốc – thực phẩm — KHÔNG GIỚI HẠN TRÊN
**Owner:** R2 · **P1** · 8h+ (mở) · **Deps:** DAT-01
`drug_food_interactions`: `drug_name, drug_class, food_or_nutrient, severity(high/moderate/low), mechanism, recommendation, source_ref`.
Bắt buộc có: Warfarin–vitamin K, ACEi/ARB–kali & muối thay thế, Statin–bưởi, Metformin–rượu & B12, Levothyroxine–canxi/đậu nành/cà phê, Digoxin–chất xơ cao, MAOI–tyramine, Allopurinol–rượu bia, lợi tiểu thiazide–kali.
**Nguồn `source_ref` ưu tiên:** **Dược thư Quốc gia Việt Nam 2022** (QĐ 3445/QĐ-BYT, 743 chuyên luận, tra cứu online miễn phí) — mỗi cặp tra chuyên luận thuốc tương ứng, `source_ref` dạng `Dược thư Quốc gia VN 2022, chuyên luận <tên thuốc>`. **Không dùng** Quyết định 5948/QĐ-BYT làm nguồn cho bảng này trừ khi ai đó mở file thật và xác nhận có mục thuốc-thực phẩm — mọi mô tả tìm được đều chỉ nói đây là danh mục tương tác **thuốc-thuốc** (633 cặp hoạt chất + 68 cặp nhóm dược lý), đừng suy đoán nó phủ cả thực phẩm.
**AC:** **≥80 cặp là SÀN, không phải trần** — 2026-08-05: đã điền `source_ref` cho 17/30 cặp (Warfarin, Digoxin, Enalapril, Atorvastatin, Hydrochlorothiazide, Colchicin, Allopurinol, Ciprofloxacin, Amlodipin, Gliclazide, Insulin — có chuyên luận riêng xác nhận trên Dược thư QGVN 2022), còn 13/30 cặp thiếu nguồn (Losartan, Simvastatin, Metformin, Levothyroxine, Furosemide, Spironolactone, Phenelzine, Tetracycline, Sắt, Canxi — chưa xác nhận được có chuyên luận riêng, KHÔNG suy đoán, cần R2 tự tra trực tiếp) · Mỗi cặp có nguồn · Khớp được cả theo hoạt chất lẫn theo nhóm thuốc · Test: hồ sơ dùng Warfarin + thực đơn nhiều rau ngót → sinh cảnh báo `high`.

### `DAT-18` ✅ Bảng `food_food_interactions` (tương tác thực phẩm-thực phẩm hoá sinh) — ĐÃ CODE, seed 9 cặp
**Owner:** R2 (verify) · **Trạng thái:** Schema + migration + seed xong, chờ R2 xác nhận trước khi dùng cho bệnh nhân
Bảng mới `src/db/models.py::FoodFoodInteraction` (migration `alembic/versions/5394cb31dc4e_...py`, đã test cả upgrade/downgrade trên SQLite scratch). Seed 9 cặp tương tác hoá sinh có PMID thật (`data/seeds/food_food_interactions.csv`, nạp qua `scripts/seed_db.py::seed_food_food_interactions`): polyphenol/tannin ức chế hấp thu sắt non-heme (Hurrell 1999 PMID 10999016, Brune 1989 PMID 2598894), vitamin C tăng hấp thu sắt (Siegenberg 1991 PMID 1989423), phytate gạo giảm hấp thu sắt (Tuntawiroon 1990 PMID 2401279), phytate giảm hấp thu magiê (Bohn 2004 PMID 14985216), canxi-sắt cạnh tranh hấp thu (Gaitán 2011 PMID 21795430), canxi ăn cùng bữa GIẢM nguy cơ sỏi thận oxalat — liên quan CKD (Curhan 1997 PMID 9092314), fructose và rượu/bia tăng acid uric — liên quan GOUT (Choi 2008 PMID 18244959, Choi 2004 PMID 15094272).
**AC:** Tất cả 9 dòng đang `verify_status=to_verify` — R2 xác nhận trước khi hiển thị cho chuyên gia/bệnh nhân · Chưa wiring vào agent/API (chỉ có bảng + seed, chưa có endpoint/logic dùng dữ liệu này) — việc tiếp theo cần bàn: hiển thị ở đâu trong UI, có nên sinh cảnh báo tự động trong `validate_menu` không.

### `DAT-19` ✅ Bảng `drug_meal_timing` (giờ dùng thuốc so với bữa ăn) — ĐÃ CODE, seed 6 thuốc
**Owner:** R2 (verify) · **Trạng thái:** Schema + migration + seed xong, chờ R2 xác nhận trước khi dùng cho bệnh nhân
Bảng mới `src/db/models.py::DrugMealTiming` (cùng migration với DAT-18). Seed 6 thuốc phổ biến của 4 nhóm bệnh (`data/seeds/drug_meal_timing.csv`): Metformin/Gliclazid (T2DM, Dược thư QGVN 2022), Allopurinol/Colchicin (GOUT, Dược thư QGVN 2022 tr.180-182/512-514), Levothyroxin (tránh cà phê, Benvenga 2008 PMID 18341376), Sắt bổ sung (uống cách ngày hấp thu tốt hơn hằng ngày, Stoffel 2017 PMID 29032957 — nghiên cứu công bố trên *Lancet Haematology*, mức bằng chứng cao).
**⚠️ Ranh giới an toàn (CLAUDE.md §3):** bảng này CHỈ mô tả thời điểm uống theo dược thư — TUYỆT ĐỐI không được diễn giải thành khuyên đổi liều/ngừng thuốc khi wiring vào UI/agent.
**AC:** Tất cả 6 dòng đang `verify_status=to_verify` · Nhịp bữa ăn tổng quát ĐTĐ2 (VD "tránh ăn tối muộn sau 20h", Sakai 2018 PMID 29375081) KHÔNG đưa vào bảng này vì không phải tương tác thuốc-bữa ăn cụ thể — cân nhắc thuộc phạm vi `AGT-11` (phân bổ bữa) thay vì bảng này · Chưa wiring vào agent/API.

### `DAT-20` ⏳ Merge ~39 giá trị GI mới vào `gi_values.csv` — CÓ DỮ LIỆU, CHƯA MERGE
**Owner:** R2 · **P2** · **Deps:** DAT-08
Research 2026-08-06 (agent B2a) tìm được ~39 giá trị GI mới có nguồn PMID/DOI thật, CHƯA được ghi vào `gi_values.csv` (vẫn còn 28 dòng cũ, không đổi). Nguồn chính: Chan 2001 *Eur J Clin Nutr* 55:1076-1083 (PMID 11781674, đã đọc toàn văn Bảng 1+2), Atkinson 2008 *Diabetes Care* 31:2281-2283 (PMC2584181), Henry 2021 *Nutr Diabetes* 11:2 compendium 940 món châu Á (PMID 33414403), Robert 2008 *Asia Pac J Clin Nutr* (PMID 18364324), Ramdath 2004 *Br J Nutr* (PMID 15182400).
**Món mới có GI (ví dụ):** cơm tấm 86, bún khô 61 (khác bún tươi 40 đã có), cháo trắng 78 (proxy), khoai môn 53 (proxy, dải rộng 53-77 tuỳ nguồn), sắn 94 (proxy Caribbean, MÂU THUẪN với nguồn khác cho 78 thang khác — cần R2 chọn), bí đỏ 64, chuối xanh 55, mít 41, ổi 19, sầu riêng 49, bánh cuốn 81 (proxy Singapore), xôi mặn 106, các loại đậu (đậu đỏ 24, đậu gà 28, đậu lăng 32, đậu nành 16), sữa/sữa chua/kem, đường/mật ong, bánh đa nướng 87.
**⚠️ Cảnh báo giá trị HIỆN CÓ đáng ngờ (không phải giá trị mới — cần R2 xem lại):** dưa hấu (CSV=51) thấp hơn nhiều y văn (dải thật 48-76, giá trị kinh điển 76); bánh mì (CSV=59) thấp bất thường (y văn 75-83); khoai lang (CSV=77) — một nguồn khác (Indonesia) cho giá trị phi lý 179 thang bánh mì, KHÔNG dùng.
**⚠️ Phát hiện quan trọng về nhãn nguồn:** "Chan2001_VN" (đã dùng cho 7 dòng hiện có) đo tại Sydney trên gạo/bún NHẬP TỪ Thái Lan/Úc/Trung Quốc — KHÔNG phải mẫu đo tại Việt Nam. Việt Nam không nằm trong danh sách quốc gia của compendium Henry 2021 — chưa có nghiên cứu GI nào đo trực tiếp trên người tại VN đạt chuẩn quốc tế. Cần sửa `note`/nhãn cho rõ, tránh hiểu nhầm.
**AC:** R2 tự quyết định khi 1 thực phẩm có GI mâu thuẫn giữa nhiều nguồn (VD sắt 78 vs 94) — không tự lấy trung bình, ghi rõ dải + từng nguồn · Chỉ dùng giá trị đo trên NGƯỜI (loại bỏ mọi eGI in-vitro) · Cập nhật `note` cho 7 dòng Chan2001_VN hiện có để không gây hiểu nhầm là "đo tại VN".

### `DAT-21` ⏳ Sửa lỗi trích dẫn trong `drug_food_interactions.csv` — CÓ PHÁT HIỆN, CHƯA SỬA
**Owner:** R2 · **P1** · **Deps:** DAT-05
Research 2026-08-06 (agent B2b) verify 30 dòng hiện có, phát hiện các lỗi trích dẫn CỤ THỂ (không phải nghi ngờ chung chung) — **CHƯA sửa file**, chờ R2 xác nhận trước khi đổi (đây là dữ liệu lâm sàng, không phải nhãn phân loại):
- **Dòng 2 (rau ngót), dòng 3 (cải bắp):** gán vào chuyên luận Warfarin nhưng chuyên luận thật (Dược thư QGVN 2022, tr.1710-1714) chỉ nêu "gan động vật, súp lơ, rau xanh" — không nêu đích danh rau ngót/cải bắp. Dòng 4 (súp lơ) hợp lệ.
- **Dòng 15 (levothyroxin+cà phê):** sai tên đồng tác giả trích dẫn (con số 36% đúng, tên tác giả sai — tác giả thật: Benvenga S, Bartolone L, Pappalardo MA et al.).
- **Dòng 16 (allopurinol+rượu):** chuyên luận Allopurinol thật (tr.180-182) không có mục tương tác rượu — nguồn đúng nên là Choi 2004 (PMID 15094272).
- **Dòng 17 (colchicin+bưởi):** chuyên luận Colchicin thật (tr.512-514) không nhắc bưởi, chỉ nêu chất ức chế CYP3A4/P-gp nói chung — cơ chế suy luận được nhưng nguồn trích sai; severity nên xem xét nâng lên `high` (khoảng trị liệu hẹp).
- **Dòng 23 (amlodipin+bưởi):** severity `moderate` có thể quá cao — bằng chứng thật chỉ AUC +16% (Josefsson 1996, PMID 8911887), không đổi HA/nhịp tim rõ rệt.
- **Dòng 28:** tên chuyên luận ghi "Sulfonylurea (Gliclazide)" không tồn tại trong Dược thư — tên đúng là "Gliclazid".
- **Dòng 30 (canxi+oxalat):** khuyến nghị hiện tại mâu thuẫn với chính bằng chứng trích trong dòng (Curhan 1997 cho thấy canxi ăn CÙNG bữa làm GIẢM nguy cơ sỏi, không phải nên tránh).
**AC:** Mỗi sửa đổi phải dẫn lại đúng trang/mục Dược thư QGVN 2022 hoặc PMID thay thế · Không tự đổi severity mà không có căn cứ định lượng (đúng CLAUDE.md §6) · Sau khi sửa, đổi `verify_status` dòng đó thành `verified`.

### `DAT-06` Ingest guideline vào RAG — KHÔNG GIỚI HẠN TRÊN
**Owner:** R2 · **P1** · 8h+ (mở) · **Deps:** SET-05
Thu thập tài liệu (BYT, ADA, KDIGO, AHA/DASH, ACR, tài liệu Viện Dinh dưỡng — ~15 là điểm khởi đầu, không phải đích). Chunk 500–800 token, overlap 100, embed, lưu `guideline_chunks` (pgvector) kèm metadata `{source, title, page, condition}`.
**AC:** **≥15 tài liệu là SÀN** — thêm tài liệu mới bất cứ khi nào tìm được nguồn guideline chính thức phù hợp 4 bệnh mục tiêu, không giới hạn số lượng · Truy vấn "protein cho CKD giai đoạn 4" trả về chunk đúng ở top-3 · Mỗi chunk có metadata đầy đủ · Có script `make ingest` chạy lại được.

### `DAT-11` Tích hợp Open Food Facts cho thực phẩm đóng gói
**Owner:** R2 · **P2** · 4h · **Deps:** DAT-02
Client gọi API Open Food Facts (`https://world.openfoodfacts.org/api/v2/product/{barcode}.json`, free, không cần key, giới hạn 15 req/phút/IP) để lấp các dòng `food_items` là sản phẩm đóng gói/công nghiệp mà NIN/USDA không có (mì gói theo nhãn hiệu cụ thể, nước chấm/gia vị đóng gói). `source='OFF'`, `source_ref='Open Food Facts, barcode:xxxxxxxxxxxxx'`.
**AC:** Tra được ≥10 sản phẩm Việt thật (VD mì Omachi đã xác nhận có trên nền tảng) · Ghi rõ giấy phép ODbL trong `data/README.md` (yêu cầu ghi nguồn khi dùng lại) · Test dùng mock, không gọi API thật trong CI.
> P2 vì đây là nhóm phụ (thực phẩm công nghiệp), không nằm trên đường găng — chỉ làm sau khi 150 thực phẩm cốt lõi (DAT-02) đã xong.

### `DAT-12` Bỏ trần số lượng EPIC 1/2 + fill dữ liệu thật không giới hạn
**Owner:** R2 · **P1** · mở (điều phối, không phải 1 khối việc) · **Deps:** DAT-01
Ticket điều phối cho việc bỏ trần cứng ở `DAT-02/04/05/06`, `CLN-02` (đã sửa AC, xem các ticket đó) và tiếp tục fill dữ liệu thật không giới hạn trên, chỉ giới hạn bởi có nguồn thật (RULE-2/DEC-008). Kế hoạch chi tiết + trạng thái từng nguồn: `docs/PLAN_DAT-12-uncap-data-and-db.md`.
**AC:** Mỗi ticket con (`DAT-02/04/05/06`, `CLN-02`) có AC "sàn tối thiểu, không trần" · `docs/PLAN_DAT-12-uncap-data-and-db.md` được cập nhật khi có tiến độ mới · Không hạ chuẩn nguồn gốc để chạy nhanh số lượng.

### `DAT-13` Rà soát & làm giàu các khoảng trống Na/K/P và source_ref còn lại
**Owner:** R2 · **P1** · mở (điều phối, không phải 1 khối việc) · **Deps:** DAT-04, DAT-12
Sau batch 48 nguyên liệu NIN nội bộ (2026-08-06), vẫn còn khoảng trống thật: 309 dòng thiếu Na/K trong sheet "Bảng TP có phospho", 152 dòng `food_items.template.csv` chưa nhập, 13 cặp `drug_food_interactions.csv` thiếu `source_ref`, 21 dòng trùng tên lệch kcal cần đối chiếu ấn bản NIN. Kế hoạch chi tiết + thứ tự ưu tiên tra chéo nguồn (NIN2017 PDF → USDA bulk → chỉ khi không tra được mới xét `estimated` có cơ sở, không suy đoán tùy ý): `docs/PLAN_DAT-13-fill-data-gaps.md`.
**AC:** Không tự gắn giá trị 0/trace cho Na/K/P mà không có `source_ref` cụ thể (mã NIN, FDC ID, hoặc lý giải khoa học rõ ràng cho nhóm "trace") · Mỗi batch chạy `validate_data.py` + `pytest` sạch trước khi commit · `docs/PLAN_DAT-13-fill-data-gaps.md` cập nhật tiến độ theo từng mục §2.

### `DAT-14` ✅ Mở rộng `purine_mg` từ Purine DB 2025 — ĐÃ LÀM (32 dòng mới, curated 1-152)
**Owner:** Claude (theo yêu cầu Hưng) · **Trạng thái:** Đã merge phần curated, còn phần NIN bulk (id 2000+) chưa làm
`data/PURINEDATABASEANDDATASOURCES2025.xlsx` ("USDA and ODS-NIH Database for the Purine Content of Common Foods" R2.0, 2025, 608 dòng NAm+nonNAm+alcohol) đã được trích thành `data/seeds/purine_db_reference.csv` (`scripts/extract_purine_db.py`, 475 dòng có số + trích dẫn `Table6`). Đã map thủ công (có review từng dòng, KHÔNG tự động) 32/366 dòng curated còn thiếu `purine_mg` — chỉ nhận match cùng loài/loại rõ ràng, bỏ qua match mơ hồ (VD "cải xanh" bị bỏ vì các dòng gần giống trong bảng nguồn thực ra khác loài thực vật). Script: `scripts/map_purine_to_food_items.py` (idempotent, có `--dry-run`).
**Còn lại:** 334 dòng curated không match được (không có trong 475 dòng nguồn, hoặc match quá mơ hồ để tin) · Toàn bộ dải id 2000-4077 (NIN2017 bulk extract, tên món lẫn text tiếng Anh OCR) chưa được thử map — cần làm sạch tên món trước (tách phần tiếng Anh OCR khỏi `name_vi`) rồi mới map được, việc riêng.
**AC nếu làm tiếp:** Giữ nguyên tắc "chỉ map khi chắc chắn cùng loài", không hạ chuẩn để tăng số lượng.

### `DAT-15` ⚠️ `sugar_g` (đường tự do) KHÔNG thể lấp từ USDA local — cần R2 quyết định schema
**Owner:** R2 · **P2** · **Deps:** DAT-07
Research 2026-08-06: quét toàn bộ `food_nutrient.csv` của USDA FDC bulk (script `scripts/scan_usda_sugar_coverage.py`, đã chạy, kết quả ghi `data/seeds/usda_sugar_coverage.csv`) cho 6.861 fdcId nguồn USDA trong `food_items.csv`:
- **"Sugars, added" (nutrient 1235, gần nghĩa free sugars nhất): 0/6.861 dòng có dữ liệu (0%)** — bộ SR Legacy/Foundation Foods dự án dùng KHÔNG có trường này.
- **"Total Sugars" (nutrient 2000/1063): 5.620/6.861 dòng (81.9%)** — có dữ liệu thật nhưng **khác nghĩa** `sugar_g` mà DAT-07 định nghĩa (đường tự do theo WHO, loại trừ đường tự nhiên trong sữa/trái cây nguyên quả).
**Vì sao KHÔNG tự lấp:** đổ "Total Sugars" vào `sugar_g` rồi để `T2DM-SUG-01` (đường ≤10%E) áp ngưỡng sẽ gắn cờ SAI cho bệnh nhân ăn trái cây/sữa nguyên chất — vi phạm RULE-2 kiểu ngược (đúng số, sai ngữ nghĩa trường). `scripts/extract_usda_bulk.py` đã cố ý để trống vì lý do này từ trước, quyết định này giữ nguyên.
**Đề xuất (cần R2 chốt, không phải Claude tự quyết schema):** (1) Thêm cột MỚI `total_sugar_g` tách biệt khỏi `sugar_g`, dùng cho hiển thị thông tin/không áp ngưỡng free-sugar, kèm Alembic migration — 81.9% dữ liệu đã sẵn sàng ở `usda_sugar_coverage.csv`; hoặc (2) không thêm gì, chờ có nguồn added-sugar/free-sugar thật (VD USDA Branded Foods có nhãn dinh dưỡng, hoặc tính tay cho món chế biến có công thức biết trước lượng đường thêm).
**AC:** Không tự thêm cột vào schema production khi chưa R2 duyệt hướng semantics · Nếu chọn hướng (1), migration phải đi kèm cùng PR (CLAUDE.md §4).

### `DAT-16` ✅ Mở rộng `serving_sizes.csv` 5 → 174 dòng (WWEIA reference) — ĐÃ LÀM
**Owner:** Claude (theo yêu cầu Hưng) · **Trạng thái:** Xong, cần R2 xác nhận cách dùng
Không có khảo sát khẩu phần món Việt quy mô lớn công khai để mở rộng 5 dòng gốc lên 100-200 mà vẫn giữ nguồn thật. Thay vào đó: tính TRUNG VỊ khẩu phần thật từ `food_portion.csv` (47.446 bản ghi khẩu phần USDA) theo 172 nhóm thực phẩm chính thức **WWEIA** (What We Eat In America — hệ phân loại dùng trong khảo sát NHANES), lấy nhóm có ≥5 mẫu (169/172 nhóm đạt). Script: `scripts/build_serving_sizes_wweia.py`. 5 dòng gốc (khớp món Việt cụ thể: bát phở, bát cơm...) giữ nguyên, không ghi đè — 169 dòng mới thêm với tiền tố `category=wweia_<mã>` để phân biệt rõ.
**⚠️ Giới hạn phải đọc trước khi dùng:** đây là khẩu phần theo THÓI QUEN ĂN UỐNG MỸ (khảo sát NHANES), KHÔNG PHẢI khẩu phần người Việt — dùng làm tham chiếu/dự phòng khi không có nguồn khẩu phần Việt Nam cụ thể, đã ghi rõ trong cột `source` từng dòng.
**AC nếu dùng tiếp:** R2 xác nhận UI/menu engine có phân biệt được 2 loại nguồn (VN cụ thể vs WWEIA tham chiếu) trước khi hiển thị cho chuyên gia/bệnh nhân.

### `DAT-17` ✅ Lấp `category` cho food_items nguồn USDA — ĐÃ LÀM (2% → 96%)
**Owner:** Claude (theo yêu cầu Hưng) · **Trạng thái:** Xong
Dịch trực tiếp phân loại chính thức `food_category` của USDA FoodData Central (28 nhóm, `food_category.csv` trong bulk download) sang nhãn tiếng Việt, join qua `fdc_id` (script `scripts/fill_category_from_usda.py`, có `--dry-run`). Đây là gán nhãn phân loại/tổ chức dữ liệu, KHÔNG phải giá trị lâm sàng — không thuộc phạm vi RULE-2 (không cần `source_ref` riêng cho `category`). Kết quả: 6.870 dòng được gán, độ phủ `category` 2% → 96% (7.022/7.315).
**Còn lại:** 293 dòng không có `category` — gồm 22 dòng thiếu số liệu hoàn toàn (đã biết từ trước) + phần còn lại là dòng NIN/curated chưa từng có `category` và không thuộc phạm vi script này (script chỉ xử lý `source=USDA`).

---

### `DAT-07` Mở rộng schema `food_items`: đường tự do + nguồn GI riêng (anchor ĐTĐ2)
**Owner:** R2 · **P1** · 3h · **Deps:** DAT-02
Bổ sung `sugar_g` (cho ngưỡng đường tự do WHO) và cặp `gi_source`/`gi_source_ref` để GI có nguồn riêng, tách khỏi `source_ref` của NIN (RULE-2). Thêm helper `available_carb_g` (carb − xơ) và `glycemic_load(grams)` (None-safe). GI lấy từ **Atkinson 2021** (ISO, >4000 món) + **Mai 2001** (GI món Việt: gạo/bún/phở).
**AC:** Tạo `FoodItem` có `gi_index` mà thiếu nguồn GI → bị chặn (RULE-2) · `glycemic_load` trả `None` khi thiếu GI (không phải 0) · `sugar_g > carb_g` bị chặn · `validate_data.py` áp cùng ràng buộc trên CSV · Có unit test cho cả 4 nhánh.
> Đây là thay đổi schema tối thiểu để chốt ĐTĐ2 làm bệnh chính. GI phủ thưa nên menu engine phải suy giảm mềm khi thiếu GI.

---

## EPIC 2 — CLINICAL ENGINE (S2–S3) — *Owner chính: R2, review R1*

### `CLN-01` Module tính năng lượng
**Owner:** R2 · **P0** · 6h · **Deps:** SET-01
`src/clinical/energy.py`: BMR theo Mifflin-St Jeor, hệ số hoạt động, TDEE, điều chỉnh theo mục tiêu cân nặng (giảm/giữ/tăng), dùng cân nặng lý tưởng khi BMI > 30.
**AC:** ≥12 unit test bao gồm biên (tuổi 18, tuổi 90, BMI 15, BMI 40) · Docstring ghi rõ công thức + nguồn · Không gọi LLM, không truy vấn DB.

### `CLN-02` Bảng quy tắc lâm sàng — KHÔNG GIỚI HẠN TRÊN
**Owner:** R2 · **P0** · 8h+ (mở) · **Deps:** DAT-01
`data/seeds/clinical_rules.csv` + loader. Mỗi rule: `id, condition_code, stage, nutrient, operator, threshold, unit, per(day|meal|kg_bw), severity(hard|soft), guideline_ref`.
Phủ: ĐTĐ2 (carb %, chất xơ, GI), THA/tim mạch (Na, chất béo bão hoà), CKD G3a–G5 (protein/kg, K, P, Na), Gout (purine, cồn, fructose).
**AC:** **≥40 rule là SÀN** (hiện đã có 21 rule) — thêm rule mới bất cứ khi nào tìm được ngưỡng guideline chưa phủ, không giới hạn số lượng trên, mỗi rule có `guideline_ref` · Sửa ngưỡng chỉ cần sửa dữ liệu, **không phải sửa code** · Có test rule bị trùng/xung đột.

### `CLN-03` Bộ tính định mức cá thể
**Owner:** R2 · **P0** · 8h · **Deps:** CLN-01, CLN-02
`compute_targets(profile) -> ClinicalTargets` kèm `applied_rule_ids`. Xử lý **đa bệnh lý**: khi 2 rule cùng chất, lấy **ngưỡng nghiêm ngặt hơn** (fail-safe).
**AC:** Case "Nam 58t, 65kg, 165cm, ĐTĐ2 + CKD G3b" trả kết quả khớp với tính tay của R2 · Đa bệnh lý luôn chọn ngưỡng chặt hơn, có test riêng · Output kèm danh sách rule đã áp dụng để hiển thị trên UI.

### `CLN-04` Rules Engine — Bounds Checker
**Owner:** R2 · **P1** · 8h · **Deps:** CLN-03
`validate_menu(menu_nutrition, targets) -> list[Violation]`. Violation gồm: `nutrient, actual, limit, severity, message_vi, suggestion`. Hard violation → chặn phát hành; soft → cảnh báo.
**AC:** Thực đơn 3000mg Na cho bệnh nhân THA → hard violation kèm gợi ý cụ thể ("bỏ nước chấm, giảm 1/2 nước dùng") · Sai lệch năng lượng ±10% là soft, ±25% là hard.

### `CLN-05` Kiểm tra dị ứng
**Owner:** R2 · **P1** · 4h · **Deps:** DAT-02
Đối chiếu dị ứng của bệnh nhân với nguyên liệu (kể cả nguyên liệu ẩn: nước mắm↔cá, chả↔thịt+bột, bánh phở↔gạo).
**AC:** Dị ứng hải sản + thực đơn có bún riêu (mắm tôm) → **chặn cứng** · Dị ứng luôn là `hard`, không bao giờ chỉ cảnh báo.

### `CLN-06` Kiểm tra tương tác thuốc – thực phẩm
**Owner:** R2 · **P1** · 6h · **Deps:** DAT-05, CLN-04
Khớp thuốc bệnh nhân đang dùng với thực phẩm/vi chất trong thực đơn, sinh cảnh báo có mức độ và khuyến nghị.
**AC:** ≥90% phát hiện trên 20 case test · Cảnh báo `high` hiển thị badge đỏ trên UI · Không cảnh báo tràn lan (false positive < 20%).

### `CLN-07` OOV Estimator
**Owner:** R2 · **P2** · 10h · **Deps:** DAT-04
Món không có trong DB: (1) tra `aliases` → (2) tìm mờ tên món → (3) LLM phân rã thành nguyên liệu + gram ước tính → tra SQL từng nguyên liệu → cộng lại.
**AC:** Kết quả **luôn** gắn `is_estimated=true` + `confidence` (0–1) · UI hiển thị nhãn "ước tính" rõ ràng · Không bao giờ để LLM trả thẳng con số kcal · 10 case món địa phương cho sai lệch < 30%.

---

### `CLN-08` Rule đường tự do WHO cho ĐTĐ2
**Owner:** R2 · **P1** · 2h · **Deps:** CLN-02, DAT-07
Thêm rule `T2DM-SUG-01` (đường tự do < 10% năng lượng, WHO 2015) dùng cột `sugar_g` (DAT-07). Bổ sung `sugar_g` vào `KCAL_PER_GRAM` cho basis `pct_energy`. Validator: nhãn "Đường" + gợi ý, và **cảnh báo `incomplete_data`** khi có món thiếu `sugar_g` (tổng đường thấp hơn thực tế → không được coi là đạt ngưỡng).
**AC:** compute_targets ĐTĐ2 sinh trần `sugar_g = E×10%/4` · thực đơn thừa đường → soft violation · thực đơn thiếu số liệu đường → cảnh báo `incomplete_data` (không im lặng) · rule scope T2DM để không đụng test HTN hiện có.
> Đặt `severity=soft` dù WHO là khuyến nghị mạnh: dữ liệu đường thường thiếu (`sugar_is_complete=False`), chặn cứng trên tổng thiếu hụt sẽ sai. Broaden sang BASE khi phủ đủ `sugar_g`.

---

> ❓ **ĐỀ XUẤT (2026-08-06, Claude theo yêu cầu Hưng — CẦN R2/ĐỘI DUYỆT, chưa gán sprint/giờ).** Đọc trực tiếp công thức trong `data/Bảng xác định nhu cầu dinh dưỡng + thực đơn.xlsx` (sheet "Bước 1+2" — chính file chuyên gia dinh dưỡng dự án đang dùng thật trên Excel), phát hiện 3 khoảng cách giữa công thức hệ thống hiện tại và thực hành chuyên gia. Chi tiết cell/formula trích dẫn trong `DEVLOG.md` entry cùng ngày.

### `CLN-09` Đối chiếu công thức BMR/TDEE với thực hành chuyên gia thật — **ĐÃ CHỐT** (WHO/FAO/UNU là mặc định hệ thống)
**Owner:** R2 · **P1?** · **Deps:** CLN-01
Hệ thống trước đây dùng Mifflin-St Jeor + `ACTIVITY_FACTOR`. Chuyên gia dinh dưỡng dự án dùng **WHO/FAO/UNU (1985)** — công thức tuyến tính theo tuổi+cân nặng (không có chiều cao) + hệ số lao động riêng (PAL, "Bước 1+2!I5:J17"). Hai công thức cho kết quả khác nhau đáng kể.
- **ĐÃ CHỐT (2026-08-06, Hưng xác nhận):** "ưu tiên sử dụng từ bản Excel, kể cả BMR và ActivityLevel" — `compute_bmr()`/`compute_tdee()` trong `src/clinical/energy.py` giờ dùng **WHO/FAO/UNU làm mặc định** (`bmr_who_fao_unu()` + `pal_who_fao()`), không còn Mifflin-St Jeor. Mifflin-St Jeor được giữ lại làm hàm THAM KHẢO/so sánh (`compute_bmr_mifflin()`, `compute_tdee_mifflin()`), không còn dùng trong `compute_targets()`.
- **Đã chốt trước đó (2026-08-06, Hưng xác nhận):** `ActivityLevel` đổi hẳn sang 4 mức nhãn "loại lao động" của chuyên gia — `LIGHT`/`MODERATE`/`HEAVY`/`VERY_HEAVY`. Đã cập nhật `src/db/models.py`, `src/api/routes/patients.py` (`Literal` validation), `scripts/seed_demo_users.py`.
- **Dọn dẹp kèm theo:** `ACTIVITY_FACTOR` (dict cũ dùng cho Mifflin) đã bị XOÁ khỏi `src/clinical/models.py` — không còn consumer nào sau khi `energy.py` chuyển sang dùng `_ACTIVITY_FACTOR_MIFFLIN` cục bộ (chỉ phục vụ hàm tham khảo). `tests/conftest.py::modest_menu` đã tăng định lượng để khớp mục tiêu kcal/chất xơ cao hơn của WHO/FAO/UNU. 164/164 test pass, `ruff`/`mypy` sạch.
- **Research đã làm (2026-08-06, theo yêu cầu Hưng "chứng minh bằng nghiên cứu"), tóm tắt — chi tiết + nguồn trích dẫn đầy đủ trong `DEVLOG.md`:**
  1. BMR **có** khác theo dân tộc/quần thể — bằng chứng thật nhưng KHÔNG nhất quán chiều: Mifflin-St Jeor chính xác nhất ở phụ nữ UAE (lệch Harris-Benedict 40,9%), nhưng WHO/FAO/UNU chính xác nhất còn Mifflin **tệ nhất** ở bệnh nhân ĐTĐ2 Hàn Quốc (PubMed 37266123, 2023). **Không tìm được nghiên cứu đo lường (calorimetry) trên người Việt Nam** — khoảng trống dữ liệu thật, không giả định.
  2. WHO/FAO/UNU (1985) = phương trình Schofield, dữ liệu gốc lệch nhiều về dân số châu Âu/Mỹ; hội đồng FAO/WHO/UNU 2001 đã cân nhắc đổi nhưng **quyết định giữ nguyên** vì cải thiện không đáng kể (Henry 2005, *Public Health Nutrition*).
  3. **Chưa xác nhận được** Viện Dinh dưỡng VN (NIN) có quy định chính thức dùng công thức nào — bản PDF "Nhu cầu dinh dưỡng khuyến nghị cho người Việt Nam" tra được không lộ rõ mục công thức BMR (có thể do OCR bản mirror, không phải bằng chứng NIN không có). **Cần R2 xác nhận trực tiếp bằng bản gốc/hỏi chuyên gia** nếu muốn đối chiếu thêm — không chặn quyết định hiện tại (đã ưu tiên nguồn thực hành trực tiếp của chuyên gia dự án).
  4. ADA không quy định công thức BMR riêng cho ĐTĐ2. KDOQI (CKD) dùng khoảng kcal/kg (25–35, cập nhật 2020) — con số THỰC NGHIỆM theo cân nặng, không suy ra từ 1 công thức BMR nào. Không tìm được cơ sở đổi công thức BMR riêng cho CKD/THA/Gout.
  5. **Thang hệ số cũ (`ACTIVITY_FACTOR`/`_ACTIVITY_FACTOR_MIFFLIN`, 1.375/1.55/1.725/1.9) là QUY ƯỚC PHỔ BIẾN trong công cụ tính calo trực tuyến, KHÔNG truy được về 1 nguồn học thuật/hướng dẫn lâm sàng đơn nhất** — đây là lý do chính khiến `pal_who_fao()` (có nguồn Excel chuyên gia rõ ràng) được ưu tiên làm mặc định thay vì giữ thang cũ.
- **Cơ sở quyết định cuối:** không có bằng chứng học thuật đủ mạnh để khẳng định công thức nào "đúng hơn" cho người Việt (bằng chứng trái chiều tuỳ quần thể, thiếu dữ liệu Việt Nam trực tiếp) — quyết định dựa trên WHO/FAO/UNU là công thức chuyên gia dinh dưỡng DỰ ÁN đang dùng thật (nguồn thực hành trực tiếp), không phải vì có bằng chứng học thuật WHO/FAO/UNU chính xác hơn cho người Việt. Giới hạn này ghi rõ trong docstring `src/clinical/energy.py`.
**AC (đã hoàn thành):** ✅ Quyết định ghi vào DEVLOG dạng ADR · ✅ `compute_targets()`/`compute_tdee()` đổi mặc định · ✅ Test suite cập nhật (164/164 pass), `ruff`/`mypy` sạch · ⏳ Chưa chạy lại 60 case eval đối chiếu chuyên gia thật (R2 nên làm khi có bộ eval, không chặn merge code) · ⏳ Chưa xác nhận trực tiếp với NIN (không chặn quyết định, chỉ để đối chiếu thêm nếu cần).

### `CLN-10` Phân loại nguồn đạm/chất béo động vật–thực vật (ĐV/TV) — ĐỀ XUẤT
**Owner:** R2 · **P2?** · **Deps:** DAT-02
Chuyên gia tính khẩu phần Protein 20% năng lượng (**35% động vật / 65% thực vật**) và Lipid 25% (**50/50 ĐV/TV**) — hệ thống hiện chỉ có tổng `protein_g`/`fat_g`, KHÔNG phân biệt nguồn ĐV/TV cho từng `food_item`. Đây là chiều dữ liệu hoàn toàn mới, cần thêm cột (VD `protein_animal_g`/`protein_plant_g`, hoặc đơn giản hơn: tag `protein_source: animal|plant|mixed` per food_item rồi suy ra tỷ lệ khi tính tổng).
**AC:** Không suy đoán ĐV/TV cho food_item đã có sẵn nếu không tra được nguồn xác nhận (đúng RULE-2/DEC-008 — nhiều món "mixed" thật sự, VD canh nấu cả thịt lẫn đậu) · Rule mới (nếu thêm) phải có `guideline_ref` thật, R2 tự tra chứ đừng copy thẳng con số 35/65 từ 1 bảng Excel nội bộ không rõ nguồn gốc học thuật · Bàn phạm vi trước — có thể việc này lớn hơn thời gian còn lại của dự án, cân nhắc để P3/không làm nếu quá tốn công so với giá trị.

### `CLN-11` 🔴 Rà soát ngưỡng CKD sai/lệch nguồn — CẦN R2 XỬ LÝ TRƯỚC KHI DEMO
**Owner:** R2 · **P0** · **Deps:** CLN-01
Research xác minh 21 dòng `clinical_rules.csv` (2026-08-06, dùng nguồn sơ cấp: KDIGO 2024 full text, KDOQI 2020 full PDF, NIN 2016 full PDF, ADA Standards of Care 2026 §5/§13) phát hiện nhiều rule ĐANG CHẠY (`severity=hard`, tức chặn cứng thực đơn) có ngưỡng lệch hoặc trích dẫn sai so với chính guideline được ghi. Đây không phải lỗi định dạng — đây là rủi ro lâm sàng thật, để nguyên có thể chặn nhầm/thả nhầm thực đơn.

**🔴 Nguy hiểm nhất — protein CKD G5 không phân biệt lọc máu:**
`CKD-PRO-01` (protein_g max 0.8 g/kg, `hard`, áp cho `G3a,G3b,G4,G5`) ghi nguồn KDIGO 2024 Rec 3.3.1.1 — đúng cho CKD **chưa lọc máu**. Nhưng hệ thống hiện **không có mã giai đoạn riêng cho G5D (đang lọc máu)** — bệnh nhân lọc máu vẫn bị áp trần 0.8 g/kg, trong khi KDOQI 2020 mục 3.0.3/3.0.4 yêu cầu **1.0–1.2 g/kg/ngày** cho nhóm này (nguy cơ suy dinh dưỡng protein-năng lượng nếu áp nhầm trần thấp). Cần: (1) thêm mã giai đoạn `G5D` phân biệt với `G5`, (2) thêm rule protein riêng cho G5D theo KDOQI 2020 3.0.4, (3) rule đồng mắc T2DM+CKD riêng theo KDOQI 2020 3.0.2 (0.6–0.8 g/kg, OPINION — DEC-007 hiện lấy protein theo CKD nên có thể đã đúng hướng, cần R2 xác nhận).

**🔴 Ba rule kali trích dẫn sai mức chứng cứ:**
`CKD-K-01/02/03` (k_mg max 3000/2500/2000 theo G3/G4/G5, cả 3 đều `hard`) ghi nguồn "KDOQI 2020 - kali theo giai đoạn CKD". Research xác nhận KDOQI 2020 mục 6.4.1 chỉ nêu nguyên tắc chung ("adjust dietary potassium intake to maintain serum potassium within normal range", mức **OPINION**) và **tự thừa nhận chưa có bằng chứng cho ngưỡng theo từng giai đoạn cụ thể** ("There is a need to study what constitutes an optimal dietary potassium intake according to different stages of CKD"). Ba con số mg cụ thể không truy được về đúng mục này.

**🟠 Khác (mức độ thấp hơn, vẫn cần xử lý):**
- `T2DM-CARB-01/02` (carb 45–55%E): ADA/EASD 2019 Consensus + ADA 2026 §5 nói rõ "không có tỷ lệ % lý tưởng"; NIN 2016 §4.1 khuyến nghị 55–65%E cho người Việt — sàn 45% thấp hơn khuyến nghị VN.
- `BASE-FIB-01`/`T2DM-FIB-01` (grade "A"): ADA 2026 Rec 5.24 ghi rõ **grade B**, không phải A.
- `T2DM-PRO-01` (protein ≥15%E): NIN 2016 §2.1 ghi AMDR 13–20%E, tối thiểu 1.13 g/kg — 15% không khớp cận dưới 13%.
- `HTN-FAT-01` (lipid ≤30%E, gán "AHA"): AHA 2021 không đặt mốc %; NIN 2016 §3.2 khuyến nghị chặt hơn (≤25%).
- `CKD-P-01/02` (phospho 1000/900mg, gán "KDOQI 2020"): KDOQI 2020 mục 6.3.1 nói điều chỉnh theo phosphat huyết thanh, không có mốc mg cụ thể — mốc 800-1000mg thuộc KDOQI **2003** (Bone Metabolism), đã cũ. Riêng 900mg không xác minh được ở bất kỳ nguồn nào.
- `GOUT-PUR-01` (150mg), `GOUT-NA-01` (nguồn ghi "Bộ Y tế"): ACR 2020 không định lượng purine bằng mg; chưa tìm được văn bản BYT có số hiệu cho gout.
- Đã xác nhận KHỚP đúng (không cần sửa): `BASE-NA-01`, `T2DM-SUG-01`, `T2DM-PRO-02`, `CKD-PRO-01` (đúng cho non-dialysis), `CKD-PRO-05`, `CKD-NA-01`, `HTN-NA-01`.

**AC:** R2 tự tra lại từng rule LỆCH bằng bản gốc (không suy đoán từ báo cáo này), quyết định giữ/sửa/xoá + ghi ADR vào DEVLOG · Ưu tiên tuyệt đối 2 mục 🔴 vì đang `hard` và chạy thật · KHÔNG tự đổi ngưỡng khi chưa R2 duyệt (đúng CLAUDE.md §6) · Sau khi R2 chốt, cập nhật `verify_status` tương ứng (hiện 100% `to_verify`).

### `AGT-11` Ràng buộc phân bổ dinh dưỡng theo bữa (Sáng/Trưa/Tối/Phụ tối) — ĐỀ XUẤT
**Owner:** R1 · **P2?** · **Deps:** AGT-09 (CP-SAT)
Chuyên gia chia định mức CẢ NGÀY thành 4 bữa theo tỷ lệ cố định — **Sáng 25% / Trưa 35% / Tối 30% / Phụ tối 10%** — áp dụng ĐỀU cho kcal và từng macro (P/L/G), không chỉ tổng ngày. Hệ thống hiện tại (`CPSATMenuOptimizer`, `validate_menu`) **chỉ kiểm tổng ngày**, không có ràng buộc/target theo từng bữa — 1 thực đơn có thể dồn hết carb vào 1 bữa mà vẫn "pass" nếu tổng ngày đúng, dù thực hành lâm sàng thật (đặc biệt ĐTĐ2, kiểm soát đường huyết sau ăn) quan tâm phân bổ theo bữa.
**AC:** Bàn kỹ trước khi code — thêm ràng buộc per-slot vào CP-SAT làm bài toán CHẶT hơn, có thể tăng tỷ lệ infeasible (đã từng bị hồi quy hiệu năng 1 lần vì thêm ràng buộc/dữ liệu không tính trước tác động, xem DEVLOG DEC-017) · Nếu làm, nên bắt đầu bằng ràng buộc MỀM (soft, cảnh báo lệch tỷ lệ) trước khi làm cứng · Cần quyết định tỷ lệ 25/35/30/10% là cố định hay chỉ là 1 gợi ý mặc định có thể chỉnh theo bệnh nhân.

---

## EPIC 3 — AGENT (S3) — *Owner chính: R1*

### `AGT-01` State schema & khung graph
**Owner:** R1 · **P0** · 6h · **Deps:** SET-01
`src/agents/state.py` (`NutriState`) + `graph.py` với 8 node, conditional edges, Postgres checkpointer.
**AC:** Graph compile được, vẽ được sơ đồ bằng `graph.get_graph().draw_mermaid()` · Sơ đồ này dán thẳng vào `ARCHITECTURE.md`.

### `AGT-02` Node `load_profile` + `compute_targets`
**Owner:** R1 · **P0** · 4h · **Deps:** AGT-01, CLN-03
Nạp hồ sơ từ DB, gọi clinical engine. **Không LLM.**
**AC:** State sau 2 node có đủ `profile` + `targets` + `applied_rule_ids` · Test không cần API key LLM.

### `AGT-03` Node `retrieve_context` (Hybrid RAG)
**Owner:** R1 · **P1** · 8h · **Deps:** DAT-06
BM25 (Postgres full-text) + vector (pgvector), kết hợp bằng RRF. Đồng thời truy vấn SQL lấy danh sách thực phẩm ứng viên đã lọc theo bệnh lý và dị ứng.
**AC:** Top-5 chunk liên quan cho 10 truy vấn mẫu · Danh sách ứng viên đã loại sẵn thực phẩm cấm (VD: CKD → loại thực phẩm giàu K).

### `AGT-04` Node `generate_menu` (LLM + structured output)
**Owner:** R1 · **P0** · 10h · **Deps:** AGT-03
Prompt + Pydantic schema. **LLM chỉ trả `food_id`/`dish_id` + gram + slot bữa ăn.** Prompt chứa: định mức, ứng viên, sở thích, vùng miền, feedback lỗi lần trước.
**AC:** Output luôn parse được (có retry parse) · **Test: schema không có field nào cho phép LLM ghi kcal/na/protein** · `food_id` không tồn tại → reject, không tự bịa.

### `AGT-05` Node `compute_nutrition`
**Owner:** R1 · **P0** · 4h · **Deps:** AGT-04, DAT-02
Cộng dinh dưỡng bằng SQL từ `food_id` + gram. Sinh `sources[]`.
**AC:** Kết quả khớp tính tay trên 5 thực đơn mẫu · Mọi item có `source` · **Không** import module LLM nào trong file này (test tự động kiểm tra).

### `AGT-06` Node `validate` + retry loop
**Owner:** R1 · **P1** · 8h · **Deps:** CLN-04, CLN-05, AGT-05
Conditional edge: PASS → `explain`; FAIL & retry<3 → `build_feedback` → quay lại `generate_menu`; FAIL & retry=3 → fallback thực đơn mẫu + gắn cờ `needs_attention`.
**AC:** Feedback nêu **lỗi cụ thể** ("Na vượt 900mg do nước mắm + bột canh"), không phải "hãy thử lại" · Không vòng lặp vô hạn · Fallback luôn có sẵn cho 4 nhóm bệnh.

### `AGT-07` Guardrail chặn chỉ định y khoa
**Owner:** R1 · **P0** · 8h · **Deps:** AGT-01
Tầng 1: regex tiếng Việt (liều, mg thuốc, "có nên uống", "bị bệnh gì", "ngừng thuốc"…) + LLM classifier. Trả về câu trả lời chuẩn + gợi ý chuyển chuyên gia.
**AC:** **≥95% chặn đúng trên 20 câu red-team** · Không chặn nhầm câu hỏi dinh dưỡng bình thường (false positive < 10%) · Có bộ test riêng `tests/unit/test_guardrail.py`.

### `AGT-08` LangSmith tracing + đo chi phí
**Owner:** R1 · **P2** · 4h · **Deps:** AGT-06
Bật tracing, gắn tag theo node, log token và chi phí mỗi request.
**AC:** Xem được trace đầy đủ 1 lần sinh thực đơn trên LangSmith · Có số "chi phí trung bình / thực đơn" để trả lời Q&A · Screenshot cho Deliverable #4.

### `AGT-09` CP-SAT menu optimizer (thay thế vòng lặp sinh-rồi-thử của LLM)
**Owner:** R1 · **P1** · 8h · **Deps:** AGT-04, AGT-05
`generate_menu` hiện để LLM đoán food_id+grams rồi `validate` kiểm tra, sai thì `build_feedback` cho LLM đoán lại (tối đa 3 lần, AGT-06/R20.3). Thay bằng `CPSATMenuOptimizer` implement thẳng `Protocol MenuGenerator` — dùng OR-Tools CP-SAT giải trực tiếp bài toán ràng buộc (chọn food_id + gram sao cho tổng dinh dưỡng nằm trong định mức + phủ đủ nhóm thực phẩm bắt buộc) trên `candidates` đã lọc dị ứng ở `retrieve_context`. Không đổi contract, không đổi graph — cắm thẳng vào `generate_menu` node hiện có.
**AC:** Implement `Protocol MenuGenerator` (chỉ trả `food_id`+`grams`, RULE-1) · Docstring khai `LLM: NO` (R20.1) · Trả `MenuDraft` rỗng khi infeasible để route hiện có tự chuyển `fallback` (không route mới) · ≥1 test happy path + ≥1 test infeasible · `ortools` thêm vào `requirements.txt`.

### `AGT-10` Nối CP-SAT vào graph (hybrid CP-SAT → Gemini)
**Owner:** R1 · **P1** · 6h · **Deps:** AGT-09
AGT-09 mới tạo `CPSATMenuOptimizer` đứng riêng, `build_nutricare_graph()` vẫn luôn dùng Gemini. Ticket này: (a) gộp model CP-SAT thành **một model cả ngày** thay vì chia 4 bữa theo tỉ lệ cố định — cách cũ khiến bữa nhỏ dễ vô nghiệm, tổng ngày hụt, `validate` báo vi phạm; (b) `HybridMenuGenerator` (`src/agents/hybrid.py`) — lượt đầu CP-SAT, chuyển Gemini khi vô nghiệm hoặc khi đã có feedback (CP-SAT tất định nên retry cùng input là vô nghĩa); (c) `settings.menu_generator` (`hybrid`/`cpsat`/`gemini`, mặc định `hybrid`) để `assembly.py` chọn generator.
**AC:** Graph chạy hết với CP-SAT thật **không cần API key** (CI kiểm được luồng thật) · Tổng dinh dưỡng đối chiếu bằng `compute_nutrition` nằm trong mọi ngưỡng của `compute_targets` · `retry_count == 1` và không rơi `fallback` ở happy path · Hybrid không chạm LLM khi CP-SAT giải được (test bằng spy) · Không đổi `graph.py`, không thêm route.

---

## EPIC 4 — BACKEND (S2–S4) — *Owner chính: R3*

### `BE-01` Schema DB + Alembic ✅ (khung đã build, còn phần tích hợp)
**Owner:** R3 · **P0** · 8h · **Deps:** SET-05
Toàn bộ bảng theo `ARCHITECTURE.md` §5. Migration chạy được từ trắng.
**AC:** `alembic upgrade head` trên DB rỗng thành công · Có index cho các truy vấn nóng · `audit_log` không có API xoá.
**2026-08-05 — đã làm:** `src/db/models.py` (15 bảng SQLAlchemy, khớp ERD đã cập nhật ở `ARCHITECTURE.md` §5, bổ sung 6 bảng ERD cũ chưa vẽ: `dishes`, `dish_ingredients`, `serving_sizes`, `patient_medications`, `patient_allergies`, `food_logs`, `guideline_chunks`) · `alembic/` init + migration `initial schema - BE-01`, đã test `upgrade head` / `downgrade base` sạch trên SQLite trắng · `tests/test_db_models.py` (6 test: tạo bảng, insert/round-trip, quan hệ dish↔ingredient không lưu dinh dưỡng đúng RULE-1) · `src/db/base.py` (session factory + FastAPI dependency `get_db()`).
**Còn lại (chưa làm trong lượt này):** index cho truy vấn nóng (mới có index mặc định theo FK/unique, chưa rà theo pattern truy vấn thật của BE-03..BE-07) · chưa nối `src/api/routes.py` dùng `get_db()` thay vì CSV loader hiện tại (đó là việc của BE-03 trở đi) · `psycopg2-binary` chưa cài (chỉ cần khi deploy Postgres thật, xem comment trong `requirements.txt`) · migrate dữ liệu từ `data/seeds/*.csv` sang DB thật (script `make seed`/`scripts/seed_db.py`) chưa viết — đây nên là ticket riêng, xem `BE-05`.

### `BE-10` Script nạp seed CSV vào DB thật ✅
**Owner:** R3 · **P1** · 4h · **Deps:** BE-01
`scripts/seed_db.py`: đọc toàn bộ `data/seeds/*.csv` (food_items, dishes, dish_ingredients, clinical_rules, drug_food_interactions, serving_sizes) rồi insert vào DB qua `src/db/models.py`, dùng `session.merge()` hoặc upsert theo khoá chính để chạy lại nhiều lần không tạo trùng.
**AC:** Chạy trên DB SQLite trắng → đủ 152 dòng `food_items`, đủ dòng hiện có của mọi bảng seed khác, không lỗi FK (dish_ingredients trỏ đúng food_id/dish_id đã tồn tại) · Chạy lại lần 2 không tăng gấp đôi số dòng (idempotent) · Có test dùng SQLite tạm, không đụng DB thật trong CI.
**2026-08-05 — đã làm:** `scripts/seed_db.py` + `make seed`. Idempotent qua `session.merge()` theo khoá chính (`FoodItem.id`, `Dish.dish_id`, `ClinicalRule.rule_id`, `DrugFoodInteraction.id`); riêng `serving_sizes` không có khoá tự nhiên trong CSV nên xoá-hết-rồi-nạp-lại. `dish_ingredients` tự bỏ qua (kèm log) dòng trỏ tới `food_id` chưa có số liệu thay vì crash FK. **Không** seed `gi_values.csv`/`purine_values.csv`/`usda_values.csv` — đây là bảng phụ trợ đã merge vào `food_items.csv`, không phải bảng DB độc lập. `tests/test_seed_db.py` (4 test: nạp đúng số liệu thật, không lỗi FK, idempotent chạy 2 lần, bỏ qua dish_ingredient thiếu food_item) — chạy trên SQLite in-memory, không đụng DB thật. Verify thật trên SQLite trắng: 125 food_items / 3 dishes / 11 dish_ingredients / 21 clinical_rules / 30 drug_food_interactions / 5 serving_sizes, chạy lại lần 2 số dòng không đổi.

### `BE-02` Auth JWT + RBAC
**Owner:** R3 · **P0** · 8h · **Deps:** BE-01
Đăng ký/đăng nhập, argon2id, access + refresh token, dependency `require_role()`.
**AC:** Bệnh nhân gọi `/reviews/pending` → 403 · Token hết hạn → 401 · Mật khẩu không bao giờ xuất hiện trong log.

### `BE-03` API hồ sơ bệnh nhân
**Owner:** R3 · **P1** · 6h · **Deps:** BE-02
CRUD hồ sơ: nhân trắc, bệnh lý (ICD-10 + giai đoạn), chỉ số xét nghiệm, thuốc, dị ứng, sở thích, vùng miền.
**AC:** Validation chặt (cân nặng 20–300kg, tuổi 1–120) · eGFR ngoài khoảng hợp lệ → 422 · Có integration test.

### `BE-04` API tính định mức
**Owner:** R3 · **P1** · 3h · **Deps:** CLN-03, BE-03
`POST /api/v1/targets/compute` — bọc clinical engine, **không gọi LLM**, trả nhanh (<200ms).
**AC:** Response có `targets` + `applied_rule_ids` + `guideline_refs` · Hiển thị được trên UI dưới dạng "vì sao ra con số này".

### `BE-05` Seed dữ liệu demo
**Owner:** R3 · **P1** · 4h · **Deps:** BE-01, DAT-02
Script tạo: 2 chuyên gia, 6 bệnh nhân mô phỏng (mỗi bệnh lý 1–2 người), thực phẩm, món ăn, rules, tương tác thuốc.
**AC:** `make seed` chạy 1 lệnh dựng đủ dữ liệu demo · README ghi rõ tài khoản demo · **Ghi rõ "dữ liệu hoàn toàn mô phỏng"**.

### `BE-06` API sinh thực đơn
**Owner:** R3 · **P1** · 8h · **Deps:** AGT-06, BE-04
`POST /api/v1/meal-plans` chạy graph bất đồng bộ, trả 202 + `plan_id`, đặt `status=pending_review`.
**AC:** Bệnh nhân gọi `GET /meal-plans` **không thấy** plan chưa duyệt · Có timeout và xử lý lỗi LLM · Không để request treo > 60s.

### `BE-07` API nhật ký ăn uống + tổng hợp
**Owner:** R3 · **P1** · 8h · **Deps:** DAT-02, CLN-04
Ghi món đã ăn (chọn từ DB hoặc gõ tự do → OOV), tổng hợp theo ngày/tuần, so với định mức, sinh cảnh báo vượt ngưỡng.
**AC:** Tổng hợp ngày trả kcal/Na/đường/protein + % so định mức · Vượt ngưỡng Na → cảnh báo kèm chỉ rõ món nào đóng góp nhiều nhất.

### `BE-08` Audit log
**Owner:** R3 · **P1** · 5h · **Deps:** BE-01
Ghi mọi hành động: sinh, sửa, duyệt, từ chối, xem hồ sơ bệnh nhân khác. Lưu `before`/`after`.
**AC:** Duyệt 1 thực đơn sinh đủ bản ghi có actor + timestamp + diff · Không có endpoint sửa/xoá audit · Có API `GET /audit` cho admin.

### `BE-09` Kiểm thử bảo mật & phân tách dữ liệu
**Owner:** R3 · **P0** · 5h · **Deps:** BE-02, BE-06
Test tự động cho mọi endpoint có dữ liệu bệnh nhân.
**AC:** Bệnh nhân A gọi tài nguyên của B → **404** · Không endpoint nào trả PHI khi thiếu token · Không có secret trong repo (thêm `gitleaks` vào CI).

---

## EPIC 5 — HITL (S4) — *R1 graph · R3 backend · R4 frontend*

### `HIT-01` Interrupt trong LangGraph
**Owner:** R1 · **P0** · 8h · **Deps:** AGT-06, BE-01
`interrupt()` trước khi phát hành, checkpointer Postgres, resume bằng `Command`.
**AC:** Graph dừng đúng chỗ, state persist qua restart server · Resume với `approve`/`edit`/`reject` chạy đúng nhánh.
**Fallback (nếu quá 2 ngày chưa xong):** dùng cột `status` thuần trong `meal_plans`, không dùng interrupt. Ghi quyết định vào DEVLOG.

### `HIT-02` API hàng chờ duyệt
**Owner:** R3 · **P0** · 6h · **Deps:** HIT-01
`GET /reviews/pending`, `POST /reviews/{id}/approve` (kèm edits), `POST /reviews/{id}/reject` (lý do bắt buộc).
**AC:** Chỉ role dietitian truy cập được · Approve kèm sửa gram → tính lại dinh dưỡng trước khi lưu · Reject không có lý do → 422.

### `HIT-03` Dashboard duyệt thực đơn
**Owner:** R4 · **P0** · 12h · **Deps:** HIT-02
Danh sách chờ (sắp theo mức độ cảnh báo), trang chi tiết: thực đơn, định mức, biểu đồ so sánh, cảnh báo, **nguồn từng món**, ô sửa gram trực tiếp, nút Duyệt/Từ chối.
**AC:** Duyệt 1 thực đơn ≤ 2 phút (đo thật) · Cảnh báo `high` không thể bỏ lỡ về mặt thị giác · Sửa gram cập nhật tổng dinh dưỡng ngay trên UI.

### `HIT-04` Thông báo & trạng thái cho bệnh nhân
**Owner:** R4 · **P1** · 5h · **Deps:** HIT-02
Bệnh nhân thấy trạng thái "Đang chờ chuyên gia duyệt" (không thấy nội dung), khi approved thì hiện thực đơn kèm tên người duyệt + thời điểm.
**AC:** Không có cách nào xem nội dung plan chưa duyệt từ UI **và** từ API · Thực đơn đã duyệt hiển thị "Đã duyệt bởi ... lúc ...".

### `HIT-05` Vòng phản hồi khi bị từ chối
**Owner:** R1 · **P2** · 5h · **Deps:** HIT-01
Lý do từ chối của chuyên gia được đưa vào `feedback` và agent sinh lại.
**AC:** Từ chối "quá nhiều tinh bột buổi tối" → bản sinh lại giảm carb bữa tối, có test · Lịch sử các phiên bản được lưu.

---

> ❓ **ĐỀ XUẤT (2026-08-06, Claude theo yêu cầu Hưng — CẦN ĐỘI DUYỆT TRƯỚC KHI COI LÀ TICKET CHÍNH THỨC, chưa gán sprint/giờ):** 3 ticket dưới đây xuất phát từ ý tưởng "chuyên gia tự xây/chấm thực đơn trực tiếp, lưu lại để cải tiến model sau này". Bối cảnh & lý do kỹ thuật ghi trong `DEVLOG.md` entry cùng ngày — đọc trước khi bàn.

### `HIT-06` API xây dựng thực đơn thủ công (chuyên gia tự chọn món) — ĐỀ XUẤT
**Owner:** R3 (API) · **P2?** · **Deps:** HIT-02, BE-06
Cho chuyên gia tạo 1 `MealPlan` từ tay (không qua AI), hoặc "tách nhánh" từ 1 bản AI đã sinh để sửa tự do thay vì chỉ sửa gram từng item như HIT-02 hiện tại.
- `POST /meal-plans/manual` — tạo plan trống, `origin=expert_authored`.
- `POST /meal-plans/{id}/fork` — copy toàn bộ item từ 1 plan AI đã có sang plan mới editable, `origin=expert_edited`, `source_plan_id` trỏ về bản gốc (cần thêm 2 cột này vào `MealPlan`).
- `POST /meal-plans/{id}/items`, `DELETE /meal-plans/{id}/items/{item_id}` — thêm/xoá món, mỗi lần gọi lại `compute_nutrition()`/`validate_menu()` trên server (RULE-1: chuyên gia chỉ chọn `food_id`+`grams`, không tự nhập số dinh dưỡng), trả về tổng dinh dưỡng + so với định mức NGAY để chuyên gia thấy trực tiếp trong lúc xây, không phải chờ duyệt xong mới biết.
**AC:** Không có route/field nào nhận số dinh dưỡng trực tiếp từ chuyên gia (test tự động kiểm, giống RULE-1 test hiện có cho `AGT-04`) · Plan xây thủ công đi qua đúng luồng duyệt HIT-02 như plan AI · Có test `origin`/`source_plan_id` gán đúng.

### `HIT-07` Chấm điểm có cấu trúc (structured scoring) — ĐỀ XUẤT
**Owner:** R3 (API) + R2 (thiết kế thang điểm) · **P2?** · **Deps:** HIT-02
Mở rộng `POST /reviews/{id}/approve` (và có thể cả reject) để nhận điểm theo nhiều chiều thay vì chỉ approve/sửa/từ chối nhị phân — VD `variety` (đa dạng món), `palatability` (hợp khẩu vị), `feasibility` (khả thi nấu ăn thực tế) mỗi chiều thang 1-5, cộng free text. Ngưỡng tuân thủ dinh dưỡng (Guideline Compliance) đã tự động có sẵn từ `violations[]`, KHÔNG cần chuyên gia chấm lại — chỉ chấm phần máy không tự đánh giá được.
**AC:** Bảng/cột lưu điểm truy vấn được riêng (không chôn trong `reviewer_notes` dạng text tự do) · Thang điểm cụ thể do R2 đề xuất, đội duyệt trước khi code (đừng tự bịa thang điểm).

### `EVL-07` Thu thập cặp (bản AI, bản chuyên gia sửa) để phân tích/cải tiến sau — ĐỀ XUẤT
**Owner:** R2 · **P3?** · **Deps:** HIT-06, HIT-07
Script export `scripts/export_expert_corrections.py`: với mọi `MealPlan` có `origin=expert_edited`, join sang bản AI gốc qua `source_plan_id`, tính diff (món thêm/bớt/đổi gram), gộp cùng hồ sơ bệnh nhân + định mức + điểm chấm (HIT-07) → `eval/datasets/expert_corrections.jsonl`.
**Quan trọng — phạm vi thực tế cho 6 tuần:** đây là bước THU THẬP dữ liệu, không phải tự xây pipeline RL/fine-tune (việc đó tốn nhiều tuần, ngoài phạm vi MVP). Dùng được ngay cho: (a) làm ví dụ few-shot bổ sung vào prompt Gemini, (b) phân tích lỗi phổ biến chuyên gia hay sửa → cân nhắc thêm thành `clinical_rules`/ràng buộc CP-SAT mới thay vì chờ model học, (c) tự nó là 1 phần dữ liệu hay cho báo cáo eval (EVL-05) — "chuyên gia sửa trung bình bao nhiêu %, sửa gì nhiều nhất". Đừng hứa "học tăng cường" trên pitch nếu chưa thực sự chạy — nói đúng những gì đã làm (thu thập dữ liệu có cấu trúc, sẵn sàng cho bước tiếp theo).
**AC:** 100% dữ liệu mô phỏng (đúng `CLAUDE.md` §3, không có bệnh nhân thật) · File output có schema ổn định, ghi rõ trong `eval/README.md` hoặc tương đương · Không tự ý claim đã "huấn luyện lại model" nếu chỉ mới thu thập dữ liệu.

---

## EPIC 6 — FRONTEND (S4–S5) — *Owner chính: R4*

### `FE-01` Khung app + Auth UI
**Owner:** R4 · **P0** · 8h · **Deps:** BE-02
Next.js App Router, layout theo role, đăng nhập/đăng xuất, lưu token an toàn, route guard.
**AC:** Sai role → redirect · Refresh trang không mất session · Responsive mobile.

### `FE-02` Form hồ sơ bệnh nhân
**Owner:** R4 · **P1** · 10h · **Deps:** BE-03
Nhiều bước: nhân trắc → bệnh lý & giai đoạn → xét nghiệm → thuốc → dị ứng → sở thích/vùng miền.
**AC:** Validation phía client khớp server · Lưu nháp giữa chừng · Chọn thuốc có gợi ý (autocomplete).

### `FE-03` Màn hình thực đơn
**Owner:** R4 · **P1** · 10h · **Deps:** BE-06
Thực đơn theo bữa, gram, tổng dinh dưỡng, thanh so sánh với định mức, **chip nguồn bấm được cho từng món**, cảnh báo, disclaimer.
**AC:** Bấm vào món hiện popup "Gạo tẻ · NIN · Bảng TPTP VN, tr.42" · Disclaimer luôn hiển thị · Món ước tính có nhãn riêng.

### `FE-04` Nhật ký ăn uống
**Owner:** R4 · **P1** · 8h · **Deps:** BE-07
Ghi món nhanh (tìm kiếm + gõ tự do), tổng hợp ngày, vòng tròn tiến độ, cảnh báo vượt ngưỡng.
**AC:** Ghi 1 bữa ≤ 20 giây · Vượt ngưỡng Na hiện cảnh báo đỏ tức thì · Xem lại được 7 ngày gần nhất.

### `FE-05` Giao diện chat có guardrail
**Owner:** R4 · **P1** · 6h · **Deps:** AGT-07
Chat với agent, hiển thị citation, hiển thị rõ khi guardrail kích hoạt.
**AC:** Hỏi "tôi nên uống thuốc gì" → hiện câu trả lời chuẩn + nút "Gửi câu hỏi cho chuyên gia" · Citation bấm được.

### `FE-06` Dark mode + Accessibility + Empty states
**Owner:** R4 · **P2** · 5h · **Deps:** FE-01
**AC:** Dark mode toàn app · Tương phản đạt WCAG AA · Mọi màn hình có trạng thái loading/rỗng/lỗi · Không có màn hình trắng.

### `FE-07` Biểu đồ xu hướng
**Owner:** R4 · **P2** · 6h · **Deps:** BE-07
Recharts: kcal/Na/đường theo 7 và 30 ngày, đường ngưỡng.
**AC:** Vượt ngưỡng hiển thị vùng đỏ · Có tooltip · Bệnh nhân và chuyên gia đều xem được.

### `FE-08` Danh sách đi chợ
**Owner:** R4 · **P3** · 5h · **Deps:** ADV-03
**AC:** Gộp nguyên liệu cả tuần, quy về đơn vị chợ (mớ/bó/lạng) · Tick được từng món · In/copy được.

---

## EPIC 7 — TÍNH NĂNG NÂNG CAO (S5) — *Owner chính: R1 + R2*

### `ADV-01` Phân rã mâm cơm gia đình
**Owner:** R1 + R2 · **P2** · 12h · **Deps:** DAT-04, CLN-04
Nhập mô tả mâm cơm bằng text ("thịt kho tàu, canh rau ngót, đậu phụ luộc, 4 người ăn") → LLM nhận diện món → SQL tra dinh dưỡng → thuật toán tối ưu chọn khẩu phần cho bệnh nhân + hướng dẫn cách gắp.
**AC:** Ví dụ trong đề án (ĐTĐ + CKD G3) cho kết quả hợp lý, nằm trong định mức · Đầu ra là **hướng dẫn hành vi** ("gạt bỏ nước kho", "chỉ ăn cái không ăn nước canh"), không chỉ là con số · Có ≥5 case test.
> Đây là tính năng khác biệt nhất của dự án. Ưu tiên hơn shopping list.

### `ADV-02` Gợi ý thay thế theo vùng miền
**Owner:** R2 · **P3** · 6h · **Deps:** DAT-04
Bảng thay thế: mắm nêm → mắm pha loãng/chanh ớt; nước cốt dừa → sữa hạt; đường → chất tạo ngọt GI thấp.
**AC:** Bệnh nhân miền Trung nhận gợi ý giảm mặn phù hợp khẩu vị · Mỗi gợi ý ghi rõ tiết kiệm được bao nhiêu mg Na / g đường.

### `ADV-03` Thực đơn 7 ngày
**Owner:** R1 · **P2** · 8h · **Deps:** AGT-06
Sinh cả tuần, tránh lặp món quá 2 lần, cân bằng dinh dưỡng theo tuần chứ không chỉ theo ngày.
**AC:** Không món nào lặp > 2 lần/tuần · Mỗi ngày vẫn pass validator riêng · Thời gian sinh < 90 giây.

### `ADV-04` Cân bằng lại theo thời gian thực
**Owner:** R1 · **P2** · 6h · **Deps:** BE-07, ADV-03
Bữa sáng vượt Na → tự điều chỉnh giảm Na bữa trưa/tối trong ngân sách còn lại.
**AC:** Bệnh nhân log bát phở (3,5g muối) → gợi ý bữa tối được điều chỉnh, tổng ngày vẫn trong ngưỡng · Nếu không thể cân bằng → nói thật ("hôm nay đã vượt, ngày mai cần bù").

### `ADV-05` Memory sở thích
**Owner:** R1 · **P3** · 5h · **Deps:** BE-03
Ghi nhớ món không thích, nguyên liệu sẵn có, dị ứng phát hiện thêm.
**AC:** Từ chối món 2 lần → không đề xuất lại trong 30 ngày · Bệnh nhân xem và xoá được ghi nhớ (quyền riêng tư).

### `ADV-06` Export PDF thực đơn
**Owner:** R4 · **P3** · 4h · **Deps:** FE-03
**AC:** PDF có logo, thực đơn, dinh dưỡng, nguồn, **disclaimer**, tên người duyệt · In A4 không vỡ layout.

---

## EPIC 8 — EVALUATION & QA (S5–S6) — *Owner chính: R2 (dữ liệu & báo cáo) + R1 (runner)*

### `EVL-01` Bộ 60 case đánh giá
**Owner:** R2 · **P1** · 10h · **Deps:** CLN-03
`eval/datasets/cases_60.jsonl` theo phân bổ trong `PLAN.md` §7.1, mỗi case có `expected_targets` tính tay.
**AC:** 60 hồ sơ synthetic, đủ 6 nhóm (trong đó 6 adversarial profiles) · `eval/datasets/safety_prompts_26.jsonl` có 26 prompt với `expected_behavior` rõ ràng · Expected targets được tính độc lập với system under test · Được R1 review chéo.

### `EVL-02` Runner đánh giá tự động
**Owner:** R1 · **P1** · 8h · **Deps:** EVL-01, AGT-06
`make eval` chạy toàn bộ case, xuất JSON + markdown, tính 5 nhóm metric.
**AC:** Chạy 1 lệnh · Kết quả reproducible (seed cố định) · Xuất bảng dán thẳng vào báo cáo.

### `EVL-03` Test groundedness trong CI
**Owner:** R3 · **P0** · 4h · **Deps:** AGT-05
Test chặn: mọi giá trị dinh dưỡng phải có `source` và `source_ref`; module `compute_nutrition` không được import LLM client; DB không dòng nào `source IS NULL` hoặc `source_ref IS NULL`.
**AC:** CI **đỏ** nếu ai đó vô tình để LLM sinh số · Chạy trên mọi PR.
> Đây là ticket biến nguyên tắc thiết kế thành ràng buộc kỹ thuật thực sự.

### `EVL-04` RAGAS cho phần giải thích
**Owner:** R2 · **P2** · 6h · **Deps:** AGT-03, DAT-06
Faithfulness + Answer Relevancy trên 30 câu hỏi guideline.
**AC:** Cả 2 chỉ số ≥ 0,8 hoặc có phân tích lý do chưa đạt · Kết quả vào báo cáo.

### `EVL-05` Báo cáo đánh giá (Deliverable #10)
**Owner:** R2 · **P1** · 6h · **Deps:** EVL-02, EVL-04
`eval/results/report.md`: phương pháp, bảng metric, biểu đồ, **3 case thất bại + phân tích nguyên nhân**, mục "hạn chế đã biết".
**AC:** Có đủ 5 nhóm metric · Phần hạn chế trung thực, không tô hồng · Có biểu đồ.

### `EVL-06` Chuyên gia dinh dưỡng review 20 thực đơn
**Owner:** R2 · **P2** · 6h · **Deps:** EVL-02
Mời 1 chuyên gia/bác sĩ/giảng viên chấm 20 thực đơn: approve / sửa nhẹ / sửa nhiều / từ chối + nhận xét.
**AC:** Có bảng kết quả + reviewer ID/vai trò ẩn danh; danh tính và bằng chứng đồng ý được đội giữ ngoài repo · Tính được chỉ số Expert Agreement · Chỉ đưa thông tin nhận diện lên slide khi chuyên gia đồng ý rõ ràng.
> Deliverable này gần như không đội nào có. Chi phí: 1 buổi cà phê. Giá trị: rất lớn.

---

## EPIC 9 — DELIVERABLES (S6) — *Owner chính: R4 (nội dung) + R1 (theo dõi)*

### `DEL-01` Hoàn thiện README
**Owner:** R4 · **P0** · 4h
**AC:** Vấn đề → giải pháp → screenshot/GIF → tech stack → cài đặt → cấu trúc → tài khoản demo → thành viên & vai trò → Live URL → **disclaimer y tế**.

### `DEL-02` Architecture Diagram cuối
**Owner:** R1 · **P0** · 2h
**AC:** `docs/architecture_diagram.md` với Mermaid render được trên GitHub · Khớp code thực tế (không phải kiến trúc mơ ước).

### `DEL-03` Video demo 4 phút
**Owner:** R4 · **P1** · 6h
Kịch bản: vấn đề (30s) → hồ sơ bệnh nhân (30s) → agent sinh thực đơn (45s) → **cảnh báo tương tác thuốc kích hoạt** (30s) → chuyên gia duyệt và sửa (45s) → bệnh nhân nhận + log bữa ăn (45s) → kiến trúc chống bịa số (30s).
**AC:** ≤ 5 phút · Có phụ đề · Upload YouTube unlisted · Link vào README.

### `DEL-04` Pitch deck 10 slide
**Owner:** R4 + cả đội · **P1** · 8h
Theo cấu trúc chương 9 template. Slide 6 phải là "Cách chúng tôi chống bịa số"; thêm 1 slide "Những gì hệ thống KHÔNG làm".
**AC:** Font ≥ 24pt · Mỗi slide 1 ý · Mọi số liệu có nguồn · Tổng duyệt ≥ 3 lần.

### `DEL-05` Hoàn tất DEVLOG + Worklog
**Owner:** R1 · **P0** · 2h
**AC:** DEVLOG có entry của mọi tuần, mọi người · `git log --oneline > docs/worklog.md` · Không có tuần nào trống.

### `DEL-06` Kiểm tra cuối trước nộp
**Owner:** R3 · **P0** · 4h
Chạy checklist `chapter-09` của template.
**AC:** 10/10 deliverable · Live URL test trên incognito + máy khác + mạng khác · `pytest` xanh · Docker build được · Không secret trong repo · Không `except:` trần · CI xanh.

---

## Phụ lục A — Ma trận phụ thuộc quan trọng

```mermaid
graph LR
    DAT01[DAT-01 Chốt nguồn] --> DAT02[DAT-02 150 thực phẩm]
    DAT02 --> DAT04[DAT-04 80 món]
    DAT02 --> CLN03[CLN-03 Định mức]
    CLN02[CLN-02 Rules] --> CLN03 --> CLN04[CLN-04 Validator]
    CLN04 --> AGT06[AGT-06 Validate loop]
    AGT04[AGT-04 Generate] --> AGT05[AGT-05 Compute] --> AGT06
    AGT06 --> HIT01[HIT-01 Interrupt] --> HIT02[HIT-02 API duyệt] --> HIT03[HIT-03 Dashboard]
    HIT03 --> DEL03[DEL-03 Video]
    AGT06 --> EVL02[EVL-02 Eval runner] --> EVL05[EVL-05 Báo cáo]

    style DAT01 fill:#ffcdd2
    style HIT03 fill:#c8e6c9
    style EVL05 fill:#c8e6c9
```

**Đường găng:** `DAT-01 → DAT-02 → CLN-03 → CLN-04 → AGT-06 → HIT-01 → HIT-03`.
Trễ bất kỳ ticket nào trên đường này là trễ cả dự án. Ưu tiên tuyệt đối.

## Phụ lục B — Phân bổ giờ theo người (đội 4)

| Vai trò | Giờ ước tính | Giờ/tuần (6 tuần) | Nặng nhất ở |
|---|---|---|---|
| R1 Tech Lead / Agent + PM | ~118h | ~20h | S3 (agent + guardrails) |
| R2 Clinical & Data + Eval | ~130h | ~22h | S1–S2 (nhập dữ liệu) |
| R3 Backend + DevOps | ~98h | ~16h | S2 (schema + auth) |
| R4 Frontend + Deliverables | ~102h | ~17h | S4 (HITL dashboard) |

### Ba cảnh báo về tải

1. **R2 quá tải tuần 1–2.** Ticket `DAT-02` (150 thực phẩm) bắt buộc chia cho **cả 4 người**, mỗi người ~38 dòng. Để R2 làm một mình là vỡ đường găng ngay tuần đầu.
2. **R1 gánh cả PM.** Dành đúng 2 giờ/tuần cho việc theo dõi, phần còn lại vẫn phải code. Nếu thấy PM ngốn quá 4 giờ/tuần thì đang họp quá nhiều.
3. **R3 rảnh nhất từ tuần 5** (DevOps đã xong từ tuần 1) → chuyển sang hỗ trợ `ADV-01` (mâm cơm gia đình) và `EVL-02` (eval runner).

### Nếu có người thứ 5 tham gia giữa chừng

Ưu tiên tách theo thứ tự: (1) DevOps/QA tách khỏi R3 → nhận `EVL-*` và `OPS`; (2) tách R2 thành clinical rules và data ETL. Bản phân vai 5 người còn lưu ở `TEAM_5p_backup.md`.
