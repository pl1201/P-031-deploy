# WORKLOG — Nhật ký công việc

> ⚙️ File này được sinh tự động từ `DEVLOG.md` bằng `scripts/sync_devlog.py`.
> Đừng sửa trực tiếp — hãy sửa `DEVLOG.md` rồi chạy lại script.

> Cập nhật lần cuối: 06/08/2026 12:40 · 92 commit

---

## 1. Đóng góp theo thành viên

| Thành viên | Số commit |
|---|---|
| Kim Mạnh Hưng | 119 |
| NocNam | 8 |
| Đinh Lê Quỳnh Phương | 8 |
| pl1201 | 7 |
| Phùng Linh | 3 |
| phoenix-mentor[bot] | 1 |
| pluvia21 | 1 |

---

## 2. Nhật ký công việc hằng ngày

<!-- Entry mới thêm vào CUỐI mục này, theo thứ tự thời gian -->

### [2026-08-05] · R2 (Claude) · Nghiên cứu bổ sung nguồn dữ liệu từ tài liệu tổng quan
- **Làm:** Đối chiếu `data/Dữ liệu dinh dưỡng Việt Nam.md` (báo cáo tổng quan, 57 trích dẫn) với trạng thái thật của repo — xác nhận cả 8 nguồn đề xuất (Open Food Facts, uFiSh1.0, PhyFoodComp1.0, eBASIS, ASEANFOODS, WikiFCD/FoodOn, QĐ 5948/QĐ-BYT, Dược thư QGVN) chưa được dùng ở bất kỳ đâu trong repo. Tự xác minh từng nguồn qua WebSearch/WebFetch (không chép nguyên claim từ tài liệu)
- **Kết quả:** 2 nguồn xác nhận dùng được ngay (Open Food Facts — free API/ODbL; Dược thư QGVN 2022 — nguồn `source_ref` cho DAT-05), 1 nguồn cần thêm bước xác minh (uFiSh1.0 — link FAO không tải được lúc kiểm tra), 4 nguồn loại có lý do (PhyFoodComp ngoài scope lâm sàng, eBASIS license không rõ, ASEANFOODS trùng lặp VFCT 2017 đã đối chiếu chéo sẵn, WikiFCD/FoodOn over-engineering cho MVP)
- **Phát hiện quan trọng:** QĐ 5948/QĐ-BYT (2021, 633+68 cặp) mọi mô tả tìm được đều chỉ nói đây là danh mục tương tác **thuốc-thuốc**, KHÔNG có xác nhận nó phủ cặp thuốc-thực phẩm như tài liệu tổng quan ngụ ý — đã ghi rõ trong `docs/TICKETS.md` DAT-05 để R2 không suy đoán nhầm khi làm ticket
- **Cập nhật:** `data/README.md` (mục mới "Nghiên cứu bổ sung nguồn dữ liệu"), `docs/TICKETS.md` (DAT-01, DAT-05 cập nhật; thêm `DAT-11` cho Open Food Facts)
- **Tiếp theo:** R2 tự thử tải link uFiSh1.0 trực tiếp để chốt nốt; khi làm DAT-05 thật, tra Dược thư QGVN cho từng cặp thay vì để `source_ref` trống

### [2026-07-26] · Cả đội · Dựng khung code + tổ chức lại cho đội 4 người
- **Làm:** Phân vai lại 4 người (R5 chia cho R1/R2/R3/R4); dựng khung clinical engine + LangGraph; seed clinical_rules (18) + drug_food (30) + template 152 thực phẩm; pitch deck outline
- **Kết quả:** 43 test xanh, graph compile và xuất được mermaid, `validate_data.py` bắt đúng 4/4 lỗi cài sẵn
- **Phát hiện:** test bắt được xung đột ADA vs KDIGO ở ca ĐTĐ+CKD → đã xử lý bằng rule precedence (DEC-007), đưa vào slide 9
- **Vướng:** vẫn chưa chốt được nguồn Bảng thành phần thực phẩm VN (DAT-01) — rủi ro RSK-01 còn nguyên
- **Tiếp theo:** SET-01→06 (R3), DAT-00 + DAT-01 (R2), nhập 152 dòng thực phẩm chia 4 người

### [2026-08-02] · R2 Clinical & Data · DAT-02 — gỡ đường găng: fetcher NIN + bản nháp food_items
- **Làm:** Tìm ra **API công khai Viện Dinh dưỡng** (`/api/fe/foodNatunal/getPageFoodData`, 853 món, đủ chất trừ purine). Viết `scripts/fetch_nin_foods.py` + `scripts/build_food_items_from_nin.py` (khớp token-subset + neo đầu). Sinh `data/seeds/food_items.nin_draft.csv`: **107/152 dòng có dữ liệu NIN thật** (kcal/protein/carb/fat/xơ/đường/Na/K/P), mỗi dòng có `match_confidence` + `nin_name` để R2 soát
- **Schema:** `purine_mg` → **optional** (None-aware như sugar), vì NIN/USDA không có purine và chỉ gout cần. Validator có guard `incomplete_data` cho gout
- **Kết quả:** 70 test xanh, ruff + format sạch, validate_data sạch. Bản nháp bắt được cả lỗi khớp (VD 'Đường trắng' từng khớp nhầm sữa có đường → đã neo đầu để loại)
- **Promote:** đã sinh `food_items.csv` sản xuất — **59 dòng hoàn chỉnh** (đủ kcal/đạm/carb/béo/xơ/Na/K/P + GI merge), validate sạch. Chỉ nhận dòng NIN đủ khoáng chất; NIN thiếu Na/K/P thì để trống cho R2. Bỏ sugar khi NIN báo sugar>carb (mâu thuẫn dữ liệu, không bịa)
- **Còn 93 dòng trống:** món nấu chín (cơm/xôi/cháo — cần ước tính), NIN thiếu khoáng, và món chưa khớp tên. R2/USDA bổ sung
- **Tiếp theo:** ✅ đã probe API *món ăn* NIN (DAT-04, xem dưới); còn purine từ bảng Nhật; ước tính món nấu chín

### [2026-08-03] · R2 Clinical & Data · Khẩu phần chuẩn + PHÁT HIỆN dữ liệu món ăn NIN không đáng tin
- **Làm:** Tìm khẩu phần chuẩn (VN/Mỹ) → `data/seeds/serving_sizes.csv` (phở/bún 1 bát ~500g, bát cơm ~150g…)
- **🔴 Phát hiện quan trọng:** dữ liệu API *món ăn* NIN **KHÔNG dùng được cho ngưỡng muối lâm sàng**. Cùng "Phở bò": kcal dao động **276–826/100g** (vô lý — bát ăn thực ~70 kcal/100g), muối **0,01–6,7 g/100g**. Nhân với bất kỳ khối lượng bát nào cũng ra muối phi lý (0,8–33 g/bát)
- **Quyết định (DEC-013):** **KHÔNG seed dishes.csv từ số per-món của NIN.** Quay lại kế hoạch gốc DAT-04: LLM phân rã món → nguyên liệu → tính bằng SQL từ `food_items.csv` (nước mắm Na=7720 đáng tin). Test hồi quy muối tính từ nguyên liệu, không tin số món NIN
- **Tiếp theo:** DAT-04 theo hướng phân rã nguyên liệu; wiring agent cần Gemini key

### [2026-08-03] · R1 Agent · Nối GeminiMenuGenerator vào graph — luồng 8-node chạy đầu-cuối ✅
- **Làm:** `src/agents/assembly.py` — ráp cổng cụ thể vào `build_graph`: `load_food_repository` (seed), `GeminiMenuGenerator`, `InMemoryProfileRepository`, `SimpleFallbackProvider`. Hàm `build_nutricare_graph()`
- **Kết quả:** **Chạy thật qua graph với Gemini** — status=`pending_review` (happy path): Gemini chọn 16 món → Python tính 1926 kcal/Na 608mg (~1,54g muối) → 1 vi phạm mềm → tới bước duyệt HITL. `tests/test_graph_e2e.py` (generator giả, CI không cần key) chứng minh 8 node chạy thông. 78 test xanh
- **Ghi chú:** LangSmith báo 403 (key tracing trong .env không hợp lệ) — vô hại, graph vẫn chạy. Sẵn sàng quay video demo
- **Tiếp theo:** merge PR lớn vào develop

### [2026-08-05] · R1 Agent · AGT-09 — CPSATMenuOptimizer (OR-Tools CP-SAT thay vòng lặp sinh-rồi-thử của LLM)
- **Làm:** `src/agents/optimizer.py` — implement thẳng `Protocol MenuGenerator` bằng OR-Tools CP-SAT, không gọi LLM (`LLM: NO`, R20.1). Model: biến IntVar gram (bước 25g) + BoolVar chọn/không-chọn cho mỗi món trong `candidates`, ràng buộc tuyến tính lấy động từ mọi nutrient có ngưỡng trong `ClinicalTargets.targets` (kcal/protein/carb/fat/xơ/Na/K/P/purine/đường), chia định mức cả ngày theo tỉ lệ 4 bữa (sáng 25% / trưa 35% / tối 30% / phụ 10%), tối ưu mục tiêu đưa kcal về giữa khoảng cho phép thay vì chỉ chạm biên
- **Vì sao:** vòng lặp hiện tại (`generate_menu` → `validate` → `build_feedback` → retry ≤3, AGT-06) tốn tới 3 lượt gọi LLM mà vẫn có thể fallback nếu LLM không đoán trúng. CP-SAT giải trực tiếp — khả thi thì ra kết quả ngay lần đầu, vô nghiệm thì báo ngay (trả `MenuDraft` rỗng, route hiện có tự chuyển fallback, không cần route mới)
- **POC trước khi code thật:** chạy thử trên `food_items.csv` thật (`scripts/poc_cpsat_menu.py`, không commit — chỉ để nghiên cứu), phát hiện lần đầu solver trả UNKNOWN dù bài toán khả thi vì chi phí nạp thư viện native OR-Tools trong sandbox tốn ~8s cố định (đo `deterministic_time` thực chỉ ~0.003s) — phải nới trần thời gian solve lên 20-30s để không bị cắt giữa chừng
- **Hạn chế đã biết (ghi trong docstring module):** chia 4 bữa theo tỉ lệ cố định thay vì tối ưu đồng thời 1 model lớn (đơn giản hơn, chưa tối ưu toàn cục); `FoodItem` chưa có `category` nên chưa ép được ràng buộc kiểu "phải có món nhóm rau" — cần thêm cột đó vào model trước (việc khác)
- **Kết quả:** 3 test mới (`tests/test_cpsat_optimizer.py`) — khả thi trên dữ liệu thật, rỗng khi không có ứng viên, rỗng khi vô nghiệm. 81 test xanh, ruff+format+mypy sạch. Thêm `ortools>=9.11.0` vào `requirements.txt`
- **Tiếp theo:** nối `CPSATMenuOptimizer` vào `build_nutricare_graph()` như một lựa chọn generator (song song `GeminiMenuGenerator`, chọn theo cấu hình) — chưa làm trong ticket này để giữ PR gọn

### [2026-08-05] · R1 Agent · AGT-10 — Nối CP-SAT vào graph + 2 phát hiện đo được về solver
- **Làm:** (a) Gộp CP-SAT thành **một model cả ngày** (biến theo cặp bữa×món, ràng buộc dinh dưỡng trên tổng ngày, chỉ số món còn theo bữa); (b) `src/agents/hybrid.py` — `HybridMenuGenerator`: lượt đầu CP-SAT, chuyển Gemini khi vô nghiệm hoặc khi đã có feedback; (c) `settings.menu_generator` (`hybrid`/`cpsat`/`gemini`, mặc định `hybrid`) cho `assembly.py` chọn generator
- **Vì sao bỏ chia tỉ lệ 25/35/30/10:** cách cũ bắt MỖI bữa tự thoả `tỉ_lệ × min` cho MỌI chất, nên bữa phụ (10%) phải tự gánh 10% chất xơ + 10% đạm → dễ vô nghiệm; slot đó trả rỗng làm tổng ngày hụt → `validate` báo vi phạm ngưỡng tối thiểu. Đây là lỗi hệ thống chứ không phải ca hiếm
- **🔴 Phát hiện 1 — hàm mục tiêu làm solver không tìm nổi lời giải:** bản có `Minimize(|kcal − điểm giữa|)` chạy **105 s vẫn trả UNKNOWN** (không tìm được lời giải khả thi NÀO), trong khi bản khả thi thuần xong **0,1 s OPTIMAL** — chênh ~1000 lần. Hàm mục tiêu lái tìm kiếm sang nhánh xấu. Thay bằng **2 pha khả thi**: pha 1 siết năng lượng vào dải ±3% quanh điểm giữa, vô nghiệm thì pha 2 dùng khoảng gốc. Đạt cùng ý định lâm sàng ("vừa đủ, không chạm biên") mà nhanh và tất định
- **🔴 Phát hiện 2 — sai số làm tròn có thể phá ngưỡng MAX:** CP-SAT chỉ nhận hệ số nguyên, bản đầu làm tròn giá trị/100 g về số nguyên (`protein_g=9.43` → 9, sai −4,6%). Sai số cộng dồn qua ~20 món có thể đẩy tổng **vượt ngưỡng MAX thật** dù solver tin là còn trong ngưỡng. Sửa: giữ 1 chữ số thập phân (`VALUE_SCALE=10`). Đo thực tế cho thấy biên rất sát — ca ĐTĐ2+THA ra `sugar=49,3/49,7` và `fat=65,1/66,3`, đúng chỗ sai số cũ sẽ phá
- **Kết quả:** graph chạy hết với CP-SAT thật **không cần API key** — `status=pending_review`, `retry_count=1` (xong ngay lượt đầu, không cần vòng lặp retry), **không rơi fallback**, 0,1 s. **Không đổi `graph.py`, không thêm route** — nhờ giữ đúng `Protocol MenuGenerator`
- **Tiếp theo:** audit độc lập trước khi merge (xem entry kế)

### [2026-08-05] · R1 Agent · AGT-10 hardening — audit ĐỘC LẬP bắt bug làm tròn mà 89 test tự viết bỏ lọt
- **Bối cảnh:** trước khi merge, chạy **2 agent audit độc lập** (một soi tính đúng đắn CP-SAT, một soi độ đủ test) — cố ý bắt đầu lạnh, không mớm kết luận "code đúng", đúng nguyên tắc tách bạch người viết ≠ người kiểm.
- **🔴 Bug audit tìm ra (test tôi tự viết KHÔNG bắt được):** `VALUE_SCALE=10` làm tròn `round()` đối xứng, cộng với giải khả thi thuần (không hàm mục tiêu) đặt tổng ĐÚNG SÁT ngưỡng → sai số làm tròn cộng dồn đẩy tổng **thật** (do `compute_nutrition` tính) ra ngoài ngưỡng. Auditor quét 126 hồ sơ → **11 thực đơn** bị `validate_menu` gắn cờ, cả min lẫn max, gồm **hard rule** (chất xơ, carb, chất béo, đường). Test cũ chỉ dùng 1 hồ sơ ĐTĐ2 tình cờ an toàn nên pass giả.
- **Vì sao "2 phát hiện" của entry trên vẫn chưa đủ:** phát hiện 2 tôi tự nghĩ đã "sửa" bằng `VALUE_SCALE=10`, nhưng đó chỉ **giảm** sai số chứ không **loại**. Bản chất: round() đối xứng không có bảo đảm hướng.
- **Cách sửa (có chứng minh toán học, không phải nới magic number):** làm tròn **CÓ HƯỚNG** — ngưỡng MAX dùng hệ số `ceil` + ngưỡng `floor` (mô hình ước lượng tổng CAO hơn thật ⇒ thật ≤ ngưỡng); ngưỡng MIN dùng hệ số `floor` + ngưỡng `ceil` (thật ≥ ngưỡng). Đảm bảo đúng **bất kể** VALUE_SCALE. Nutrient có cả 2 phía (carb, kcal) dùng 2 biểu thức riêng.
- **Bug thứ 2 lộ ra khi sửa:** `compute_nutrition` **làm tròn tổng về 2 chữ số** rồi `validate_menu` mới so — nên hợp đồng thật là giá trị ĐÃ tròn. Thêm `SUMMARY_ROUND_MARGIN=0,005` siết ngưỡng để bù. Sau đó quét **168 hồ sơ** (thêm gout): **0 vi phạm, 0 blocking** (24 ca vô nghiệm là gout thật — purine lọc còn quá ít món, hybrid chuyển LLM).
- **Lỗ hổng test audit chỉ ra (đã đóng):** thêm test hồi quy 6 hồ sơ **đã kiểm chứng fail dưới bản cũ** (fixed→pass, buggy→4/6 fail, chứng minh bằng cách áp lại bản buggy); test `_eligible_candidates` loại món thiếu purine (RULE-2); test 2 pha (monkeypatch `_try_solve`); test `_generator_from_settings` cả 3 nhánh config; mạnh hóa assert lỏng (`test_graph_chay_het_8_node` → pin `pending_review`+`used_fallback`+`retry=3`; đủ 4 bữa; memoize lazy-init LLM); thêm e2e "CP-SAT vô nghiệm → fallback qua graph thật".
- **Bài học:** agent viết code/test không được tự chấm bài mình. 2 audit độc lập bắt 1 bug đúng (hard rule, ảnh hưởng bệnh nhân thật) + ~10 lỗ hổng test mà pipeline "89 test xanh" hoàn toàn che.
- **Kết quả:** **102 test xanh**, ruff+format+mypy sạch (mypy còn 3 lỗi baseline: thiếu stub langgraph/pydantic_settings). Fix có test hồi quy khoá lại.
- **Tiếp theo:** eval runner (EVL-01/02) hoặc quay video demo — MVP giờ demo được không cần key

### [2026-08-03] · R2 Data · Lấp food_items từ USDA — 88 → 111 dòng
- **Làm:** Tra USDA FDC cho ~32 món NIN thiếu, soát tay bỏ khớp sai (cam→vỏ cam, sữa→phô mai, bí đao→dưa) → `data/seeds/usda_values.csv` **23 món sạch** (cá rô phi, đậu đen/đỏ, cà tím, su hào, mướp đắng, đậu bắp, cam/quýt/bưởi/nhãn, sữa tươi, dầu, mỡ, bơ, lạc, đường…). Build merge USDA làm fallback sau NIN
- **Kết quả:** food_items.csv **111/152 dòng** có số liệu thật (NIN+USDA+GI+purine+ước tính), validate sạch. Nới trần kcal→920 (mỡ/dầu ~902)
- **Ghi chú:** lạc rang USDA có muối (Na cao), nấm rơm USDA đóng hộp — đã note; R2 soát. Còn 41 dòng trống (món thuần Việt: tía tô/kinh giới/rau răm/chao/tương/mắm nêm…) cần nguồn khác

### [2026-08-03] · R2 Data · DAT-03 — tích hợp USDA FoodData Central + dò thêm API NIN
- **Làm:** `scripts/fetch_usda_foods.py` — client USDA FDC (`/fdc/v1/foods/search`, ưu tiên Foundation/SR Legacy). Config `usda_api_key`. Map nutrientId→cột schema (kcal/đạm/carb/béo/xơ/đường/Na/K/P). USDA KHÔNG có purine (đã có DB purine riêng)
- **Kết quả:** chạy thật OK với key R1 cấp — salmon/tofu trả đủ chất + `source_ref=USDA fdcId:xxx`. Dùng lấp món NIN thiếu; khớp tên cần curate (snakehead→bluefish sai) như NIN
- **Dò API NIN:** 2 trang còn lại (*nhu cầu*, *đánh giá tình trạng*) là SPA, endpoint dựng động trong JS → cần browser network inspect (đang tạm chặn). Giá trị thấp: ta đã tự tính BMR/TDEE/BMI. 2 API giá trị cao (thực phẩm + món ăn) đã tích hợp
- **Tiếp theo:** map query USDA cho các món NIN thiếu (giống OVERRIDES) để lấp nốt 64 dòng trống

### [2026-08-03] · R2 Clinical & Data · Gia vị mặn — lấp nốt trục chính bài toán muối
- **Làm:** MANUAL_FILL 5 gia vị mặn: mì chính (MSG, Na 12280 — hoá học, curated), bột canh (~33000, est), hạt nêm (~17000, est), mắm tôm (Na 4054 từ NIN 13011 + macro est), nước mắm giảm mặn (~4000, est)
- **Kết quả:** food_items.csv **88 dòng**, validate sạch. Nới trần na_mg→40000 cho muối tinh. Ước tính có ghi rõ "cần đối chiếu nhãn"
- **Ghi chú:** bột canh/hạt nêm là sản phẩm thương mại (proprietary) → ước tính; R2 nên xác nhận từ nhãn thực tế

### [2026-08-03] · R1 Agent · AGT-04 — MVP end-to-end với Gemini thật ✅
- **Làm:** `GeminiMenuGenerator` (src/services/llm.py) cài Protocol `MenuGenerator` bằng google-genai structured output — LLM CHỈ trả slot+food_id+grams (schema `_LLMSelection` cố ý không có trường dinh dưỡng, RULE-1). Config 5 GEMINI key + **xoay vòng khi 429**. Sửa llm.py cũ (đang import langchain_openai chưa cài)
- **Kết quả:** **Chạy thật thành công** — Gemini chọn 8 món → `compute_nutrition` tính 1874 kcal/Na 393mg → validator ra 2 vi phạm (kích hoạt retry loop). 76 test xanh (3 test mock mới), ruff sạch
- **Phát hiện:** `gemini-2.0-flash` free-tier limit=0 (429 cả 5 key); `gemini-1.5-flash` đã ngừng (404) → **default `gemini-2.5-flash`** (chạy được). Key rotation hoạt động đúng như thiết kế
- **Lưu ý:** `.env` (có key) nằm ở repo gốc, gitignore — app đọc từ thư mục chạy. CI/test không cần key (đã mock)
- **Tiếp theo:** nối vào graph (make_generate_menu đã sẵn cổng); khẩu phần chuẩn + gia vị mặn

### [2026-08-03] · R2 Clinical & Data · DAT-04 — phân rã món ăn + test hồi quy muối
- **Làm:** `dishes.csv` + `dish_ingredients.csv` (phở bò, bún đậu, canh rau muống) — món phân rã thành nguyên liệu (food_id+gram), dinh dưỡng tính bằng `compute_nutrition` (RULE-1, không lưu số của món). Loader `src/clinical/seeds.py`. Điền tay nguyên liệu nền (muối NaCl Na=38758, bún/phở gạo) qua MANUAL_FILL
- **Kết quả:** **phở bò = 3,58 g muối/bát** — KHỚP mốc nghiên cứu 3,3–4,0 g → xác nhận cả chuỗi (nước mắm NIN + muối USDA + công thức) đúng. Test hồi quy `tests/test_dishes.py`. 73 test xanh. food_items.csv nay 83 dòng
- **Nới trần:** na_mg 25000→40000 (muối tinh ~38758). Công thức là NHÁP, verified_by=pending — R2 rà
- **Tiếp theo:** wiring agent với 5 GEMINI key (item 2); thêm món nguy hiểm (bún riêu, bún bò Huế) khi đủ nguyên liệu

### [2026-08-03] · R2 Clinical & Data · Purine (gout) — điền từ USDA/ODS-NIH Purine DB R2.0
- **Làm:** R1 tải `data/PURINEDATABASEANDDATASOURCES2025.xlsx` (436 món, cột "Total of 4 Purines" mg/100g). Trích + map tay 19 món template (nội tạng/thịt/cá/tôm/cua/mực/ngao/nấm/đậu) → `data/seeds/purine_values.csv`
- **Provenance:** thêm cột `purine_source_ref` (nguồn RIÊNG, khác NIN — RULE-2); model FoodItem + validate_data ép mỗi trị purine phải dẫn nguồn USDA + mô tả món gốc
- **Kết quả:** gan lợn 289, cá thu 194, tôm 166.5, đậu phụ 31.1… merge vào food_items.csv. 70 test xanh, validate sạch (19 trị purine). Nấm hương ghi rõ trị TƯƠI 23.1 (khô cao gấp ~13 lần)
- **Tiếp theo:** dishes.csv cần khẩu phần chuẩn (đang tìm nghiên cứu VN/Mỹ)

### [2026-08-02] · R2 Clinical & Data · DAT-04 (probe) — API món ăn NIN
- **Làm:** Tìm ra API **`/api/fe/tool/getPageFoodData`** — **1250 món ăn Việt** kèm dinh dưỡng/100g: kcal, đạm, béo, carb, **Natri + tương đương muối (g)**, Kali, xơ, cholesterol. Viết `scripts/fetch_nin_dishes.py` (tái lập). KHÔNG có purine; `dish_components` (công thức) để trống
- **Kết quả:** có đủ nhóm món "nguy hiểm" natri của đề bài. VD **Bún riêu cua: Na 2176mg = 5,44g muối/bát** (vượt trần WHO 5g/ngày chỉ với 1 bát) — đúng thông điệp muối của dự án
- **Tiếp theo:** dựng `dishes.csv` (DAT-04) từ API, chọn ~80 món + test hồi quy muối (phở bò 3,3–4,0g); purine (DAT gout)
- **Thời gian:** ~2h

### [2026-08-02] · R2 Clinical & Data · DAT-08b — trích Atkinson Suppl. Table 1 (GI quả/staple)
- **Làm:** Đọc PDF `docs/TLTK/SupplementalTable1.pdf` (139 trang, 2091 món) bằng pypdf, trích GI per-food cho 17 món Việt còn thiếu (chuối/cam/quýt/táo/lê/xoài/đu đủ/dứa/dưa hấu/vải/ổi/nho/khoai lang/ngô/bánh mì/đậu xanh/giá đỗ)
- **Kết quả:** `gi_values.csv` từ 11 → **28 trị**, validate sạch. Mỗi trị dẫn số hiệu mục Suppl. Table 1
- **Trung thực:** để trống đậu đen/đậu đỏ/thanh long/sầu riêng/bơ vì không có mục sạch (chỉ có dạng chế biến/mixed) — không gán bừa (DEC-008)
- **Tiếp theo:** dò API Viện Dinh dưỡng (viendinhduong.vn) để lấp số liệu dinh dưỡng food_items (DAT-02, đường găng)
- **Thời gian:** ~1.5h

### [2026-08-01] · R2 Clinical & Data · CLN-08 — rule đường tự do WHO cho ĐTĐ2
- **Làm:** Thêm rule `T2DM-SUG-01` (đường tự do <10%E, WHO 2015) dùng `sugar_g`; bổ sung `sugar_g` vào `KCAL_PER_GRAM`; validator có nhãn "Đường" + cảnh báo `incomplete_data` khi thiếu số liệu đường
- **Kết quả:** 3 test mới (TestFreeSugarRule) pass, tổng 68 test xanh, validator 21 rule sạch, ruff clean
- **Quyết định:** đặt `severity=soft` dù WHO là khuyến nghị mạnh — vì `sugar_is_complete` thường False (dữ liệu đường thiếu), chặn cứng trên tổng thiếu hụt sẽ sai. Scope T2DM để không phá test HTN hiện có
- **Tiếp theo:** khi phủ đủ `sugar_g` thì broaden rule sang BASE; lấy Supplemental Table 1 cho GI quả (DAT-08)
- **Thời gian:** ~1.5h

### [2026-08-01] · R2 Clinical & Data · DAT-08 — bổ sung GI staple từ Atkinson 2021
- **Làm:** Đọc [Atkinson 2021, AJCN 114:1625-1632](https://academic.oup.com/ajcn/article/114/5/1625/6320814) để transcribe GI cho staple quốc tế
- **Kết quả:** Thêm 4 trị per-food nêu rõ trong bài (gạo lứt 65, khoai tây luộc 73, yến mạch 55, cà chua 22) → gi_values.csv nay 11 dòng, validate sạch
- **Phát hiện:** Bài 8 trang **chỉ có trung bình theo nhóm**, per-food (quả/đậu/khoai lang/ngô/bánh mì) nằm trong Supplemental Table 1 / CSDL glycemicindex.com — chưa lấy được ở đây. KHÔNG gán trung bình nhóm cho một loại quả cụ thể (biến thiên lớn). Giữ nguyên tắc "research chuẩn nguồn" (DEC-008)
- **Tiếp theo:** lấy Supplemental Table 1 cho GI quả/đậu; CLN — rule đường tự do WHO dùng sugar_g
- **Thời gian:** ~1h

### [2026-08-01] · R2 Clinical & Data · Chốt ĐTĐ2 làm bệnh chính + mở rộng schema (DAT-07)
- **Làm:** Nghiên cứu khoanh vùng bệnh mãn tính sẵn dataset (HF/Kaggle/NIN/NHANES) → chọn **ĐTĐ2 làm anchor tim-chuyển hoá** (THA + CKD sớm là comorbidity modifier). Mở rộng `FoodItem`: thêm `sugar_g`, `gi_source`/`gi_source_ref`, helper `available_carb_g` + `glycemic_load()`
- **Kết quả:** 11 unit test mới (tests/test_food_item.py) pass, tổng 46 test xanh (trừ test_agent.py cần langgraph chưa cài trong env này); `validate_data.py` áp cùng ràng buộc GI/đường trên CSV, chạy sạch
- **Phát hiện:** Dataset "diabetes/heart" trên HF/Kaggle hầu hết là dữ liệu **dự đoán bệnh**, không phải dữ liệu dinh dưỡng — nguồn thật cho engine vẫn là NIN 2017 + USDA + GI (Atkinson 2021 / Mai 2001). GI phủ thưa → `glycemic_load` phải None-safe
- **Vướng:** GI cho món Việt (phở/bún) mâu thuẫn giữa nguồn (phở GI 53 vs "cao") → cần chốt ở bước seed gi_values
- **Tiếp theo:** (2) tải & trích Mai 2001 + Atkinson 2021 thành `data/seeds/gi_values.csv`; (3) ghi deep-dive vào `docs/NGHIEN_CUU_BO_SUNG_v2.md`
- **Thời gian:** ~2h

### [2026-07-26] · Cả đội · Khởi động
- **Làm:** Đọc đề bài VMEC-10, rà soát đề án mở rộng và tài liệu nghiên cứu; nhận đánh giá kỹ thuật độc lập
- **Kết quả:** Bộ tài liệu `docs/` v1 (đánh giá, kế hoạch 6 tuần, kiến trúc, phân vai, 52 ticket, rules, skills)
- **Quyết định lớn:** cắt scope mạnh — bỏ vision/OCR, knowledge graph, K8s, benchmark y khoa; giữ trọng tâm ở nguyên tắc "LLM chọn món, Python tính số" + HITL (chi tiết ở §3, DEC-001)
- **Vướng:** chưa xác định nguồn Bảng thành phần thực phẩm Việt Nam dùng được → đây là rủi ro số 1
- **Tiếp theo:** SET-01 đến SET-06 và DAT-00, DAT-01 trong tuần 1
- **Thời gian:** —

### [2026-07-27] · Claude (thay R3) · SET-03 + SET-04
- **Làm:** SET-03 — `.github/CODEOWNERS` (theo mẫu `TEAM.md` §4), `pull_request_template.md`, issue template feature + bug. SET-04 — bổ sung `ruff format --check`, `mypy`, job `docker-build` vào `ci.yml`
- **Kết quả:** `make check` xanh (51 test), `mypy src/` sạch, `docker build` + chạy container xác nhận `GET /health` trả 200
- **Phát hiện (ngoài phạm vi ticket nhưng chặn CI mới):**
  1. `src/api/routes.py` import `agent` không tồn tại trong `src/agents/graph.py` (đã đổi sang `build_graph()` từ AGT-01..06) → app không boot được. Đã tạm thay `/chat` bằng stub 501 trỏ sang ticket BE-06 (nơi cần wire `build_graph()` với repository/generator thật)
  2. 4 lỗi mypy: `MenuDraft | None` truyền vào hàm yêu cầu `MenuDraft` không None-check ở `compute_nutrition_node`/`validate_node`; `ChatOpenAI.api_key` cần `SecretStr`
  3. `print()` trong `src/main.py` (vi phạm `CLAUDE.md` §4) → đổi sang `logging`
  4. Dockerfile: `pip install --user` cài vào `/root/.local`, nhưng `/root` mode 0700 chặn traversal của `appuser` dù đã `chown` — container không khởi động được (`Permission denied`). Đổi sang cài system-wide, copy `/usr/local/lib/.../site-packages` + `/usr/local/bin` — xem DEC-009
  5. `ruff format --check` fail trên 16 file cũ (chưa từng chạy formatter) → chạy `ruff format` một lần cho toàn repo (chỉ whitespace, test vẫn 51/51 xanh) để gate mới không đỏ ngay khi bật
- **Vướng:** chưa có `develop` branch (chỉ có `main`) → tạo nhánh `feature/SET-03-04-codeowners-ci` từ `main`
- **Tiếp theo:** SET-05 (deploy) cần thông tin tài khoản Render/Vercel/Neon từ R3; SET-01/SET-02/SET-06 cần xác nhận đã hoàn tất hay chưa
- **Thời gian:** ~2h

### [2026-07-27] · Claude (thay R3) · SET-01 bootstrap
- **Làm:** Rà lại toàn bộ EPIC 0 và phát hiện nhiều phần trước đó *chưa thực sự* đạt AC dù trông như đã xong. Sửa: thêm `pyproject.toml` (không tồn tại), thêm target `make run`/`lint`/`format` vào `Makefile` (AC "cả 5 người chạy `make run`" trước đó chắc chắn fail vì không có target), bổ sung biến thiếu trong `.env.example` (`APP_NAME`, `MODEL_NAME`, `LLM_TEMPERATURE`), redact `AI_LOG_API_KEY` thật khỏi `.env.example` (đã từng bị redact bởi Đinh Lê Quỳnh Phương rồi bị commit đè lại bằng key thật). Tạo branch `develop` trên repo đội thật (`AI20K-Build-Phase-Cohort-3/P-031`) — trước đó chỉ có `main`
- **Kết quả:** PR #3 (SET-01) + PR #2 (SET-03/SET-04, xem entry trước) mở trên repo đội thật
- **Phát hiện quan trọng:** repo đội thật là `AI20K-Build-Phase-Cohort-3/P-031`, không phải `hwngkm/VMEC10_P31` (repo cá nhân) — công việc trước đó (bao gồm cả PR đầu của phiên này) từng nhắm nhầm repo
- **Vướng:** tài khoản GitHub hiện dùng (`hwngkm`) không có quyền Admin trên repo đội thật (`permissions.admin=false` qua API) dù được xác nhận là admin — cần người thật kiểm tra lại trên GitHub UI để bật branch protection cho `main`/`develop` (AC SET-01 "main không push thẳng được" chưa đạt). TEAM.md/CODEOWNERS vẫn dùng handle placeholder vì chưa có tên GitHub thật của 4 thành viên
- **Tiếp theo:** merge PR #2 + PR #3, sau đó bật branch protection, điền tên thật vào TEAM.md/CODEOWNERS, xác nhận SET-02 đã chạy trên máy cả 4 người, viết lại README theo đúng AC SET-06 (hiện là README kỹ thuật cho khung code, thiếu phần giới thiệu dự án/Live URL/thành viên)
- **Thời gian:** ~1h

### [2026-07-27] · Claude (thay R3) · Gộp lên nhánh hung + SET-05/SET-06
- **Làm:** Theo yêu cầu Hưng — vì admin repo là BTC (không phải đội), gộp PR #2 + PR #3 vào một nhánh và đẩy thẳng lên `hung` (nhánh cá nhân trên repo đội) thay vì chờ merge qua `develop`/`main`. Trong lúc gộp: phát hiện + fix bug BOM khiến `.git/hooks/pre-push` không chạy được trên Windows (`cannot spawn ... No such file or directory`) — sửa gốc trong `scripts/setup_hooks.sh`. Thêm `GET /api/v1/health` (AC SET-05 yêu cầu đúng path này, code cũ chỉ có `/health` ở root). Thêm `render.yaml` blueprint cho backend. Viết lại `README.md` theo `docs/templates/README_boilerplate.md` cho đúng AC SET-06 (nội dung kỹ thuật cũ chuyển sang `docs/KHUNG_CODE.md`)
- **Kết quả:** nhánh `hung` trên `AI20K-Build-Phase-Cohort-3/P-031` có đầy đủ SET-01, SET-02 (hook), SET-03, SET-04, phần code của SET-05, và SET-06 (được duyệt, bảng thành viên/tài khoản demo còn để trống chờ đội tự điền)
- **Phát hiện:** working tree có sẵn thay đổi dở từ phiên làm việc khác (không phải tôi) — `src/agents/graph.py` được thêm một `agent` object "backward-compat" xung đột với cách tôi đã sửa `routes.py` trong PR #2 (bỏ `/chat` cũ). Đã `git stash` (không mất), **chưa quyết định** giữ cách nào — cần Hưng xem lại trước khi áp dụng
- **Vướng:** SET-05 mới có tài khoản Vercel; chưa có Render + Neon/Supabase nên chưa deploy thật được, `render.yaml` mới là chuẩn bị sẵn cấu hình
- **Tiếp theo:** hướng dẫn Hưng các bước Render + Neon cụ thể; quyết định xử lý stash graph.py; đội tự điền TEAM.md/README khi có tên thật
- **Thời gian:** ~1.5h

### [2026-08-05] · Claude (tiếp quản HANDOFF_2026-08-05.md) · Merge chuỗi 6 PR (CI self-hosted, DAT-09/10, AGT-09/10, nghiên cứu ĐTĐ) + 2 sự cố phát sinh
- **Làm:** Tiếp quản `HANDOFF_2026-08-05.md` từ phiên trước (worktree `vmec10-architecture-audit-253205`), merge theo đúng thứ tự phụ thuộc #18 → #20 → #21 → #24 → #22 → #23 vào `develop`. Trước khi merge từng PR, verify **thật** (không chỉ tin CI đã báo, vì `.venv` dùng chung thiếu `ortools` nên CI/agent trước không chạy được test CP-SAT thật): cài `ortools` + `google-genai`, chạy lại `make check` trên từng nhánh.
- **Kết quả xác minh:** claim "0 vi phạm sau khi sửa làm tròn có hướng" trong handoff **CONFIRMED thật** — 13/13 test `test_cpsat_optimizer.py` pass (gồm 6 hồ sơ `_AUDIT_PROFILES`), không chỉ đọc code tĩnh như agent trước.
- **2 phát hiện mới (không có trong handoff gốc):**
  1. `requirements.txt` thiếu `google-genai` — bug **có sẵn từ trước trên `develop`** (không liên quan 6 PR), chặn `pytest` fail ngay bước collect. Vá bằng PR riêng (#25), merge trước tiên.
  2. Cài `ortools` thật vào `mypy` mới lộ 12 lỗi thật ở `src/agents/optimizer.py` (API PascalCase `NewIntVar`/`Add`... không có type stub, dù chạy đúng ở runtime qua alias legacy) — khác hẳn "3 lỗi baseline langgraph/pydantic_settings" mà handoff ghi. Sửa sang API snake_case có stub (`new_int_var`/`add`...), thêm vào PR AGT-10.
- **🔴 Sự cố tự gây ra:** dùng `gh pr merge 21 --delete-branch` xoá `feature/AGT-09-cpsat-menu-optimizer` — đúng cái bẫy handoff cảnh báo ("GitHub tự đổi base PR #24 sang develop, đừng tự đổi tay") nhưng theo cách khác: xoá branch base khiến GitHub **tự đóng PR #24** thay vì tự retarget. `gh pr reopen` không cứu được (base đã mất). Khắc phục: tạo PR mới **#26** từ đúng branch đầu (`feature/AGT-10-wire-cpsat-graph`, commit không mất), base thẳng `develop`, merge `develop` vào nhánh, giải xung đột (DEVLOG.md/TICKETS.md: cộng dồn cả hai đoạn; `optimizer.py`/`test_cpsat_optimizer.py`: giữ bản AGT-10 vì AGT-09's `_solve_slot` bị viết lại hoàn toàn), verify lại đủ 102 test + mypy sạch, merge #26 thay #24 (đã đóng #24 kèm comment trỏ sang #26).
- **Bài học:** sau lần này, **không dùng `--delete-branch` khi PR khác còn base vào branch sắp xoá** — kiểm tra trước bằng `gh pr list --state open` xem có PR nào base = branch sắp xoá không.
- **Kết quả cuối trên `develop`:** 102 test xanh, `ruff check`/`ruff format --check`/`mypy src/` sạch 0 lỗi, `food_items.csv` **125/152 dòng** có nguồn, `scripts/validate_data.py` 0 lỗi (5 cảnh báo cũ, không cảnh báo mới). Không còn PR nào trong 6 PR gốc ở trạng thái OPEN.
- **Chưa xử lý (để nguyên, ngoài phạm vi phiên này):** PR #17 (`develop`→`main`, có sẵn từ trước, không thuộc chuỗi handoff); file `HANDOFF_2026-08-05.md` ở `D:\VMEC10_P31\` gốc (tự ghi "tự huỷ giá trị sau khi merge hết 6 PR" nhưng để người dùng tự xoá).
- **Tiếp theo:** EVL-01/EVL-02 (bộ eval + runner) hoặc DEL-03 (video demo, MVP demo được ngay không cần API key nhờ hybrid CP-SAT mặc định) — theo gợi ý ưu tiên trong handoff §7.
- **Thời gian:** ~2h

### [2026-08-05] · Claude (theo yêu cầu Hưng) · Đồng bộ tài liệu theo PRD v2.1 + rà lại quyết định needs_expert_review đa bệnh lý
- **Làm:** Sau khi merge PRD v2.1 (Đinh Lê Quỳnh Phương, thu hẹp trọng tâm MVP về ĐTĐ2) vào `develop`, cập nhật `CLAUDE.md`, `docs/TICKETS.md`, `docs/rules/10-clinical-safety.md`, `docs/00_ASSESSMENT.md`, `docs/PLAN.md`, `docs/ARCHITECTURE.md` để nhất quán với PRD mới — không xoá nội dung đa bệnh lý, chỉ chú thích ưu tiên nghiệm thu.
- **Câu hỏi mở ra:** PRD v2.1 §2.2 đọc theo nghĩa đen có thể hiểu là MỌI hồ sơ có bệnh đồng mắc ngoài ĐTĐ2 phải bắt buộc `needs_expert_review` — khác hành vi hiện tại của `compute_targets()` (chỉ gắn cờ khi rule thật sự xung đột, DEC-007). Ban đầu định sửa code theo hướng này nhưng dừng lại vì đây là ngưỡng lâm sàng thật, đúng tinh thần `CLAUDE.md` §6 "không chắc thì hỏi, đừng tự đặt".
- **Research trước khi quyết:** đọc lại `KeHoachDuAn_VNutriCare_VMEC10_v3.docx` (chính PRD.md v2.1 ghi là "Nguồn yêu cầu chính") — mục 6.4.1 "Bốn tình huống kiểm chứng" đặc tả **chính xác** hành vi hiện tại: ca ĐTĐ2+CKD chỉ chuyển chuyên gia khi dải ngưỡng ADA/KDIGO hẹp bằng 0 (xung đột số thật), KHÔNG phải vì có 2 bệnh — trích nguyên văn tài liệu: "Một hệ thống kém sẽ âm thầm chọn một bên. Hệ thống này phát hiện [xung đột] và chuyển cho chuyên gia quyết định." Mục 1.1 của cùng tài liệu còn nói thẳng đồng mắc "bắt buộc hệ thống phải xử lý được, không thể thiết kế cho từng bệnh riêng lẻ". `docs/NGHIEN_CUU_DAI_THAO_DUONG_2026.md` (merge cùng ngày) liệt kê cơ chế phát hiện xung đột này là **điểm khác biệt cạnh tranh** so với app đối thủ (không app nào xử lý đa bệnh lý đồng thời).
- **Quyết định:** giữ nguyên `compute_targets()`/DEC-007, KHÔNG sửa code. Đã sửa lại các note vừa thêm vào `CLAUDE.md`/`docs/TICKETS.md`/`docs/rules/10-clinical-safety.md` cho khớp kết luận này (bản đầu ghi nhầm là "cần sửa code" — xem DEC-014).
- **Bài học:** một dòng tóm tắt trong PRD (viết bởi 1 thành viên, không trích tài liệu gốc) có thể đọc sai nghĩa nếu không đối chiếu lại nguồn chính — nhất là khi nó đảo ngược một quyết định đã kiểm chứng bằng test. Luôn tìm "nguồn yêu cầu chính" thật trước khi sửa code lâm sàng.
- **Thời gian:** ~30 phút (research + sửa tài liệu)

### [2026-08-06] · R2 (Claude, theo yêu cầu Hưng) · DAT-04 — thêm 48 nguyên liệu Việt từ bảng NIN nội bộ chuyên gia
- **Làm:** Hưng chỉ ra 2 sheet "Bảng TP" (841 dòng) và "Bảng TP có phospho" (397 dòng) trong `data/Bảng xác định nhu cầu dinh dưỡng + thực đơn.xlsx` — xác nhận đây là bảng thành phần dinh dưỡng gốc từ NIN, do chính chuyên gia dinh dưỡng dự án biên soạn/dùng (không phải LLM sáng tác)
- **Đối chiếu trước khi tin dùng:** so khớp tên với `food_items.csv` hiện có — phát hiện 21/80 dòng trùng tên có kcal lệch >2 so với NIN/USDA đã cite (VD Cà rốt NIN=47 vs bảng này=43.65) → **không ghi đè** dữ liệu đã xác minh trước, chỉ thêm dòng MỚI (đúng DEC-008)
- **Ràng buộc kỹ thuật phát hiện khi trích:** `validate_data.py` bắt buộc `na_mg`/`k_mg`/`p_mg` phải có giá trị khi `kcal_100g` đã điền (không nằm trong `OPTIONAL_NUMERIC_COLS`) — sheet "Bảng TP" (841 dòng, nhiều tên hơn) KHÔNG có 3 cột này nên không dùng được để tạo dòng mới; chỉ sheet "Bảng TP có phospho" đủ điều kiện, và trong đó vẫn còn 309/387 dòng thiếu Na hoặc K thật trong bảng gốc (không suy đoán để lấp)
- **Kết quả:** viết `scripts/extract_menu_xlsx_composition.py`, thêm **48 nguyên liệu mới** (id 3000-3047, `source=NIN`) đầy đủ kcal/protein/carb/fat/fiber/na/k/p. `validate_data.py` 0 lỗi, `pytest` 112/112 pass
- **Khoảng trống còn lại:** 309 nguyên liệu trong bảng nội bộ (đa số ngũ cốc/tinh bột) thiếu Na hoặc K — cần R2 tự tra bổ sung hoặc chấp nhận để trống vĩnh viễn cho nhóm này; 21 dòng lệch số liệu với NIN/USDA hiện tại cần R2 đối chiếu ấn bản NIN nào đúng hơn trước khi quyết định có sửa dữ liệu cũ hay không

### [2026-08-05] · R2/R3 (Claude) · Bỏ trần số lượng EPIC 1/2 + fill thêm data + BE-01 (schema DB thật + ERD)
- **Làm (3 việc song song theo yêu cầu):**
  1. **Bỏ trần EPIC 1/2:** `DAT-02` (150 món), `DAT-04` (80 món ăn), `DAT-05` (80 cặp thuốc-thực phẩm), `DAT-06` (~15 tài liệu guideline), `CLN-02` (40 rule) — đổi AC từ "≥N là đích" sang "≥N là SÀN, không phải trần", ghi rõ trạng thái thật hiện tại của từng ticket (VD `dishes.csv` mới 3/80, cần ưu tiên trước khi mở rộng thêm).
  2. **Fill thêm data thật:** `drug_food_interactions.csv` — điền `source_ref` cho 17/30 cặp (Warfarin, Digoxin, Enalapril, Atorvastatin, Hydrochlorothiazide, Colchicin, Allopurinol, Ciprofloxacin, Amlodipin, Gliclazide, Insulin) sau khi xác minh từng dược chất có chuyên luận riêng trên Dược thư Quốc gia VN 2022 (`trungtamthuoc.com/hoat-chat/<tên>`). 13 cặp còn lại (Losartan, Simvastatin, Metformin, Levothyroxine, Furosemide, Spironolactone, Phenelzine, Tetracycline, Sắt, Canxi) **cố ý để trống** — không xác nhận được có chuyên luận riêng qua tìm kiếm, không suy đoán (DEC-008).
  3. **BE-01 (schema DB thật):** `src/db/models.py` — 15 bảng SQLAlchemy khớp `ARCHITECTURE.md` §5, bổ sung 6 bảng ERD cũ (viết từ S1, trước khi có data thật) chưa vẽ: `dishes`, `dish_ingredients`, `serving_sizes`, `patient_medications`, `patient_allergies`, `food_logs`, `guideline_chunks`. `alembic/` init + migration đầu, đã test `upgrade head`/`downgrade base` sạch trên SQLite trắng (không đụng Postgres thật trong `.env` — dùng `DATABASE_URL` override tạm trỏ SQLite để sinh migration, tránh kết nối nhầm vào DB cloud chung của team). `tests/test_db_models.py` (6 test).
- **Sự cố trong lúc làm (ghi cả lỗi của chính mình):** khi định đọc file trên `main` để đối chiếu, lỡ chạy `git checkout main -- .` trên nhánh `work/hung-consolidated` — ghi đè toàn bộ working tree bằng nội dung `main`, xoá mất 1 dòng sửa `.gitignore` chưa commit của Hưng. Tìm lại được nội dung gốc từ stash commit cũ (`git fsck --no-reflog` — chưa bị gc), khôi phục bằng `git reset --hard HEAD` (đã xin phép trước khi chạy vì bị auto-mode chặn) rồi áp lại đúng 1 dòng đã mất. Không mất gì, nhưng bài học: **không thao tác `checkout <branch> -- .` khi có WIP người khác trên nhánh đang đứng**, dùng `git show <branch>:<path>` để đọc file nhánh khác mà không đụng working tree.
- **Kết quả:** `validate_data.py` 0 lỗi (drug_food_interactions từ "30 cặp chưa có source_ref" → còn 13) · `alembic upgrade head`/`downgrade base` chạy sạch trên SQLite trắng · 108 test xanh (thêm 6 test DB) · ruff/format sạch cho `src/db/` + test mới · ERD trong `ARCHITECTURE.md` §5 viết lại đầy đủ 15 bảng khớp `src/db/models.py`.
- **Còn lại (ghi vào ticket `BE-10` mới):** chưa có script nạp `data/seeds/*.csv` vào DB thật (`scripts/seed_db.py`) — DB schema đã build xong nhưng vẫn trống, mọi thứ vẫn chạy qua CSV loader hiện có (`src/clinical/seeds.py`) cho tới khi BE-10 xong.
- **Tiếp theo:** BE-10 (seed script), tiếp tục lấp `dishes.csv` (3/80, ưu tiên cao nhất còn lại của EPIC 1), R2 tự tra nốt 13 cặp thuốc-thực phẩm còn thiếu nguồn.

### [2026-08-05] · Claude (R3) · Thực hiện PLAN_DAT-12 — BE-10 seed_db.py
- **Làm:** Đọc lại toàn bộ dự án (git log, TICKETS.md, data/README.md, `src/db/models.py`, alembic, test) trước khi bắt tay — xác nhận §2.1 (bỏ trần TICKETS.md) và DAT-11 đã xong từ commit trước, chỉ còn thiếu ticket `DAT-12` (đã thêm) và §2.3.1 (`seed_db.py`, chưa ai làm).
- **`scripts/seed_db.py` + `make seed`:** đọc `food_items/dishes/dish_ingredients/clinical_rules/drug_food_interactions/serving_sizes.csv` → insert qua `src/db/models.py`. Idempotent bằng `session.merge()` theo khoá chính tự nhiên của từng bảng; riêng `serving_sizes` không có khoá tự nhiên trong CSV nên xoá-hết-rồi-nạp-lại (nội dung giống hệt mỗi lần chạy). `dish_ingredients` tự bỏ qua (kèm log rõ dòng nào) nếu `food_id`/`dish_id` chưa tồn tại/chưa có số liệu, thay vì crash lỗi FK. **Không** seed `gi_values.csv`/`purine_values.csv`/`usda_values.csv` — đã merge vào `food_items.csv` từ trước, không phải bảng DB độc lập.
- **Verify thật (không chỉ tin test):** chạy `DATABASE_URL=sqlite:///./_tmp... python scripts/seed_db.py` 2 lần liên tiếp trên DB trắng — lần 1 và lần 2 đều ra đúng 125 food_items / 3 dishes / 11 dish_ingredients / 21 clinical_rules / 30 drug_food_interactions / 5 serving_sizes (idempotent thật, không chỉ test giả lập).
- **Kết quả:** `tests/test_seed_db.py` — 4 test (nạp đúng số liệu thật, không lỗi FK, idempotent, bỏ qua dish_ingredient thiếu food_item). 112 test xanh toàn repo, ruff/mypy sạch cho file mới (các lỗi ruff có sẵn ở `scripts/log_*.py`/`codex_hook.py` không đụng tới — ngoài phạm vi).
- **Chưa làm trong phiên này (đúng theo `docs/PLAN_DAT-12-uncap-data-and-db.md` §2.2 — cần R2 chuyên môn thật, không tự ý làm):** fill thêm `dishes.csv` (3→80+), `clinical_rules.csv` (21→40+), 13 cặp `drug_food_interactions` còn thiếu `source_ref`, 27 dòng `food_items.csv` còn trống. Rà index DB theo truy vấn thật và cài `psycopg2-binary` cũng cố ý chưa làm — đúng kế hoạch, chỉ cần khi BE-03+ / deploy Postgres thật bắt đầu.
- **Tiếp theo:** R2 tiếp tục fill dữ liệu (ưu tiên `dishes.csv`), R3 rà index khi BE-03 bắt đầu viết truy vấn thật.
- **Thời gian:** ~1h

### [2026-08-05] · Claude · Bỏ trần dữ liệu tối đa — 7.173 food_items (mục tiêu 1000+), 2.635 dishes (mục tiêu 500+)
- **Làm:** Theo yêu cầu Hưng "lấy tối đa dữ liệu có thể từ dataset/paper sẵn có trong `data/`", viết 3 script ETL từ tài nguyên đã tải sẵn (không gọi API, không suy đoán số liệu):
  1. `scripts/extract_usda_bulk.py` — SR Legacy (7.793) + Foundation Foods (436) từ `food.csv`/`food_nutrient.csv` → **6.854 dòng mới**, chỉ giữ dòng đủ 8 cột bắt buộc, loại mục cô đặc vô nghĩa lâm sàng (bột nở, kem tartar).
  2. `scripts/extract_nin2017_bulk.py` — trích TOÀN BỘ bảng "TPTP VN 2017" (304 trang, `pdfplumber` neo cột theo toạ độ tag-name) → **167 dòng mới** (621 mã có dữ liệu trên trang hợp lệ, 87 đã có sẵn, còn lại thiếu Na/K/béo/xơ thật sự không in trong bảng gốc, loại đúng RULE-2).
  3. `scripts/extract_fndds_dishes.py` — USDA FNDDS (`survey_fndds_food.csv` + `input_food.csv`, phân rã nguyên liệu thật qua SR Legacy) → **2.632 món quốc tế** có đủ nguyên liệu quy đổi được, đúng kiến trúc RULE-1 (món = nguyên liệu × gram, không lưu số dinh dưỡng trực tiếp).
- **🔴 Hồi quy hiệu năng phát hiện VÀ SỬA trước khi merge:** thêm ~7000 dòng vào `food_items.csv` khiến `retrieve_context` (đưa toàn bộ làm ứng viên CP-SAT/prompt LLM) chậm **30-50 lần** (13 test CP-SAT từ 1,5s → 50s — hồi quy so với thành tích "0,1s OPTIMAL" đã ghi ngày 05/08 buổi sáng). Đã hỏi Hưng trước khi merge, chọn phương án: giữ toàn bộ dữ liệu, thêm `USDA_BULK_ID_THRESHOLD=100_000` trong `src/agents/nodes/core.py` để lọc khối USDA bulk (id=fdc_id, luôn ≥100000) khỏi ứng viên sinh thực đơn — chỉ dùng làm kho tham chiếu. Sửa test `tests/test_cpsat_optimizer.py` (thêm fixture `menu_candidates` lọc đúng như production) — về lại 1,48s.
- **🔴 Bug thật thứ 2 tìm và sửa:** 1 món FNDDS có nguyên liệu công thức quy mô lớn (bột mì 4.540g — mẻ bánh thương mại) vượt `MenuItem.grams<=2000`, làm crash `load_dish_menus()` cho TOÀN BỘ file khi chạy test (không cô lập theo món). Thêm bộ lọc loại nguyên liệu >2000g và tổng khẩu phần >2000g trong script trích xuất, không nới trần hệ thống.
- **Xác minh thật:** `make seed` trên SQLite trắng, 2 lần liên tiếp (idempotent) → 7.146 food_items / 2.635 dishes / 5.369 dish_ingredients / 0 lỗi FK. `pytest -q` 112 test xanh, `mypy`/`ruff` sạch, `validate_data.py` 0 lỗi.
- **Việc còn để ngỏ (đã báo Hưng, không tự ý làm hết trong 1 phiên):** `PURINEDATABASEANDDATASOURCES2025.xlsx` (608 dòng purine, cần fuzzy-match tên món — phức tạp hơn 3 việc trên vì không có khoá chung); NIN 2007 (lợi ích thấp, vấn đề font); dữ liệu cần R2 chuyên môn thật (3 món Việt `pending`, `clinical_rules`/`drug_food_interactions` còn thiếu).
- **Bài học:** thêm dữ liệu "càng nhiều càng tốt" vào một hệ thống đã tối ưu cho quy mô nhỏ (CP-SAT ~150 ứng viên) có thể phá hiệu năng một tính năng khác đã kiểm chứng kỹ — luôn đo lại theo end-to-end (chạy test thật, không chỉ validate dữ liệu) trước khi merge, kể cả khi mỗi dòng dữ liệu riêng lẻ đều đúng.
- **Thời gian:** ~3h (2 lần chạy trích NIN 2017 40 phút mỗi lần do phải debug lỗi neo cột)

---

### [2026-08-06] · Claude · Bắt đầu lấp món Việt — +27 món (vẫn `pending`, chưa thay thế R2)
- **Bối cảnh:** Hưng hỏi thẳng "sao món Việt vẫn mới có 3 món" sau đợt 05/08 — đúng, 2.632 món thêm hôm trước toàn bộ là USDA FNDDS (Mỹ), không đụng tới món Việt. Hưng yêu cầu "soạn công thức, call thêm API hoặc search thu thập thêm công thức". Đã kiểm tra 1 paper Hugging Face (Epicure, arXiv 2605.22391) Hưng gợi ý — xác nhận qua fetch PDF thật: đây là model embedding nguyên liệu (Gemini embedding + RecipeNLG/Recipe1M+/Xiachufang/ChefKoch/SOMOS/USDA), có định lượng thật nhưng **không có món Việt Nam trong bất kỳ dataset liệt kê nào** → không dùng được, không tốn công tích hợp.
- **Nguồn thật tìm thấy trong `data/` chưa từng khai thác:** `data/Bảng xác định nhu cầu dinh dưỡng + thực đơn.xlsx` — file thực đơn nội bộ dự án, có 4 sheet thực đơn mẫu (Sáng/Trưa/Tối) với cột "KL sống sạch" (gram thật/khẩu phần). Viết `scripts/extract_menu_xlsx_dishes.py`: parse theo state machine (nhãn bữa ăn → tích luỹ nguyên liệu đến dòng "Hiện tại"/"Cần xây dựng"), khớp `food_id` bằng tên đã chuẩn hoá (bỏ dấu ngoặc, hạ chữ thường) — **cố tình không fuzzy-match rộng** (VD không tự suy "Dầu ăn" ≈ "Dầu ăn thực vật") để tránh gán nhầm loại thực phẩm khác thành phần dinh dưỡng khác nhau → tỷ lệ khớp chỉ ~37% (67/180 dòng), 2 sheet đầu (`tđ1`,`tđ2`) không có nhãn bữa ăn rõ nên 0 kết quả. Kết quả: **15 "bữa ăn" thật** (dish_id `MENU-*`), gram từ tài liệu thật, nhưng nguyên liệu bị thiếu (chỉ giữ phần khớp được).
- **12 món Việt tự soạn qua LLM** (phở gà, bún chả, canh chua cá, rau muống xào tỏi, đậu phụ sốt cà chua, cá kho tộ, gà kho gừng, canh cải nấu tôm, sườn xào chua ngọt, trứng chiên hành, canh su hào cà rốt thịt băm, nấm hương xào thịt bò) — dùng nguyên liệu đã có `food_id` thật trong 319 dòng Việt curated/NIN, gram theo kinh nghiệm ẩm thực phổ thông (KHÔNG có nguồn định lượng đối chiếu — khác hẳn 3 món gốc đã đối chiếu Na với nghiên cứu). Vài món thiếu gia vị (đường, dấm, nước dùng...) vì `food_items.csv` chưa có các mục đó.
- **Tất cả 27 món đều `verified_by=pending`** — không tự ý nâng lên "đã duyệt". Ghi rõ trong `note` từng món lý do cần R2 rà soát.
- **Xác minh:** `validate_data.py` 0 lỗi mới, `pytest -q` 112/112 pass, `make seed` (SQLite trắng, 2 lần) → dishes 2.635→**2.662**, dish_ingredients 5.369→**5.479**, 0 dòng bị skip do FK.
- **Việc còn để ngỏ:** 3 món gốc + 27 món mới đều `pending`, tổng 30/2.662 món Việt thật cần R2 duyệt tay — khoảng cách với mục tiêu "500 món Việt" vẫn còn rất lớn và **không có bulk source Việt Nam nào tương đương FNDDS** để lấp nhanh; đường đi khả thi duy nhất còn lại là R2 duyệt dần + LLM soạn thêm theo lô, không có shortcut tự động.
- **Thời gian:** ~1.5h

---

### [2026-08-06] · Claude · Thực hiện PLAN_DAT-13 (đợt 1) — 13/13 drug_food_interactions có source_ref, khảo sát Na/K/kcal
- **§2.3 (DAT-05) — 13 cặp `drug_food_interactions.csv` thiếu `source_ref`:** tra cứu thật qua WebFetch/WebSearch cho từng cặp, **không dùng nguồn nào chưa xác nhận được nội dung**:
  - 9 cặp tra được trực tiếp trong **Dược thư Quốc gia VN 2022** (Losartan+kali, Simvastatin+bưởi, Metformin+rượu bia, Metformin+B12, Levothyroxine+đậu nành, Furosemide+kali, Spironolactone+kali, Tetracycline+canxi) qua `trungtamthuoc.com/hoat-chat/*` — trích nguyên văn đoạn liên quan vào `source_ref`.
  - 4 cặp Dược thư không có bản tiếng Việt đủ chi tiết → dùng nguồn quốc tế uy tín thay thế (đúng thứ tự ưu tiên plan §2.3 "Martindale/BNF... trước khi bỏ trống"): Levothyroxine+canxi (MedlinePlus/NIH), Levothyroxine+cà phê (Benvenga et al., *Thyroid* 2008;18(3):293-301 — nghiên cứu gốc, espresso giảm hấp thu ~36%), Phenelzine+tyramine (StatPearls/NCBI NBK554508), Sắt+trà-cà phê và Canxi+oxalat rau chân vịt (NIH Office of Dietary Supplements, Iron/Calcium Health Professional Fact Sheet).
  - **30/30 cặp giờ có `source_ref`** (`validate_data.py` không còn cảnh báo này). `verify_status` vẫn giữ `to_verify` — có nguồn thật không thay thế được việc R2 xác nhận phù hợp lâm sàng trước Demo Day.
- **§2.1 khảo sát lại:** chạy `scripts/extract_menu_xlsx_composition.py` (dry-run) xác nhận 272/397 dòng "Bảng TP có phospho" vẫn thiếu ≥1 cột bắt buộc (na/k/p...) sau đợt 48 dòng đã thêm sáng nay — **chưa cross-reference NIN2017 PDF/USDA cho 272 dòng này** (cần quét lại toàn bộ PDF 304 trang không lọc theo mã đã có, ước tính ~40 phút, để dài hơn phạm vi phiên này) — để lại cho phiên sau, không tự đoán số.
- **§2.4 — rà soát 60 dòng lệch kcal thật (không phải 21 như ước tính ban đầu trong plan, do bản kiểm tra đầu dùng nhầm cột "KL sống sạch" cho sheet "Bảng TP" thay vì cột E/100g — đã sửa và verify lại):** ghi toàn bộ vào `data/seeds/food_items.kcal_mismatch_report.csv` (food_id, tên, kcal hiện tại + nguồn, sheet xlsx, kcal xlsx, chênh lệch). Đa số lệch nhỏ (2-8 kcal, hợp lý do khác ấn bản NIN/làm tròn). **2 outlier cần R2 xem gấp trước khi dùng bất kỳ giá trị nào:** `Đậu hà lan` (id 3008, food_items=342 kcal vs xlsx=70 kcal — chênh lệch ~5 lần, nghi ngờ 1 trong 2 nguồn nhầm "đậu Hà Lan khô" với "đậu Hà Lan tươi/đông lạnh") và `Sữa đặc có đường` (id 125, food_items=65 kcal vs xlsx=336 kcal — nghi ngờ 1 nguồn tính theo sữa đã pha loãng, 1 nguồn tính nguyên chất). **Không tự sửa số nào** — đúng nguyên tắc plan §3 (không sửa dữ liệu đã qua CI khi chưa có quyết định rõ ràng).
- **Chưa làm trong đợt này:** §2.1 phần còn lại (272 dòng), §2.2 (`food_items.template.csv` 152 dòng, 0% xong).
- **Thời gian:** ~2h (phần lớn là 13 lượt WebFetch/WebSearch xác minh nguồn thật cho drug interactions)

---

### [2026-08-06] · Claude · PLAN_DAT-13 (đợt 2) — quét toàn bộ NIN2017, lấp 78/272 dòng §2.1
- **Viết `scripts/build_nin2017_full_index.py`** — biến thể của `extract_nin2017_bulk.py` nhưng KHÔNG lọc theo mã đã có trong `food_items.csv`, để tạo 1 bảng tra cứu đầy đủ theo tên phục vụ cả §2.1 và §2.2. Chạy nền ~5 phút (nhanh hơn nhiều so với ước tính 40 phút của lần trích trước — lý do: bảng thành phần chính của NIN2017 chỉ nằm ở **trang 24-134** (nhóm mã 01-14: ngũ cốc→đồ uống có cồn), phần còn lại của file PDF 304 trang không phải bảng thành phần cùng định dạng cột (khớp mô tả `data/README.md` "phụ lục, mục lục, các phần khác") nên các trang đó bị bỏ qua đúng theo thiết kế (`NEEDED_TAGS.issubset(anchors)` false), không phải lỗi quét thiếu. Kết quả: **236 mã, ghi vào `data/seeds/nin2017_full_index.csv`** (không commit — dẫn xuất trung gian, tái tạo được bằng script).
- **Đối chiếu 272 dòng thiếu field của "Bảng TP có phospho" (§2.1) với bảng tra cứu này:** khớp tên chuẩn hoá được **78 dòng** (Ngô vàng hạt khô, Bột gạo nếp, Cà bát, Chuối xanh, Chôm chôm, Dâu tây, Đào, Lựu, Mơ... — đa số nhóm rau củ quả nhóm mã 03-08). Đã thêm 78 dòng mới vào `food_items.csv` (id 4000-4077, `source=NIN`, `source_ref` trỏ đúng mã+trang NIN2017 — không phải suy đoán). **194/272 dòng còn lại không khớp được** — tên trong bảng nội bộ dự án không xuất hiện trong 236 mã trích được (có thể do khác cách gọi tên, hoặc thực phẩm đó nằm ngoài phạm vi trang 24-134) — **giữ trống, không suy đoán**, đúng DEC-008.
- **Đối chiếu 27 dòng còn trống của `food_items.template.csv` (§2.2):** **0/27 khớp được** với 236 mã NIN2017 (Mì ăn liền, Giò lụa, Chao, Rau ngót, Tía tô, Kinh giới, Rau răm, Mắm nêm... — toàn bộ là món chế biến sẵn hoặc rau thơm không nằm trong nhóm mã 01-14 đã trích được). Không thử USDA cross-reference (khớp chéo tiếng Việt→tiếng Anh) trong đợt này — plan §2.1 xếp bước này rủi ro cao hơn, cần thời gian riêng và nên có R2 xác nhận từng cặp khớp tên trước khi ghi vào `food_items.csv` chính.
- **Xác nhận:** `validate_data.py` 0 lỗi mới (7194→**7272** dòng đã nhập số liệu), `pytest -q` 112/112 pass.
- **Còn lại:** 194 dòng §2.1 + 152 dòng §2.2 (toàn bộ) vẫn trống — cần thử USDA cross-reference (rủi ro cao hơn, cần ghi rõ khớp chéo ngôn ngữ trong `source_ref` theo đúng plan) hoặc R2 tự bổ sung trực tiếp bằng chuyên môn.
- **Thời gian:** ~45 phút

---

### [2026-08-06] · Claude · PLAN_DAT-13 (đợt 3) — khớp chéo USDA cho 21 dòng còn lại (rủi ro cao hơn, đã ghi rõ)
- **Đúng cảnh báo "rủi ro cao hơn" của plan §2.1** khi làm bước khớp chéo ngôn ngữ Việt→Anh với USDA (thay vì khớp tên trực tiếp như NIN2017): rà thủ công 191 tên còn lại của "Bảng TP có phospho" + 27 tên trống của `food_items.template.csv`, loại bỏ có chủ đích:
  - Sản phẩm thương hiệu (Vinamilk, VIFON, Dumex, Enfa, Ensure, Pediasure, Similac, Fiso, Nutren, Abound, Prosure, Isocal...) — cần đọc nhãn dinh dưỡng riêng từng sản phẩm, không phải việc "tra chéo nguồn", để nguyên trống.
  - Món/nguyên liệu đặc thù Việt không có tương đương Mỹ hợp lý (mắm nêm, mắm ruốc, chao, tương hột, giò lụa, chả quế, rau răm, kinh giới, tía tô, rau má, rau ngót, cá lóc, cá bống...) — để trống thay vì gán tạm bợ.
  - Vài dòng OCR lỗi không đọc được ("g¹o tÎ m¸y", "Bột khoai riềg"...) — để trống.
  - Trường hợp trạng thái chế biến lệch quá nhiều để tin số liệu (VD "Sắn luộc" chỉ có "Cassava, raw" trong USDA đã nhập — luộc làm thay đổi đáng kể kcal/100g do hút nước — bỏ qua).
- **Chỉ nhận 21 khớp đủ tin cậy** (tên khớp trực tiếp 1-1, cùng bộ phận/trạng thái chế biến): Ngô tươi, Củ cải, Tỏi tây, Dưa lê, Mận, Táo ta, Thịt Dê, Ốc nhồi, Dầu thực vật, Đường cát, Đuường kính (OCR của Đường kính), cà phê tan, Hạt điều khô chiên, Hạt dẻ to, Khoai tây lát chiên, Mỡ lợn nước (đợt §2.1, id 4100-4115) + Yến mạch, Thịt lợn ba chỉ, Thịt gà (đùi, có da), Đậu phụ chiên, Hành lá (đợt §2.2, **update trực tiếp 5 dòng placeholder có sẵn id 17/20/24/56/79 trong `food_items.csv`** — phát hiện giữa chừng: `food_items.csv` đã có sẵn placeholder rỗng cho toàn bộ 152 tên của `food_items.template.csv`, thêm dòng mới cùng tên sẽ tạo trùng tên — `validate_data.py` bắt lỗi này ngay, đã sửa bằng cách update in-place thay vì append).
  - Mỗi dòng: `source=USDA`, `is_estimated=TRUE` (khác hẳn khớp trực tiếp NIN — đây là suy luận tương đồng, không phải cùng 1 thực phẩm), `source_ref` ghi rõ tên USDA gốc + fdcId + lý do khớp bằng tiếng Việt + dòng nhắc "CẦN R2 xác nhận độ phù hợp trước khi dùng cho bệnh nhân".
- **Xác nhận:** `validate_data.py` 0 lỗi (22 dòng `food_items.csv` còn trống, giảm từ 27), `pytest -q` 112/112, `make seed` (SQLite trắng, 2 lần) → 7.293 food_items, 2.662 dishes, 0 skip FK.
- **Còn lại:** 170/191 dòng §2.1 + 22/27 dòng §2.2 không tìm được khớp đủ tin cậy — đây là giới hạn thật của 2 nguồn bulk hiện có (NIN2017 chỉ phủ trang 24-134, USDA không có tương đương cho món/nguyên liệu đặc thù Việt), không phải do thiếu công sức tra cứu. Bước tiếp theo khả thi duy nhất là R2 tự bổ sung bằng chuyên môn hoặc tài liệu khác ngoài `data/` hiện có.
- **Thời gian:** ~40 phút

---

---

## 3. Lịch sử commit

| Ngày | Người | Nội dung |
|---|---|---|
| 2026-08-06 | Kim Mạnh Hưng | merge: hoa giai xung dot develop <- main (sync dinh ky) |
| 2026-08-06 | Kim Mạnh Hưng | feat(data): thêm 27 món Việt Nam (pending, cho R2 duyệt) - DAT-04 (#37) |
| 2026-08-06 | Kim Mạnh Hưng | feat(data): bo tran du lieu toi da - 7173 food_items, 2635 dishes (DAT-12) (#36) |
| 2026-08-06 | Kim Mạnh Hưng | sync: đưa BE-01/BE-10 (schema DB + seed_db.py) từ main vào develop (#35) |
| 2026-08-06 | Kim Mạnh Hưng | feat(data,ops): bỏ trần EPIC 1/2 + fill data thật + schema DB (BE-01) (#34) |
| 2026-08-05 | Kim Mạnh Hưng | docs(data): nghiên cứu bổ sung nguồn dữ liệu từ tài liệu tổng quan |
| 2026-08-05 | Kim Mạnh Hưng | Develop (#17) |
| 2026-08-05 | Kim Mạnh Hưng | docs(ops): giu nguyen compute_targets()/DEC-007 - dinh chinh note PRD (#32) |
| 2026-08-05 | Kim Mạnh Hưng | docs(ops): chu thich pham vi DTD2 vao TICKETS/rules/ARCHITECTURE/PLAN (#31) |
| 2026-08-05 | Kim Mạnh Hưng | docs(ops): cap nhat CLAUDE.md theo trong tam DTD2 (PRD v2.1) (#29) |
| 2026-08-05 | Kim Mạnh Hưng | sync: đưa PRD v2.1 (trọng tâm ĐTĐ2) + fix README từ main vào develop (#28) |
| 2026-08-05 | Kim Mạnh Hưng | docs(ops): ghi DEVLOG tong ket merge chuoi 6 PR tu HANDOFF_2026-08-05 (#27) |
| 2026-08-05 | Kim Mạnh Hưng | data(food_items): lấp 5 dòng từ bộ FDC Survey Foods (FNDDS) bulk download (DAT-10) (#23) |
| 2026-08-05 | Kim Mạnh Hưng | docs: nghiên cứu ĐTĐ, nhu cầu tư vấn dinh dưỡng, khảo sát app, dataset (#22) |
| 2026-08-05 | Kim Mạnh Hưng | feat(agent): nối CP-SAT vào graph — hybrid CP-SAT → Gemini (AGT-10) (#26) |
| 2026-08-05 | Kim Mạnh Hưng | feat(agent): CPSATMenuOptimizer — CP-SAT thay vòng lặp sinh-rồi-thử của LLM (AGT-09) (#21) |
| 2026-08-05 | Kim Mạnh Hưng | data: lấp 6 dòng food_items từ Bảng TPTP VN 2017 + USDA (DAT-09) (#20) |
| 2026-08-05 | Kim Mạnh Hưng | ci(workflows): chuyển runs-on sang self-hosted (BTC runner) (#18) |
| 2026-08-05 | Kim Mạnh Hưng | fix(ops): them google-genai vao requirements.txt (#25) |
| 2026-08-04 | Đinh Lê Quỳnh Phương | docs(prd): cập nhật trọng tâm ĐTĐ2 (PR #19) |
| 2026-08-04 | Phùng Linh | Merge pull request #15 from AI20K-Build-Phase-Cohort-3/ui-main |
| 2026-08-04 | pl1201 | ci: use self-hosted runners |
| 2026-08-04 | Đinh Lê Quỳnh Phương | docs(prd): cập nhật PRD tập trung vào ĐTĐ2 làm bệnh lý trọng tâm |
| 2026-08-04 | Kim Mạnh Hưng | Merge pull request #16 from AI20K-Build-Phase-Cohort-3/fix/ci-utf8-locale |
| 2026-08-04 | Kim Mạnh Hưng | fix(ci): ép stdout UTF-8 trong check_structure/validate_data — sửa structure CI đỏ (locale non-UTF8) |
| 2026-08-04 | Kim Mạnh Hưng | Merge pull request #14 from AI20K-Build-Phase-Cohort-3/feature/DAT-08b-atkinson-suppl |
| 2026-08-04 | Kim Mạnh Hưng | merge: đồng bộ project/develop (lấy src/api, src/models, presentation của team) |
| 2026-08-04 | Kim Mạnh Hưng | feat(agent): nối GeminiMenuGenerator vào graph — luồng 8-node chạy đầu-cuối (pending_review) |
| 2026-08-04 | Kim Mạnh Hưng | feat(data): lấp food_items từ USDA FDC — 23 món, 88→111 dòng có số liệu |
| 2026-08-04 | Kim Mạnh Hưng | feat(data): DAT-03 — client USDA FoodData Central (lấp món NIN thiếu) + config key |
| 2026-08-04 | Kim Mạnh Hưng | feat(data): lấp gia vị mặn (mì chính/bột canh/hạt nêm/mắm tôm) — food_items 88 dòng |
| 2026-08-04 | Kim Mạnh Hưng | feat(agent): AGT-04 — MVP end-to-end với Gemini thật (LLM chọn món, Python tính, key rotation) |
| 2026-08-04 | Kim Mạnh Hưng | feat(data): DAT-04 — phân rã món ăn + test hồi quy muối (phở bò 3,58g/bát khớp mốc) |
| 2026-08-03 | Kim Mạnh Hưng | feat(data): matcher ưu tiên đủ khoáng + default carb=0 cho thịt/cá → food_items 63→80 dòng |
| 2026-08-03 | Kim Mạnh Hưng | docs(data): khẩu phần chuẩn (serving_sizes) + phát hiện dữ liệu món ăn NIN không đáng tin (DEC-013) |
| 2026-08-03 | Kim Mạnh Hưng | feat(data): purine từ USDA/ODS-NIH Purine DB — 19 món + provenance riêng (RULE-2) |
| 2026-08-03 | Kim Mạnh Hưng | feat(data): ước tính cơm/xôi/cháo (OOV) + sửa bug khoá OVERRIDES bỏ dấu (food_items 63 dòng) |
| 2026-08-03 | Kim Mạnh Hưng | feat(data): DAT-04 probe — fetcher API món ăn NIN (1250 món, có Na+tương đương muối) |
| 2026-08-03 | Kim Mạnh Hưng | feat(data): DAT-02 promote — food_items.csv 59 dòng NIN hoàn chỉnh + GI merge (validate sạch) |
| 2026-08-03 | Kim Mạnh Hưng | feat(data): DAT-02 — purine optional + bản nháp food_items từ API NIN (107/152 dòng) |
| 2026-08-03 | pl1201 | fix README encoding |
| 2026-08-02 | Kim Mạnh Hưng | feat(data): fetcher API Viện Dinh dưỡng (NIN) — unblock DAT-02 (853 món, đủ cột trừ purine) |
| 2026-08-02 | Kim Mạnh Hưng | feat(data): DAT-08b — trích 17 trị GI quả/staple từ Atkinson Suppl. Table 1 (gi_values 11→28) |
| 2026-08-02 | Đinh Lê Quỳnh Phương | docs: add NutriCare PRD |
| 2026-08-02 | Đinh Lê Quỳnh Phương | docs: add PRD and remove env example from repository |
| 2026-08-01 | pluvia21 | Merge pull request #12 from AI20K-Build-Phase-Cohort-3/nam-dev |
| 2026-08-01 | NocNam | docs: add project brief |
| 2026-08-01 | NocNam | style: format log_codex with ruff |
| 2026-08-01 | NocNam | Merge remote-tracking branch 'origin/main' into nam-dev |
| 2026-08-01 | Phùng Linh | Merge pull request #11 from AI20K-Build-Phase-Cohort-3/ui-main |
| 2026-08-01 | pl1201 | docs: add Mermaid UI flow |
| 2026-08-01 | pl1201 | docs: add UI flow |
| 2026-08-01 | Kim Mạnh Hưng | Merge pull request #9 from AI20K-Build-Phase-Cohort-3/main |
| 2026-08-01 | Kim Mạnh Hưng | Merge pull request #8 from AI20K-Build-Phase-Cohort-3/sync/gi-sugar-into-main |
| 2026-08-01 | Kim Mạnh Hưng | style: ruff format cho code DAT-07/CLN-08 để qua bước format-check của CI cohort (SET-04) |
| 2026-08-01 | Kim Mạnh Hưng | merge: đồng bộ project/main (ops SET-*) vào develop để merge lên main |
| 2026-08-01 | Kim Mạnh Hưng | Merge pull request #5 from AI20K-Build-Phase-Cohort-3/feature/t2dm-anchor-gi-sugar |
| 2026-08-01 | Kim Mạnh Hưng | Merge pull request #6 from hwngkm/feature/CLN-08-who-free-sugar |
| 2026-08-01 | Kim Mạnh Hưng | Merge remote-tracking branch 'origin/main' into feature/CLN-08-who-free-sugar |
| 2026-08-01 | Kim Mạnh Hưng | Merge pull request #5 from hwngkm/feature/DAT-08-atkinson-gi |
| 2026-08-01 | Kim Mạnh Hưng | feat(clinical): CLN-08 — rule đường tự do WHO cho ĐTĐ2 (dùng sugar_g) |
| 2026-08-01 | Kim Mạnh Hưng | feat(data): DAT-08 — thêm 4 trị GI staple từ Atkinson 2021 (gạo lứt/khoai tây/yến mạch/cà chua) |
| 2026-08-01 | Kim Mạnh Hưng | Merge pull request #4 from hwngkm/feature/DAT-07-food-schema-gi-sugar |
| 2026-08-01 | Kim Mạnh Hưng | fix(clinical): carry sugar_g qua NutritionSummary + chặn gi_source_ref khoảng trắng (DAT-07) |
| 2026-08-01 | Kim Mạnh Hưng | fix(clinical): bỏ quote thừa ở type annotation FoodItem — sửa lint UP037 (DAT-07) |
| 2026-08-01 | Kim Mạnh Hưng | docs(data): ghi deep-dive chọn ĐTĐ2 + tính khả thi GI vào nghiên cứu bổ sung (DAT-07) |
| 2026-08-01 | Kim Mạnh Hưng | feat(data): seed 7 trị GI món Việt (Chan 2001) + sửa nhãn nguồn GI Chan2001_VN (DAT-07) |
| 2026-08-01 | Kim Mạnh Hưng | feat(clinical): mở rộng schema FoodItem — đường tự do + nguồn GI riêng (DAT-07) |
| 2026-07-27 | Kim Mạnh Hưng | Merge pull request #4 from AI20K-Build-Phase-Cohort-3/hung |
| 2026-07-27 | NocNam | test 2 |
| 2026-07-27 | NocNam | test |
| 2026-07-27 | Kim Mạnh Hưng | docs: ghi DEVLOG cho phien gop nhanh hung + SET-05/06 |
| 2026-07-27 | Kim Mạnh Hưng | docs(ops): viet lai README theo AC SET-06 |
| 2026-07-27 | Kim Mạnh Hưng | feat(ops): them render.yaml blueprint cho SET-05 |
| 2026-07-27 | Kim Mạnh Hưng | fix(api): them GET /api/v1/health dung AC cua SET-05 |
| 2026-07-27 | Kim Mạnh Hưng | fix(ops): strip BOM khoi git hook de tranh loi tren Windows |
| 2026-07-27 | Kim Mạnh Hưng | Merge remote-tracking branch 'project/feature/SET-01-bootstrap' into work/hung-consolidated |
| 2026-07-27 | NocNam | Test git log |
| 2026-07-27 | Kim Mạnh Hưng | docs: ghi DEVLOG cho SET-01 bootstrap |
| 2026-07-27 | Kim Mạnh Hưng | feat(ops): bootstrap SET-01 con thieu (pyproject, make run, env) |
| 2026-07-27 | Kim Mạnh Hưng | feat(ops): SET-03 CODEOWNERS/PR/issue template + SET-04 CI gates |
| 2026-07-27 | Kim Mạnh Hưng | fix(ops): sua regression chan app boot va loi mypy (SET-04) |
| 2026-07-27 | Kim Mạnh Hưng | style(ops): ap dung ruff format cho code cu (SET-04) |
| 2026-07-27 | Kim Mạnh Hưng | chore: remove legacy tests for non-existent graph wrapper and api routes |
| 2026-07-27 | Kim Mạnh Hưng | docs: rename template README to Readme_AI20K.md |
| 2026-07-27 | Kim Mạnh Hưng | Merge branch 'chore/reorganize-repo' |
| 2026-07-27 | Kim Mạnh Hưng | fix(ci): fix ruff lint errors and ignore UP042 class enum checks |
| 2026-07-27 | Kim Mạnh Hưng | Merge pull request #2 from hwngkm/chore/reorganize-repo |
| 2026-07-27 | Kim Mạnh Hưng | chore: integrate v3 project updates from files.zip and reorganize repo |
| 2026-07-27 | Kim Mạnh Hưng | Merge pull request #1 from hwngkm/chore/reorganize-repo |
| 2026-07-27 | Kim Mạnh Hưng | chore(ops): sap xep lai repo theo template AI20K |
| 2026-07-27 | Kim Mạnh Hưng | feat(ops): initial setup for NutriCare Agent workspace |
