# DEVLOG — NHẬT KÝ PHÁT TRIỂN

> **Đây là file log duy nhất của dự án.** Nó phục vụ đồng thời Deliverable #8 (Development Journal) và #9 (Worklog).
> Quy tắc: **chỉ thêm, không sửa lịch sử.** Ghi sai thì thêm dòng đính chính, đừng xoá.
> Nhịp: mỗi người 1 entry sau mỗi buổi làm việc · cả đội 1 entry tổng kết mỗi cuối tuần.

---

## 0. Cách ghi

**Nhật ký cá nhân** — mất 2 phút, ghi vào §2:

```markdown
### [YYYY-MM-DD] · <Tên> · <Vai trò>
- **Làm:** CLN-04 bounds checker — xong phần Na/K, còn P
- **Kết quả:** 8 unit test pass, PR #23 đang chờ review
- **Vướng:** ngưỡng phospho cho CKD G4 chưa rõ đơn vị trong guideline → đang hỏi R2
- **Tiếp theo:** hoàn thiện P + viết test biên
- **Thời gian:** 3h
```

**Quyết định kỹ thuật** — ghi vào §3 khi có tranh luận đáng kể (bối cảnh → phương án → quyết định → hệ quả).

**Sự cố** — ghi vào §4. Bao gồm cả sự cố do chính mình gây ra. Không ai bị phạt vì ghi sự cố; ghi lại chính là thứ tạo ra slide "Challenges & Learnings".

**Tổng kết tuần** — R1 (kiêm PM) ghi vào §5 mỗi tối Chủ nhật.

> 💡 Tuần 6 sẽ cần đúng file này để dựng slide 9 và báo cáo. Ghi đều đặn từ tuần 1 rẻ hơn nhiều so với ngồi bịa lại lịch sử vào đêm trước Demo Day.

---

## 1. Thông tin dự án

| | |
|---|---|
| Tên dự án | NutriCare Agent — AI Agent Dinh dưỡng Lâm sàng |
| Đề bài | VMEC-10 |
| Repository | `https://github.com/AI20K-Build-Cohort-2/C2-App-XXX` |
| Live URL | *(cập nhật sau SET-05)* |
| Demo Day | 06/09/2026 *(giả định — cập nhật khi có lịch chính thức)* |
| Code freeze | 04/09/2026 23:59 |

| Vai trò | Thành viên | Email |
|---|---|---|
| R1 Tech Lead / Agent + PM | | |
| R2 Clinical & Data + Eval | | |
| R3 Backend + DevOps | | |
| R4 Frontend + Deliverables | | |

---

## 2. Nhật ký hằng ngày

<!-- Entry mới thêm vào CUỐI mục này, theo thứ tự thời gian -->

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

---

## 3. Quyết định kỹ thuật (Decision Log)

| ID | Ngày | Quyết định | Người quyết | Chi tiết |
|---|---|---|---|---|
| DEC-001 | 2026-07-26 | Cắt scope: bỏ vision/OCR, Neo4j, K8s, DDID full, benchmark MedQA | Cả đội | Xem `docs/00_ASSESSMENT.md` §9 |
| DEC-002 | 2026-07-26 | Postgres + pgvector, không dùng vector DB riêng | R1 | ADR-001 |
| DEC-003 | 2026-07-26 | LLM chỉ trả `food_id` + gram; số liệu tính bằng SQL | R1 | ADR-002 — nguyên tắc bất biến |
| DEC-004 | 2026-07-26 | Drug–food: curate 80 cặp thay vì import DDID | R2 | ADR-005 |
| DEC-005 | 2026-07-26 | Deploy Render + Vercel + Neon | R3 | ADR-006 |
| DEC-006 | 2026-07-26 | Đội 4 người: gộp DevOps vào R3, Eval vào R2, Deliverables vào R4, PM vào R1 | Cả đội | Xem `TEAM.md` §1 |
| DEC-007 | 2026-07-26 | Thêm cơ chế `overridden_by` cho clinical_rules | R2 | Bối cảnh: ADA (protein 15-20%E) xung đột KDIGO (0.6-0.8 g/kg) ở bệnh nhân ĐTĐ+CKD. Phương án: (A) để cơ chế conflict đẩy sang chuyên gia, (B) rule precedence. Chọn B vì ĐTĐ+CKD quá phổ biến, phương án A làm hỏng trải nghiệm. Hệ quả: giữ nguyên cơ chế conflict làm lưới an toàn cho trường hợp chưa lường trước |
| DEC-008 | 2026-07-26 | Không điền sẵn số liệu dinh dưỡng vào seed, để trống chờ tra nguồn thật | R2 | Bối cảnh: có thể sinh nhanh 152×10 con số trông hợp lý. Quyết định không làm, vì dữ liệu không truy vết được sẽ qua được cả validator lẫn mắt chuyên gia nhưng vẫn sai định mức bệnh nhân. Hệ quả: `validate_data.py` chặn merge nếu thiếu `source_ref` |
| DEC-009 | 2026-08-01 | Chọn ĐTĐ2 làm bệnh chính (anchor tim-chuyển hoá), THA + CKD sớm là comorbidity modifier | R2 | Bối cảnh: cần 1 bệnh chính cho MVP dinh dưỡng dù bệnh nhân đa bệnh. Phương án: A) làm cả 4 bệnh song song, B) anchor 1 bệnh. Chọn B/ĐTĐ2 vì: luật dinh dưỡng ĐTĐ2 tính được bằng SQL hợp RULE-1 nhất, ĐTĐ2 là hub kéo theo THA/CKD, dataset & guideline phong phú nhất, và purine (cột khó nguồn nhất) không cần cho anchor. Hệ quả: DAT-07 mở rộng schema cho đường tự do + GI |
| DEC-010 | 2026-08-01 | GI có nguồn riêng (`gi_source`/`gi_source_ref`), tách khỏi `source_ref` của NIN | R2 | Bối cảnh: GI đến từ Atkinson 2021 / Mai 2001, khác nguồn kcal (NIN). Dùng chung 1 source_ref là vi phạm tinh thần RULE-2. Hệ quả: model + validate_data chặn `gi_index` không có nguồn GI; `glycemic_load` None-safe để menu engine suy giảm mềm khi thiếu GI |
| DEC-011 | 2026-07-27 | Dockerfile cài dependency system-wide thay vì `pip install --user` | R3 (SET-04) | Bối cảnh: image 2-stage copy `/root/.local` từ builder sang runtime rồi chạy bằng `appuser` không phải root; `/root` có mode 0700 nên `appuser` không traverse được dù đã `chown -R` các file bên trong → container luôn crash `Permission denied` khi khởi động, kể cả khi build thành công. Phương án cân nhắc: (A) `chmod o+x /root` — mở quyền lên thư mục home của root, chấp nhận được vì rỗng nhưng vẫn xấu; (B) cài system-wide (bỏ `--user`), copy `/usr/local/lib/python3.11/site-packages` + `/usr/local/bin`. Chọn B vì không cần nới quyền `/root`. Hệ quả: `docker build` xanh không đủ để coi là "deploy được" — phải thực sự chạy container và gọi healthcheck (đã làm khi verify SET-04). *(đổi số từ DEC-009 khi merge develop→main để tránh trùng)* |
| DEC-013 | 2026-08-03 | Không dùng số per-món của API NIN cho dishes; phân rã nguyên liệu (DAT-04 gốc) | R2 | Bối cảnh: API món ăn NIN có kcal/muối per-100g dao động phi lý (phở 276–826 kcal/100g, muối 0,01–6,7 g/100g). Phương án: A) seed dishes.csv từ NIN, B) phân rã món → nguyên liệu → tính SQL từ food_items. Chọn B vì số món NIN không đáng tin cho ngưỡng lâm sàng; food_items có nguồn NIN/USDA truy được. Hệ quả: test hồi quy muối (phở 3,3–4,0g/bát) tính từ nguyên liệu + khẩu phần (serving_sizes.csv) |
| DEC-012 | 2026-08-02 | `purine_mg` thành optional (None) trong FoodItem/NutritionSummary | R2 | Bối cảnh: điền food_items từ NIN nhưng NIN (và USDA) KHÔNG có purine; purine chỉ cần cho gout. Phương án: A) tìm nguồn purine riêng cho cả 152 món rồi mới điền, B) purine optional + None-aware giống sugar/gi. Chọn B: gỡ được đường găng DAT-02 ngay, purine bổ sung sau từ nguồn riêng (bảng purine Nhật). Hệ quả: compute_nutrition cộng purine None-aware + cờ `purine_is_complete`; validator sinh cảnh báo `incomplete_data` cho ca gout khi thiếu → an toàn không bị đánh lừa bởi tổng thiếu hụt |
| DEC-014 | 2026-08-05 | Giữ nguyên `compute_targets()`/DEC-007 (chỉ gắn `needs_expert_review` khi rule xung đột) dù PRD v2.1 §2.2 đọc thoáng qua có vẻ yêu cầu gắn cờ cho MỌI ca đồng mắc ngoài ĐTĐ2 | Hưng (xác nhận) | Bối cảnh: PRD v2.1 (Phương) thu hẹp trọng tâm MVP về ĐTĐ2, §2.2 dễ đọc thành "mọi bệnh đồng mắc → bắt buộc chuyên gia duyệt", ngược DEC-007. Phương án cân nhắc: A) sửa code theo nghĩa đen PRD mới; B) chỉ flag khi thật sự không xác định được ngưỡng an toàn (giữ DEC-007); C) hỏi R2 trước. Đã research `KeHoachDuAn_VNutriCare_VMEC10_v3.docx` (nguồn yêu cầu chính của chính PRD.md) mục 6.4.1 "Bốn tình huống kiểm chứng" — đặc tả gốc khớp chính xác hành vi hiện tại, kể cả ca ĐTĐ2+CKD chỉ chuyển chuyên gia khi dải ngưỡng hẹp bằng 0. `docs/NGHIEN_CUU_DAI_THAO_DUONG_2026.md` xác nhận cơ chế này là điểm khác biệt cạnh tranh. Chọn B. Hệ quả: không đổi code/test; sửa lại các note đã lỡ ghi "cần sửa code" trong `CLAUDE.md`/`TICKETS.md`/`docs/rules/10-clinical-safety.md` cho khớp kết luận |

**Mẫu ghi quyết định mới:**

```markdown
| DEC-0XX | YYYY-MM-DD | <quyết định 1 dòng> | <ai> | Bối cảnh: … · Phương án cân nhắc: A/B/C · Chọn B vì … · Hệ quả: … |
```

---

## 4. Sự cố & bài học

| ID | Ngày | Sự cố | Tác động | Nguyên nhân gốc | Đã làm gì | Phòng ngừa |
|---|---|---|---|---|---|---|
| | | | | | | |

*(Ghi cả sự cố nhỏ: CI hỏng 2 tiếng, mất 1 buổi vì merge conflict, LLM ngốn hết credit… Đây là nguyên liệu tốt nhất cho slide "Challenges & Learnings".)*

---

## 5. Tổng kết tuần

### Tuần 1 (27/07 – 02/08) — Nền móng & Dữ liệu
- **Mục tiêu:** Repo + CI + Live URL hello-world + 150 thực phẩm + DEVLOG chạy
- **Hoàn thành:**
- **Chưa xong:**
- **Chỉ số:** ticket đóng __/10 · commit __ · test __ · coverage __%
- **Bài học:**
- **Điều chỉnh cho tuần sau:**

### Tuần 2 (03/08 – 09/08) — Clinical Engine
- **Mục tiêu:** API định mức đúng cho 4 bệnh lý + auth 2 role + schema DB
- **Hoàn thành:**
- **Chưa xong:**
- **Chỉ số:**
- **Bài học:**

### Tuần 3 (10/08 – 16/08) — Agent & Guardrails
- **Mục tiêu:** Sinh thực đơn pass validator ≥70% lần đầu + chặn chỉ định y khoa ≥95%
- **Hoàn thành:**
- **Chưa xong:**
- **Chỉ số:**
- **Bài học:**

### Tuần 4 (17/08 – 23/08) — HITL & Nhật ký
- **Mục tiêu:** Demo end-to-end 2 tài khoản trên Live URL
- **Hoàn thành:**
- **Chưa xong:**
- **Chỉ số:**
- **Bài học:**

### Tuần 5 (24/08 – 30/08) — Nâng cao
- **Mục tiêu:** Mâm cơm gia đình + tương tác thuốc + thực đơn 7 ngày
- **Hoàn thành:**
- **Chưa xong:**
- **Chỉ số:**
- **Bài học:**

### Tuần 6 (31/08 – 06/09) — Đóng gói
- **Mục tiêu:** Eval report + video + pitch + 10/10 deliverables
- **Hoàn thành:**
- **Chưa xong:**
- **Chỉ số:**
- **Bài học:**

---

## 6. Theo dõi Deliverables

| # | Deliverable | Owner | Trạng thái | Vị trí | Ghi chú |
|---|---|---|---|---|---|
| 1 | Source Code | R1 | ⬜ | `src/` | |
| 2 | README.md | R4 | ⬜ | `README.md` | |
| 3 | Architecture Diagram | R1 | ⬜ | `docs/architecture_diagram.md` | |
| 4 | AI Logs | R3 | ⬜ | `.ai-log/` + LangSmith | Xong ngay tuần 1 nhờ hooks |
| 5 | Live URL | R3 | ⬜ | Render + Vercel | Deploy từ tuần 1 |
| 6 | Video Demo | R4 | ⬜ | YouTube unlisted | Hiếm đội có → ưu tiên |
| 7 | Pitch Deck | R4 | ⬜ | `presentation/` | |
| 8 | Development Journal | Cả đội | 🟡 | **file này** §2, §5 | Đang chạy |
| 9 | Worklog | R1 | 🟡 | **file này** + `docs/worklog.md` | `git log` xuất cuối kỳ |
| 10 | Evaluation Evidence | R2 | ⬜ | `eval/results/report.md` | Hiếm đội có → ưu tiên |

Trạng thái: ⬜ chưa bắt đầu · 🟡 đang làm · ✅ xong

---

## 7. Theo dõi chỉ số

| Tuần | Ticket đóng | Commit | Test | Coverage | Chi phí LLM | Live URL | Ghi chú |
|---|---|---|---|---|---|---|---|
| W1 | | | | | | | |
| W2 | | | | | | | |
| W3 | | | | | | | |
| W4 | | | | | | | |
| W5 | | | | | | | |
| W6 | | | | | | | |

---

## 8. Xuất worklog cuối kỳ

```bash
git log --oneline --date=short --pretty=format:'%ad | %an | %s' --since="2026-07-27" > docs/worklog.md
```
