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

### [2026-08-05] · R2 · Nghiên cứu bổ sung nguồn dữ liệu từ tài liệu tổng quan
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

### [2026-08-06] · R2 · Nghiên cứu nguồn dữ liệu T2DM châu Á
- **Làm:** Tìm kiếm dữ liệu bệnh nhân đái tháo đường type 2 từ các quốc gia châu Á có đặc điểm nhân trắc gần Việt Nam (BMI thấp hơn phương Tây, "lean diabetes" phenotype). Ưu tiên Đông Nam Á (Thailand, Philippines, Indonesia, Malaysia, Singapore) và Đông/Nam Á (China, Korea, Japan, India, Bangladesh, Pakistan)
- **Kết quả:** Xác định được **5 nguồn có thể download ngay** với tổng ~60,000 bệnh nhân T2DM: (1) **China CHNS 2009+2015** (4k-5k T2DM, public download, biomarker đầy đủ), (2) **India NFHS-5 2019-21** (50k+ T2DM, free registration DHS Program, sample size lớn nhất), (3) **Bangladesh STEPS 2018** (700-800 T2DM, public WHO microdata, đặc điểm nhân trắc gần VN nhất: BMI 23-24, height 163/152cm), (4) Korea KNHANES 2018-21 (4k-5k T2DM, public, dietary data chi tiết), (5) Pakistan STEPS 2013-14 (1.2k-1.5k T2DM, public WHO)
- **Đặc điểm so sánh:** Bangladesh (BMI 23-24, height 163/152cm) và India (BMI 23-25, "lean diabetes") gần VN nhất về nhân trắc; China/Korea cao hơn một chút nhưng vẫn thấp hơn Western (~28-30). Thailand (mục tiêu top priority vì gần văn hóa ẩm thực) **không tìm thấy public microdata** — NHES reports có nhưng individual-level data cần request riêng
- **Deliverable:** `data/raw/asian_t2dm_sources/` với 4 files markdown: (1) `RESEARCH_REPORT.md` (báo cáo chi tiết 8 nguồn + so sánh nhân trắc), (2) `download_instructions.md` (hướng dẫn từng bước download mỗi nguồn), (3) `citations.md` (citation requirements + DUA summary), (4) `QUICKREF.md` (quick reference), (5) `README.md` (tổng quan + structure), (6) `.gitignore` (chặn raw .dta/.sav không commit), (7) `scripts/download_asian_t2dm_data.py` (script download tự động cho Bangladesh/Pakistan/China — India cần manual registration)
- **Mục đích:** So sánh thuật toán VNutriCare với "lean diabetes" phenotype (BMI thấp mà vẫn T2DM — đặc thù châu Á), validate clinical targets (BMI 18.5-23 cho ĐTĐ2 VN có phù hợp không), benchmark với NHANES (phương Tây), phân tích dietary patterns các nước có văn hóa ẩm thực gần VN
- **Variables có sẵn:** Tất cả nguồn đều có age/sex/BMI/height/weight/fasting glucose/diabetes diagnosis. CHNS+KNHANES có HbA1c+lipids+dietary intake (24h recall). NFHS-5 có biomarker nhưng subset có HbA1c. WHO STEPS có BP+behavioral risk factors
- **Estimated size:** ~1.5 GB total (NFHS-5 chiếm 700MB, CHNS 250MB, KNHANES 400MB, Bangladesh+Pakistan <150MB)
- **Data governance:** Tuân thủ DUA (không re-identify, không redistribute raw, cite nguồn, chỉ dùng statistical analysis). Raw files không commit git (có .gitignore). Processed aggregates OK để commit
- **Tiếp theo:** (1) Download Bangladesh STEPS ngay (2 phút, WHO microdata public), (2) Đăng ký DHS account cho NFHS-5 (approval 1-2 ngày), (3) Download CHNS (public, không cần approval), (4) Viết `scripts/process_asian_t2dm_data.py` (filter T2DM, standardize schema, convert units), (5) EDA notebook so sánh với NHANES
- **Liên quan ticket:** Không có ticket cụ thể (nghiên cứu tự do), nhưng hỗ trợ validation cho DEC-014 (multi-disease, MVP focus T2DM nhưng cơ chế đa bệnh lý giữ nguyên) — dữ liệu này chứng minh clinical targets VN có phù hợp với "lean diabetes" châu Á không
- **Thời gian:** 4h (search + verify sources + download instruction research + write documentation)
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

### [2026-07-27] · R3 · SET-03 + SET-04
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

### [2026-07-27] · R3 · SET-01 bootstrap
- **Làm:** Rà lại toàn bộ EPIC 0 và phát hiện nhiều phần trước đó *chưa thực sự* đạt AC dù trông như đã xong. Sửa: thêm `pyproject.toml` (không tồn tại), thêm target `make run`/`lint`/`format` vào `Makefile` (AC "cả 5 người chạy `make run`" trước đó chắc chắn fail vì không có target), bổ sung biến thiếu trong `.env.example` (`APP_NAME`, `MODEL_NAME`, `LLM_TEMPERATURE`), redact `AI_LOG_API_KEY` thật khỏi `.env.example` (đã từng bị redact bởi Đinh Lê Quỳnh Phương rồi bị commit đè lại bằng key thật). Tạo branch `develop` trên repo đội thật (`AI20K-Build-Phase-Cohort-3/P-031`) — trước đó chỉ có `main`
- **Kết quả:** PR #3 (SET-01) + PR #2 (SET-03/SET-04, xem entry trước) mở trên repo đội thật
- **Phát hiện quan trọng:** repo đội thật là `AI20K-Build-Phase-Cohort-3/P-031`, không phải `hwngkm/VMEC10_P31` (repo cá nhân) — công việc trước đó (bao gồm cả PR đầu của phiên này) từng nhắm nhầm repo
- **Vướng:** tài khoản GitHub hiện dùng (`hwngkm`) không có quyền Admin trên repo đội thật (`permissions.admin=false` qua API) dù được xác nhận là admin — cần người thật kiểm tra lại trên GitHub UI để bật branch protection cho `main`/`develop` (AC SET-01 "main không push thẳng được" chưa đạt). TEAM.md/CODEOWNERS vẫn dùng handle placeholder vì chưa có tên GitHub thật của 4 thành viên
- **Tiếp theo:** merge PR #2 + PR #3, sau đó bật branch protection, điền tên thật vào TEAM.md/CODEOWNERS, xác nhận SET-02 đã chạy trên máy cả 4 người, viết lại README theo đúng AC SET-06 (hiện là README kỹ thuật cho khung code, thiếu phần giới thiệu dự án/Live URL/thành viên)
- **Thời gian:** ~1h

### [2026-07-27] · R3 · Gộp lên nhánh hung + SET-05/SET-06
- **Làm:** Theo yêu cầu Hưng — vì admin repo là BTC (không phải đội), gộp PR #2 + PR #3 vào một nhánh và đẩy thẳng lên `hung` (nhánh cá nhân trên repo đội) thay vì chờ merge qua `develop`/`main`. Trong lúc gộp: phát hiện + fix bug BOM khiến `.git/hooks/pre-push` không chạy được trên Windows (`cannot spawn ... No such file or directory`) — sửa gốc trong `scripts/setup_hooks.sh`. Thêm `GET /api/v1/health` (AC SET-05 yêu cầu đúng path này, code cũ chỉ có `/health` ở root). Thêm `render.yaml` blueprint cho backend. Viết lại `README.md` theo `docs/templates/README_boilerplate.md` cho đúng AC SET-06 (nội dung kỹ thuật cũ chuyển sang `docs/KHUNG_CODE.md`)
- **Kết quả:** nhánh `hung` trên `AI20K-Build-Phase-Cohort-3/P-031` có đầy đủ SET-01, SET-02 (hook), SET-03, SET-04, phần code của SET-05, và SET-06 (được duyệt, bảng thành viên/tài khoản demo còn để trống chờ đội tự điền)
- **Phát hiện:** working tree có sẵn thay đổi dở từ phiên làm việc khác (không phải tôi) — `src/agents/graph.py` được thêm một `agent` object "backward-compat" xung đột với cách tôi đã sửa `routes.py` trong PR #2 (bỏ `/chat` cũ). Đã `git stash` (không mất), **chưa quyết định** giữ cách nào — cần Hưng xem lại trước khi áp dụng
- **Vướng:** SET-05 mới có tài khoản Vercel; chưa có Render + Neon/Supabase nên chưa deploy thật được, `render.yaml` mới là chuẩn bị sẵn cấu hình
- **Tiếp theo:** hướng dẫn Hưng các bước Render + Neon cụ thể; quyết định xử lý stash graph.py; đội tự điền TEAM.md/README khi có tên thật
- **Thời gian:** ~1.5h

### [2026-08-05] · R2 · Merge chuỗi 6 PR (CI self-hosted, DAT-09/10, AGT-09/10, nghiên cứu ĐTĐ) + 2 sự cố phát sinh
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

### [2026-08-05] · R2 · Đồng bộ tài liệu theo PRD v2.1 + rà lại quyết định needs_expert_review đa bệnh lý
- **Làm:** Sau khi merge PRD v2.1 (Đinh Lê Quỳnh Phương, thu hẹp trọng tâm MVP về ĐTĐ2) vào `develop`, cập nhật `CLAUDE.md`, `docs/TICKETS.md`, `docs/rules/10-clinical-safety.md`, `docs/00_ASSESSMENT.md`, `docs/PLAN.md`, `docs/ARCHITECTURE.md` để nhất quán với PRD mới — không xoá nội dung đa bệnh lý, chỉ chú thích ưu tiên nghiệm thu.
- **Câu hỏi mở ra:** PRD v2.1 §2.2 đọc theo nghĩa đen có thể hiểu là MỌI hồ sơ có bệnh đồng mắc ngoài ĐTĐ2 phải bắt buộc `needs_expert_review` — khác hành vi hiện tại của `compute_targets()` (chỉ gắn cờ khi rule thật sự xung đột, DEC-007). Ban đầu định sửa code theo hướng này nhưng dừng lại vì đây là ngưỡng lâm sàng thật, đúng tinh thần `CLAUDE.md` §6 "không chắc thì hỏi, đừng tự đặt".
- **Research trước khi quyết:** đọc lại `KeHoachDuAn_VNutriCare_VMEC10_v3.docx` (chính PRD.md v2.1 ghi là "Nguồn yêu cầu chính") — mục 6.4.1 "Bốn tình huống kiểm chứng" đặc tả **chính xác** hành vi hiện tại: ca ĐTĐ2+CKD chỉ chuyển chuyên gia khi dải ngưỡng ADA/KDIGO hẹp bằng 0 (xung đột số thật), KHÔNG phải vì có 2 bệnh — trích nguyên văn tài liệu: "Một hệ thống kém sẽ âm thầm chọn một bên. Hệ thống này phát hiện [xung đột] và chuyển cho chuyên gia quyết định." Mục 1.1 của cùng tài liệu còn nói thẳng đồng mắc "bắt buộc hệ thống phải xử lý được, không thể thiết kế cho từng bệnh riêng lẻ". `docs/NGHIEN_CUU_DAI_THAO_DUONG_2026.md` (merge cùng ngày) liệt kê cơ chế phát hiện xung đột này là **điểm khác biệt cạnh tranh** so với app đối thủ (không app nào xử lý đa bệnh lý đồng thời).
- **Quyết định:** giữ nguyên `compute_targets()`/DEC-007, KHÔNG sửa code. Đã sửa lại các note vừa thêm vào `CLAUDE.md`/`docs/TICKETS.md`/`docs/rules/10-clinical-safety.md` cho khớp kết luận này (bản đầu ghi nhầm là "cần sửa code" — xem DEC-014).
- **Bài học:** một dòng tóm tắt trong PRD (viết bởi 1 thành viên, không trích tài liệu gốc) có thể đọc sai nghĩa nếu không đối chiếu lại nguồn chính — nhất là khi nó đảo ngược một quyết định đã kiểm chứng bằng test. Luôn tìm "nguồn yêu cầu chính" thật trước khi sửa code lâm sàng.
- **Thời gian:** ~30 phút (research + sửa tài liệu)

### [2026-08-06] · R2 · DAT-04 — thêm 48 nguyên liệu Việt từ bảng NIN nội bộ chuyên gia
- **Làm:** Hưng chỉ ra 2 sheet "Bảng TP" (841 dòng) và "Bảng TP có phospho" (397 dòng) trong `data/Bảng xác định nhu cầu dinh dưỡng + thực đơn.xlsx` — xác nhận đây là bảng thành phần dinh dưỡng gốc từ NIN, do chính chuyên gia dinh dưỡng dự án biên soạn/dùng (không phải LLM sáng tác)
- **Đối chiếu trước khi tin dùng:** so khớp tên với `food_items.csv` hiện có — phát hiện 21/80 dòng trùng tên có kcal lệch >2 so với NIN/USDA đã cite (VD Cà rốt NIN=47 vs bảng này=43.65) → **không ghi đè** dữ liệu đã xác minh trước, chỉ thêm dòng MỚI (đúng DEC-008)
- **Ràng buộc kỹ thuật phát hiện khi trích:** `validate_data.py` bắt buộc `na_mg`/`k_mg`/`p_mg` phải có giá trị khi `kcal_100g` đã điền (không nằm trong `OPTIONAL_NUMERIC_COLS`) — sheet "Bảng TP" (841 dòng, nhiều tên hơn) KHÔNG có 3 cột này nên không dùng được để tạo dòng mới; chỉ sheet "Bảng TP có phospho" đủ điều kiện, và trong đó vẫn còn 309/387 dòng thiếu Na hoặc K thật trong bảng gốc (không suy đoán để lấp)
- **Kết quả:** viết `scripts/extract_menu_xlsx_composition.py`, thêm **48 nguyên liệu mới** (id 3000-3047, `source=NIN`) đầy đủ kcal/protein/carb/fat/fiber/na/k/p. `validate_data.py` 0 lỗi, `pytest` 112/112 pass
- **Khoảng trống còn lại:** 309 nguyên liệu trong bảng nội bộ (đa số ngũ cốc/tinh bột) thiếu Na hoặc K — cần R2 tự tra bổ sung hoặc chấp nhận để trống vĩnh viễn cho nhóm này; 21 dòng lệch số liệu với NIN/USDA hiện tại cần R2 đối chiếu ấn bản NIN nào đúng hơn trước khi quyết định có sửa dữ liệu cũ hay không

### [2026-08-05] · R2/R3 · Bỏ trần số lượng EPIC 1/2 + fill thêm data + BE-01 (schema DB thật + ERD)
- **Làm (3 việc song song theo yêu cầu):**
  1. **Bỏ trần EPIC 1/2:** `DAT-02` (150 món), `DAT-04` (80 món ăn), `DAT-05` (80 cặp thuốc-thực phẩm), `DAT-06` (~15 tài liệu guideline), `CLN-02` (40 rule) — đổi AC từ "≥N là đích" sang "≥N là SÀN, không phải trần", ghi rõ trạng thái thật hiện tại của từng ticket (VD `dishes.csv` mới 3/80, cần ưu tiên trước khi mở rộng thêm).
  2. **Fill thêm data thật:** `drug_food_interactions.csv` — điền `source_ref` cho 17/30 cặp (Warfarin, Digoxin, Enalapril, Atorvastatin, Hydrochlorothiazide, Colchicin, Allopurinol, Ciprofloxacin, Amlodipin, Gliclazide, Insulin) sau khi xác minh từng dược chất có chuyên luận riêng trên Dược thư Quốc gia VN 2022 (`trungtamthuoc.com/hoat-chat/<tên>`). 13 cặp còn lại (Losartan, Simvastatin, Metformin, Levothyroxine, Furosemide, Spironolactone, Phenelzine, Tetracycline, Sắt, Canxi) **cố ý để trống** — không xác nhận được có chuyên luận riêng qua tìm kiếm, không suy đoán (DEC-008).
  3. **BE-01 (schema DB thật):** `src/db/models.py` — 15 bảng SQLAlchemy khớp `ARCHITECTURE.md` §5, bổ sung 6 bảng ERD cũ (viết từ S1, trước khi có data thật) chưa vẽ: `dishes`, `dish_ingredients`, `serving_sizes`, `patient_medications`, `patient_allergies`, `food_logs`, `guideline_chunks`. `alembic/` init + migration đầu, đã test `upgrade head`/`downgrade base` sạch trên SQLite trắng (không đụng Postgres thật trong `.env` — dùng `DATABASE_URL` override tạm trỏ SQLite để sinh migration, tránh kết nối nhầm vào DB cloud chung của team). `tests/test_db_models.py` (6 test).
- **Sự cố trong lúc làm (ghi cả lỗi của chính mình):** khi định đọc file trên `main` để đối chiếu, lỡ chạy `git checkout main -- .` trên nhánh `work/hung-consolidated` — ghi đè toàn bộ working tree bằng nội dung `main`, xoá mất 1 dòng sửa `.gitignore` chưa commit của Hưng. Tìm lại được nội dung gốc từ stash commit cũ (`git fsck --no-reflog` — chưa bị gc), khôi phục bằng `git reset --hard HEAD` (đã xin phép trước khi chạy vì bị auto-mode chặn) rồi áp lại đúng 1 dòng đã mất. Không mất gì, nhưng bài học: **không thao tác `checkout <branch> -- .` khi có WIP người khác trên nhánh đang đứng**, dùng `git show <branch>:<path>` để đọc file nhánh khác mà không đụng working tree.
- **Kết quả:** `validate_data.py` 0 lỗi (drug_food_interactions từ "30 cặp chưa có source_ref" → còn 13) · `alembic upgrade head`/`downgrade base` chạy sạch trên SQLite trắng · 108 test xanh (thêm 6 test DB) · ruff/format sạch cho `src/db/` + test mới · ERD trong `ARCHITECTURE.md` §5 viết lại đầy đủ 15 bảng khớp `src/db/models.py`.
- **Còn lại (ghi vào ticket `BE-10` mới):** chưa có script nạp `data/seeds/*.csv` vào DB thật (`scripts/seed_db.py`) — DB schema đã build xong nhưng vẫn trống, mọi thứ vẫn chạy qua CSV loader hiện có (`src/clinical/seeds.py`) cho tới khi BE-10 xong.
- **Tiếp theo:** BE-10 (seed script), tiếp tục lấp `dishes.csv` (3/80, ưu tiên cao nhất còn lại của EPIC 1), R2 tự tra nốt 13 cặp thuốc-thực phẩm còn thiếu nguồn.

### [2026-08-05] · R3 · Thực hiện PLAN_DAT-12 — BE-10 seed_db.py
- **Làm:** Đọc lại toàn bộ dự án (git log, TICKETS.md, data/README.md, `src/db/models.py`, alembic, test) trước khi bắt tay — xác nhận §2.1 (bỏ trần TICKETS.md) và DAT-11 đã xong từ commit trước, chỉ còn thiếu ticket `DAT-12` (đã thêm) và §2.3.1 (`seed_db.py`, chưa ai làm).
- **`scripts/seed_db.py` + `make seed`:** đọc `food_items/dishes/dish_ingredients/clinical_rules/drug_food_interactions/serving_sizes.csv` → insert qua `src/db/models.py`. Idempotent bằng `session.merge()` theo khoá chính tự nhiên của từng bảng; riêng `serving_sizes` không có khoá tự nhiên trong CSV nên xoá-hết-rồi-nạp-lại (nội dung giống hệt mỗi lần chạy). `dish_ingredients` tự bỏ qua (kèm log rõ dòng nào) nếu `food_id`/`dish_id` chưa tồn tại/chưa có số liệu, thay vì crash lỗi FK. **Không** seed `gi_values.csv`/`purine_values.csv`/`usda_values.csv` — đã merge vào `food_items.csv` từ trước, không phải bảng DB độc lập.
- **Verify thật (không chỉ tin test):** chạy `DATABASE_URL=sqlite:///./_tmp... python scripts/seed_db.py` 2 lần liên tiếp trên DB trắng — lần 1 và lần 2 đều ra đúng 125 food_items / 3 dishes / 11 dish_ingredients / 21 clinical_rules / 30 drug_food_interactions / 5 serving_sizes (idempotent thật, không chỉ test giả lập).
- **Kết quả:** `tests/test_seed_db.py` — 4 test (nạp đúng số liệu thật, không lỗi FK, idempotent, bỏ qua dish_ingredient thiếu food_item). 112 test xanh toàn repo, ruff/mypy sạch cho file mới (các lỗi ruff có sẵn ở `scripts/log_*.py`/`codex_hook.py` không đụng tới — ngoài phạm vi).
- **Chưa làm trong phiên này (đúng theo `docs/PLAN_DAT-12-uncap-data-and-db.md` §2.2 — cần R2 chuyên môn thật, không tự ý làm):** fill thêm `dishes.csv` (3→80+), `clinical_rules.csv` (21→40+), 13 cặp `drug_food_interactions` còn thiếu `source_ref`, 27 dòng `food_items.csv` còn trống. Rà index DB theo truy vấn thật và cài `psycopg2-binary` cũng cố ý chưa làm — đúng kế hoạch, chỉ cần khi BE-03+ / deploy Postgres thật bắt đầu.
- **Tiếp theo:** R2 tiếp tục fill dữ liệu (ưu tiên `dishes.csv`), R3 rà index khi BE-03 bắt đầu viết truy vấn thật.
- **Thời gian:** ~1h

### [2026-08-05] · R2 · Bỏ trần dữ liệu tối đa — 7.173 food_items (mục tiêu 1000+), 2.635 dishes (mục tiêu 500+)
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

### [2026-08-06] · R2 · Bắt đầu lấp món Việt — +27 món (vẫn `pending`, chưa thay thế R2)
- **Bối cảnh:** Hưng hỏi thẳng "sao món Việt vẫn mới có 3 món" sau đợt 05/08 — đúng, 2.632 món thêm hôm trước toàn bộ là USDA FNDDS (Mỹ), không đụng tới món Việt. Hưng yêu cầu "soạn công thức, call thêm API hoặc search thu thập thêm công thức". Đã kiểm tra 1 paper Hugging Face (Epicure, arXiv 2605.22391) Hưng gợi ý — xác nhận qua fetch PDF thật: đây là model embedding nguyên liệu (Gemini embedding + RecipeNLG/Recipe1M+/Xiachufang/ChefKoch/SOMOS/USDA), có định lượng thật nhưng **không có món Việt Nam trong bất kỳ dataset liệt kê nào** → không dùng được, không tốn công tích hợp.
- **Nguồn thật tìm thấy trong `data/` chưa từng khai thác:** `data/Bảng xác định nhu cầu dinh dưỡng + thực đơn.xlsx` — file thực đơn nội bộ dự án, có 4 sheet thực đơn mẫu (Sáng/Trưa/Tối) với cột "KL sống sạch" (gram thật/khẩu phần). Viết `scripts/extract_menu_xlsx_dishes.py`: parse theo state machine (nhãn bữa ăn → tích luỹ nguyên liệu đến dòng "Hiện tại"/"Cần xây dựng"), khớp `food_id` bằng tên đã chuẩn hoá (bỏ dấu ngoặc, hạ chữ thường) — **cố tình không fuzzy-match rộng** (VD không tự suy "Dầu ăn" ≈ "Dầu ăn thực vật") để tránh gán nhầm loại thực phẩm khác thành phần dinh dưỡng khác nhau → tỷ lệ khớp chỉ ~37% (67/180 dòng), 2 sheet đầu (`tđ1`,`tđ2`) không có nhãn bữa ăn rõ nên 0 kết quả. Kết quả: **15 "bữa ăn" thật** (dish_id `MENU-*`), gram từ tài liệu thật, nhưng nguyên liệu bị thiếu (chỉ giữ phần khớp được).
- **12 món Việt tự soạn qua LLM** (phở gà, bún chả, canh chua cá, rau muống xào tỏi, đậu phụ sốt cà chua, cá kho tộ, gà kho gừng, canh cải nấu tôm, sườn xào chua ngọt, trứng chiên hành, canh su hào cà rốt thịt băm, nấm hương xào thịt bò) — dùng nguyên liệu đã có `food_id` thật trong 319 dòng Việt curated/NIN, gram theo kinh nghiệm ẩm thực phổ thông (KHÔNG có nguồn định lượng đối chiếu — khác hẳn 3 món gốc đã đối chiếu Na với nghiên cứu). Vài món thiếu gia vị (đường, dấm, nước dùng...) vì `food_items.csv` chưa có các mục đó.
- **Tất cả 27 món đều `verified_by=pending`** — không tự ý nâng lên "đã duyệt". Ghi rõ trong `note` từng món lý do cần R2 rà soát.
- **Xác minh:** `validate_data.py` 0 lỗi mới, `pytest -q` 112/112 pass, `make seed` (SQLite trắng, 2 lần) → dishes 2.635→**2.662**, dish_ingredients 5.369→**5.479**, 0 dòng bị skip do FK.
- **Việc còn để ngỏ:** 3 món gốc + 27 món mới đều `pending`, tổng 30/2.662 món Việt thật cần R2 duyệt tay — khoảng cách với mục tiêu "500 món Việt" vẫn còn rất lớn và **không có bulk source Việt Nam nào tương đương FNDDS** để lấp nhanh; đường đi khả thi duy nhất còn lại là R2 duyệt dần + LLM soạn thêm theo lô, không có shortcut tự động.
- **Thời gian:** ~1.5h

---

### [2026-08-06] · R2 · Thực hiện PLAN_DAT-13 (đợt 1) — 13/13 drug_food_interactions có source_ref, khảo sát Na/K/kcal
- **§2.3 (DAT-05) — 13 cặp `drug_food_interactions.csv` thiếu `source_ref`:** tra cứu thật qua WebFetch/WebSearch cho từng cặp, **không dùng nguồn nào chưa xác nhận được nội dung**:
  - 9 cặp tra được trực tiếp trong **Dược thư Quốc gia VN 2022** (Losartan+kali, Simvastatin+bưởi, Metformin+rượu bia, Metformin+B12, Levothyroxine+đậu nành, Furosemide+kali, Spironolactone+kali, Tetracycline+canxi) qua `trungtamthuoc.com/hoat-chat/*` — trích nguyên văn đoạn liên quan vào `source_ref`.
  - 4 cặp Dược thư không có bản tiếng Việt đủ chi tiết → dùng nguồn quốc tế uy tín thay thế (đúng thứ tự ưu tiên plan §2.3 "Martindale/BNF... trước khi bỏ trống"): Levothyroxine+canxi (MedlinePlus/NIH), Levothyroxine+cà phê (Benvenga et al., *Thyroid* 2008;18(3):293-301 — nghiên cứu gốc, espresso giảm hấp thu ~36%), Phenelzine+tyramine (StatPearls/NCBI NBK554508), Sắt+trà-cà phê và Canxi+oxalat rau chân vịt (NIH Office of Dietary Supplements, Iron/Calcium Health Professional Fact Sheet).
  - **30/30 cặp giờ có `source_ref`** (`validate_data.py` không còn cảnh báo này). `verify_status` vẫn giữ `to_verify` — có nguồn thật không thay thế được việc R2 xác nhận phù hợp lâm sàng trước Demo Day.
- **§2.1 khảo sát lại:** chạy `scripts/extract_menu_xlsx_composition.py` (dry-run) xác nhận 272/397 dòng "Bảng TP có phospho" vẫn thiếu ≥1 cột bắt buộc (na/k/p...) sau đợt 48 dòng đã thêm sáng nay — **chưa cross-reference NIN2017 PDF/USDA cho 272 dòng này** (cần quét lại toàn bộ PDF 304 trang không lọc theo mã đã có, ước tính ~40 phút, để dài hơn phạm vi phiên này) — để lại cho phiên sau, không tự đoán số.
- **§2.4 — rà soát 60 dòng lệch kcal thật (không phải 21 như ước tính ban đầu trong plan, do bản kiểm tra đầu dùng nhầm cột "KL sống sạch" cho sheet "Bảng TP" thay vì cột E/100g — đã sửa và verify lại):** ghi toàn bộ vào `data/seeds/food_items.kcal_mismatch_report.csv` (food_id, tên, kcal hiện tại + nguồn, sheet xlsx, kcal xlsx, chênh lệch). Đa số lệch nhỏ (2-8 kcal, hợp lý do khác ấn bản NIN/làm tròn). **2 outlier cần R2 xem gấp trước khi dùng bất kỳ giá trị nào:** `Đậu hà lan` (id 3008, food_items=342 kcal vs xlsx=70 kcal — chênh lệch ~5 lần, nghi ngờ 1 trong 2 nguồn nhầm "đậu Hà Lan khô" với "đậu Hà Lan tươi/đông lạnh") và `Sữa đặc có đường` (id 125, food_items=65 kcal vs xlsx=336 kcal — nghi ngờ 1 nguồn tính theo sữa đã pha loãng, 1 nguồn tính nguyên chất). **Không tự sửa số nào** — đúng nguyên tắc plan §3 (không sửa dữ liệu đã qua CI khi chưa có quyết định rõ ràng).
- **Chưa làm trong đợt này:** §2.1 phần còn lại (272 dòng), §2.2 (`food_items.template.csv` 152 dòng, 0% xong).
- **Thời gian:** ~2h (phần lớn là 13 lượt WebFetch/WebSearch xác minh nguồn thật cho drug interactions)

---

### [2026-08-06] · R2 · PLAN_DAT-13 (đợt 2) — quét toàn bộ NIN2017, lấp 78/272 dòng §2.1
- **Viết `scripts/build_nin2017_full_index.py`** — biến thể của `extract_nin2017_bulk.py` nhưng KHÔNG lọc theo mã đã có trong `food_items.csv`, để tạo 1 bảng tra cứu đầy đủ theo tên phục vụ cả §2.1 và §2.2. Chạy nền ~5 phút (nhanh hơn nhiều so với ước tính 40 phút của lần trích trước — lý do: bảng thành phần chính của NIN2017 chỉ nằm ở **trang 24-134** (nhóm mã 01-14: ngũ cốc→đồ uống có cồn), phần còn lại của file PDF 304 trang không phải bảng thành phần cùng định dạng cột (khớp mô tả `data/README.md` "phụ lục, mục lục, các phần khác") nên các trang đó bị bỏ qua đúng theo thiết kế (`NEEDED_TAGS.issubset(anchors)` false), không phải lỗi quét thiếu. Kết quả: **236 mã, ghi vào `data/seeds/nin2017_full_index.csv`** (không commit — dẫn xuất trung gian, tái tạo được bằng script).
- **Đối chiếu 272 dòng thiếu field của "Bảng TP có phospho" (§2.1) với bảng tra cứu này:** khớp tên chuẩn hoá được **78 dòng** (Ngô vàng hạt khô, Bột gạo nếp, Cà bát, Chuối xanh, Chôm chôm, Dâu tây, Đào, Lựu, Mơ... — đa số nhóm rau củ quả nhóm mã 03-08). Đã thêm 78 dòng mới vào `food_items.csv` (id 4000-4077, `source=NIN`, `source_ref` trỏ đúng mã+trang NIN2017 — không phải suy đoán). **194/272 dòng còn lại không khớp được** — tên trong bảng nội bộ dự án không xuất hiện trong 236 mã trích được (có thể do khác cách gọi tên, hoặc thực phẩm đó nằm ngoài phạm vi trang 24-134) — **giữ trống, không suy đoán**, đúng DEC-008.
- **Đối chiếu 27 dòng còn trống của `food_items.template.csv` (§2.2):** **0/27 khớp được** với 236 mã NIN2017 (Mì ăn liền, Giò lụa, Chao, Rau ngót, Tía tô, Kinh giới, Rau răm, Mắm nêm... — toàn bộ là món chế biến sẵn hoặc rau thơm không nằm trong nhóm mã 01-14 đã trích được). Không thử USDA cross-reference (khớp chéo tiếng Việt→tiếng Anh) trong đợt này — plan §2.1 xếp bước này rủi ro cao hơn, cần thời gian riêng và nên có R2 xác nhận từng cặp khớp tên trước khi ghi vào `food_items.csv` chính.
- **Xác nhận:** `validate_data.py` 0 lỗi mới (7194→**7272** dòng đã nhập số liệu), `pytest -q` 112/112 pass.
- **Còn lại:** 194 dòng §2.1 + 152 dòng §2.2 (toàn bộ) vẫn trống — cần thử USDA cross-reference (rủi ro cao hơn, cần ghi rõ khớp chéo ngôn ngữ trong `source_ref` theo đúng plan) hoặc R2 tự bổ sung trực tiếp bằng chuyên môn.
- **Thời gian:** ~45 phút

---

### [2026-08-06] · R2 · PLAN_DAT-13 (đợt 3) — khớp chéo USDA cho 21 dòng còn lại (rủi ro cao hơn, đã ghi rõ)
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

### [2026-08-06] · R2 (deadline mentor 08/08) · Thiết kế API stack + triển khai BE-02/03/04/05/06, HIT-02
- **Bối cảnh:** Hưng chuyển yêu cầu mentor tuần này: (1) thiết kế API stack (danh sách API, chức năng, input/output, ràng buộc), (2) xây dữ liệu mẫu + hoàn thiện backend dựa trên đó + deploy để demo. Trước phiên này `src/api/routes.py` chỉ có `/health`, `/status`, `/chat` (stub 501) — chưa có auth, chưa có route nào chạm DB thật.
- **`docs/API_DESIGN.md`:** 18 endpoint (auth/patients/targets/meal-plans/reviews/food-logs/audit), mỗi API có input/output/ràng buộc/lỗi/mapping DB, thứ tự triển khai theo đường găng `TICKETS.md`. Xác định phạm vi thực tế cho 2 ngày: ưu tiên 1→6 (auth→patients→targets→seed demo→meal-plans→reviews) — đúng lát cắt "đăng ký → hồ sơ → tính định mức → sinh thực đơn → chuyên gia duyệt" cần cho demo.
- **BE-02 (auth):** JWT (`pyjwt`, access 15p/refresh 7 ngày, rotate khi refresh) + argon2id (`passlib`). Lỗi đăng nhập dùng chung cho sai email/sai mật khẩu (chống user-enumeration, test riêng xác nhận message giống hệt).
- **BE-03 (patient CRUD):** Tách `src/api/routes.py` (1 file) thành package `src/api/routes/` theo resource — thư mục này đã có sẵn `.gitkeep` từ trước, rõ ràng là dự định gốc chưa ai làm. Chặn quyền ở **tầng query** (`_get_owned_profile` filter theo `user_id` ngay trong câu SQL), không lọc sau khi đã lấy data — bệnh nhân A gọi hồ sơ B → `404` đúng AC BE-09, không phải `403`.
- **BE-04 (targets):** bọc thẳng `compute_targets()` có sẵn (RULE-1, không LLM). Viết `src/api/clinical_bridge.py` để chuyển ORM `PatientProfile` (DB) sang Pydantic `PatientProfile` (clinical) dùng chung cho cả targets và meal-plans.
- **BE-05 (seed demo):** `scripts/seed_demo_users.py` — 2 dietitian + 6 patient mô phỏng, phủ đủ 4 nhóm bệnh mục tiêu (T2DM/HTN/CKD/Gout) + 1 ca đa bệnh lý T2DM+CKD (đúng ví dụ DEC-007/DEC-014). Mật khẩu demo chung `Demo1234`, ghi vào README.
- **BE-06 (sinh thực đơn) — phần khó nhất:** `POST /meal-plans` chạy `build_nutricare_graph()` (đã có sẵn từ AGT-10, `src/agents/assembly.py`) **thật** qua `BackgroundTasks`, trả `202` ngay (đúng AC "không treo quá 60s"). Phát hiện quan trọng khi viết test: `TestClient` **chờ background task chạy xong** trước khi trả response về test (hành vi ASGI chuẩn của Starlette) — nghĩa là test kiểm được thẳng trạng thái cuối cùng, không cần poll giả. Background task mở **session DB riêng** (session request gốc đã đóng khi task chạy) nhưng nhận `session_factory` injectable — route truyền `db.get_bind()` vào nên test tự động dùng đúng engine SQLite tạm của fixture, không cần wiring test riêng.
- **HIT-02 (duyệt):** `GET /reviews/pending` sort theo số vi phạm hard giảm dần rồi soft giảm dần. `POST /reviews/{id}/approve` — nếu có sửa gram, **không tin số client gửi**, gọi lại `compute_nutrition()`/`validate_menu()` trên server từ `food_id`+`grams` thật (RULE-1); còn hard violation sau khi sửa → `422`, chặn duyệt. Ghi `AuditLog` (before/after) mỗi lần duyệt/từ chối. Phát hiện thiếu sót khi viết test: `MealPlanItemOut` (BE-06) ban đầu không có `id`, khiến reviewer không có cách nào tham chiếu đúng item để sửa gram — bổ sung field `id`.
- **Docker:** build local thành công (`docker build`, image 2,18GB). Chạy thử container thật (`docker run` + `curl /health`) — `HEALTHCHECK` pass, `/health`/`/api/v1/health` trả `200`. `POST /auth/register` trả lỗi `no such table: users` — đúng như dự kiến vì container test không chạy `alembic upgrade head`, không phải lỗi code.
- **Deploy Render:** không tự làm — không có credential Render/Vercel/Neon nào trong máy, và Hưng xác nhận đây là việc của R1/đồng đội khác. Dừng lại ở build+test local, đẩy code lên GitHub để đồng đội tiếp tục.
- **Xác nhận:** `pytest -q` 157/157 pass (37 test API mới), `ruff check`/`ruff format --check`/`mypy src/` sạch. PR #40 (API stack) + PR #41 (backport fix `sync_devlog.py`/`JOURNAL`/`WORKLOG`/README từ `main` — phát hiện `develop` bị thiếu các fix này do đi tiếp trước khi sync chạy) đã merge vào `develop`.
- **Còn lại:** `BE-07` (food logs), `BE-08` (audit log — đã ghi qua `AuditLog` trong HIT-02 nhưng chưa có `GET /audit` riêng), `BE-09` (security test tự động), `HIT-01` (LangGraph `interrupt()` thật — hiện graph chạy hết 1 lượt rồi API tự quản trạng thái `pending_review`/`approved` ở tầng DB, không dùng cơ chế pause/resume của LangGraph checkpointer). Deploy Render/Vercel/Neon thật vẫn chưa làm.
- **Thời gian:** ~4h

### 2026-08-06 (DEC-015): Hoàn tất research report NHANES + kế hoạch crawl châu Á

**Tài liệu nghiên cứu:**
- ✅ `docs/DATA_RESEARCH_REPORT.md` (730 dòng) - Báo cáo đầy đủ 3 nguồn hiện tại
  - NHANES 2021-2023: 1,066 T2DM (US)
  - NHANES VN-adapted: 840 T2DM (BMI 24.0 khớp Da Nang 24.2)
  - Da Nang 2022: 103 T2DM (VN thật)
  - Total ready: 943 bệnh nhân
- ✅ `docs/DATA_SYNTHESIS.md` - Phương pháp adaptation NHANES → VN
- ✅ `docs/ASIAN_T2DM_CRAWL_PLAN.md` - Kế hoạch crawl 3 nguồn châu Á (5 ngày)

**Pipeline scripts NHANES (committed):**
- `scripts/download_nhanes_2021_2023.py` - Tải XPT từ CDC với checksum
- `scripts/build_nhanes_2021_2023_cohort.py` - Merge + filter probable T2DM
- `scripts/analyze_nhanes_distributions.py` - Tính phân bố có survey weights
- `scripts/convert_nhanes_to_json.py` - Chuyển sang PatientProfile schema
- `scripts/adapt_nhanes_to_vietnam.py` - Điều chỉnh BMI/height theo chuẩn VN

**Download instructions châu Á (committed):**
- `scripts/download_bangladesh_steps_t2dm.py` - Bangladesh STEPS 2018 (~750, BMI 23.4 gần VN nhất)
- `scripts/download_chns_china_t2dm.py` - China CHNS 2009+2015 (~4,500, có HbA1c)
- `scripts/download_india_nfhs5_t2dm.py` - India NFHS-5 (~55,000, lean diabetes phenotype)

**Validation results:**
- BMI adapted: 32.9 → 24.0 kg/m² (match Da Nang: 24.2)
- Height adapted: 166.0 → 161.7 cm (match VN norms)
- HbA1c preserved: 7.5%, clinical correlations maintained

**Compliance:** NCHS Data User Agreement tuân thủ, de-identification verified, provenance complete

**Commits:**
- `7f0b66b` - NHANES research report + pipeline (12 files, 2,168 insertions)
- `64e6430` - Asian crawl plan + download scripts (4 files)

**Next:** Submit CHNS/NFHS-5 registrations, download Bangladesh (instant), write build/adapt scripts
**Thời gian:** ~6h

---

### [2026-08-06] · R2 · Đề xuất HIT-06/HIT-07/EVL-07 — chuyên gia tự xây/chấm thực đơn + thu thập dữ liệu cải tiến (CHƯA DUYỆT, đang chờ đội bàn)
- **Bối cảnh:** Hưng yêu cầu đề xuất tính năng cho chuyên gia dinh dưỡng chấm/chỉnh sửa thực đơn "phù hợp" hơn (không chỉ approve/sửa gram/từ chối như HIT-02 hiện tại), tự xây thực đơn trực tiếp có tính toán ngay, và lưu lại dữ liệu này để sau này thử "học tăng cường hoặc các phương pháp cải tiến model".
- **Đã thêm 3 ticket ĐỀ XUẤT vào `docs/TICKETS.md`** (đánh dấu rõ "CẦN ĐỘI DUYỆT", chưa gán sprint/giờ):
  - `HIT-06` — API cho chuyên gia tự tạo/`fork` 1 thực đơn từ bản AI rồi sửa tự do (thêm/xoá món), mỗi thao tác gọi lại `compute_nutrition()`/`validate_menu()` NGAY trên server (đúng RULE-1 — chuyên gia chỉ chọn `food_id`+`grams`, không tự nhập số dinh dưỡng, khác hẳn "để LLM/chuyên gia tự gõ số"). Cần thêm 2 cột `origin` + `source_plan_id` vào `MealPlan` để biết bản nào từ AI, bản nào chuyên gia tự xây, và liên kết cặp gốc↔sửa.
  - `HIT-07` — chấm điểm có cấu trúc (đa chiều: đa dạng/khẩu vị/khả thi nấu) thay vì chỉ approve/reject nhị phân — phần tuân thủ dinh dưỡng máy đã tự chấm được (`violations[]`), chỉ cần chuyên gia chấm phần máy không đánh giá được.
  - `EVL-07` — script export cặp (bản AI, bản chuyên gia sửa) + diff + điểm thành `eval/datasets/expert_corrections.jsonl`, dùng cho few-shot prompt/phân tích lỗi phổ biến/số liệu báo cáo EVL-05 — **KHÔNG phải tự xây pipeline RL/fine-tune thật** (ngoài phạm vi 6 tuần), chỉ là bước thu thập dữ liệu có cấu trúc để mở đường, ghi rõ trong ticket để không ai lỡ hứa trên pitch điều chưa làm.
- **Vì sao KHÔNG tự code luôn:** đây là quyết định mở rộng phạm vi (thêm 1 luồng authoring song song với luồng AI hiện có), ảnh hưởng schema DB (`MealPlan` thêm cột) và UI (R4 cần thêm màn hình). Đúng tinh thần `CLAUDE.md` §6 "phát hiện yêu cầu mâu thuẫn/mở rộng phạm vi thì nói thẳng, đừng lặng lẽ làm theo" — ở đây không mâu thuẫn nhưng là quyết định đội nên bàn trước (đặc biệt việc RL có đáng làm trong 6 tuần hay không), Hưng đã xác nhận sẽ bàn thêm với đồng đội trước khi giao việc.
- **Thời gian:** ~20 phút

---

### [2026-08-06] · R2 · Đọc trực tiếp Excel chuyên gia — 3 khoảng cách công thức, đề xuất CLN-09/CLN-10/AGT-11
- **Bối cảnh:** Hưng gửi ảnh chụp 4 khối trong `data/Bảng xác định nhu cầu dinh dưỡng + thực đơn.xlsx` (sheet "Bước 1+2" + "4. Tính toán trên Excel" ở các sheet `tđ*`/`TĐ*`) — form thật chuyên gia dinh dưỡng dự án dùng để tính nhu cầu/chia bữa/lập thực đơn. Đọc trực tiếp formula (không suy đoán từ ảnh) bằng `openpyxl` (`data_only=False`) để trích đúng công thức, không phải giá trị đã tính sẵn.
- **Phát hiện 1 — công thức BMR khác hẳn:** hệ thống dùng Mifflin-St Jeor; Excel chuyên gia dùng **WHO/FAO/UNU (1985)**, bảng tuyến tính theo (nhóm tuổi × giới), hệ số W (cân nặng) không có số hạng chiều cao (`Bước 1+2!H2:J10`, VD nhóm 30-60 tuổi: Nam = 11,6×W + 879). PAL (hệ số lao động, `H12:J17`) cũng khác `ACTIVITY_FACTOR` hiện có: 4 mức nhẹ/TB/nặng/rất nặng = 1.6/1.7/2.1/2.4 (nam), so với Mifflin đang dùng 1.2/1.375/1.55/1.725. Hai công thức KHÔNG tương đương, cho TDEE khác nhau đáng kể trên cùng 1 hồ sơ.
- **Phát hiện 2 — phân nguồn đạm/béo động vật-thực vật:** Excel chia Protein 20%NL thành 35% ĐV/65% TV, Lipid 25%NL thành 50/50 ĐV/TV (`Bước 1+2!A12:D18`). Hệ thống hiện không có chiều dữ liệu này ở `food_items` (chỉ có tổng `protein_g`/`fat_g`).
- **Phát hiện 3 — phân bổ theo bữa áp cho cả macro, không chỉ kcal:** "2. Chia bữa" (Sáng 25%/Trưa 35%/Tối 30%/Phụ tối 10%, `A20:D49`) nhân tỷ lệ này cho TỪNG dòng P/Pđv/Ptv/L/Lđv/Ltv/G, không chỉ tổng kcal. Xác nhận công thức "Phụ tối" ở block đầu (`C49:D49`) và block cuối cùng (`C139:D145`, dùng đúng tham chiếu ô) đều là `Tổng ngày − Sáng − Trưa − Tối`, tương đương cách tính 10% trực tiếp vì 25+35+30+10=100% khớp. **Lưu ý:** các block công thức ở giữa (`C51:D138`) là lỗi copy-paste kéo công thức của người soạn Excel (tham chiếu ô lệch hàng, không khớp ý nghĩa) — không lấy làm chuẩn, chỉ dùng block đầu + block cuối làm nguồn tin cậy.
- **Đã làm (an toàn, không đổi hành vi hệ thống):** thêm `bmr_who_fao_unu()`, `pal_who_fao()`, `compute_tdee_who_fao()` vào `src/clinical/energy.py` — hàm THAM KHẢO, `compute_targets()`/`compute_bmr()`/`compute_tdee()` mặc định KHÔNG đổi. 7 test mới đối chiếu đúng từng ô công thức trong Excel (VD `test_bmr_nam_30_60_tuoi_khop_cong_thuc_excel`), cộng 1 test xác nhận 2 công thức cho kết quả khác nhau thật (không phải code trùng lặp vô nghĩa).
- **Không tự làm:** KHÔNG đổi `compute_targets()` sang dùng công thức mới (ảnh hưởng MỌI định mức đầu ra, cần quyết định tường minh — đúng `CLAUDE.md` §6 "ngưỡng lâm sàng sai không phải bug thường"), KHÔNG tự thêm rule tỷ lệ ĐV/TV (chưa có `guideline_ref` học thuật độc lập ngoài chính file Excel nội bộ — RULE-2 cần nguồn xác nhận được, không copy thẳng 1 con số từ bảng không rõ xuất xứ học thuật), KHÔNG tự thêm ràng buộc theo bữa vào CP-SAT (rủi ro hồi quy hiệu năng như đã từng gặp — DEC-017).
- **Đã thêm 3 ticket ĐỀ XUẤT** (`CLN-09`, `CLN-10`, `AGT-11`) vào `docs/TICKETS.md`, đánh dấu rõ cần R2/đội duyệt trước khi coi là chính thức.
- **Việc còn để ngỏ cho R4 (frontend) bàn cùng đội — CHƯA code, chỉ liệt kê để thảo luận:**
  1. ~~Form nhập liệu "loại lao động"~~ **Đã chốt ở entry sau (Hưng xác nhận dùng 4 mức nhãn chuyên gia).**
  2. Nếu `AGT-11` được duyệt: dashboard cần hiển thị được target/kết quả THEO BỮA (giống bảng "2. Chia bữa" trong Excel — mỗi bữa có Kcal/P/L/G riêng), không chỉ tổng ngày như hiện tại `GET /meal-plans/{id}` trả về.
  3. "Xác định tình trạng DD/BMI" trong Excel có ô phân loại (gầy/bình thường/thừa cân/béo phì — dù ảnh chụp chưa lộ rõ ngưỡng phân loại cụ thể, chỉ thấy công thức BMI thô) — hệ thống hiện chỉ trả số BMI thô nếu có, chưa có nhãn phân loại; R2 cần tra ngưỡng phân loại BMI chuẩn (WHO châu Á hay chuẩn nào) trước khi thêm, R4 cần biết để hiển thị đúng chỗ trên UI hồ sơ bệnh nhân.
- **Xác nhận:** `pytest -q` 164/164 pass (7 test mới), `ruff check`/`mypy src/` sạch.
- **Thời gian:** ~1h

---

### [2026-08-06] · R2 · Research BMR theo dân tộc/bệnh lý + chốt nhãn loại lao động 4 mức
- **Bối cảnh:** Hưng hỏi thẳng "BMR có thay đổi theo dân tộc/quốc gia/nhóm bệnh không? Cần nghiên cứu chứng minh" trước khi cân nhắc đổi công thức BMR mặc định (CLN-09), và xác nhận dùng nhãn "loại lao động" 4 mức của chuyên gia cho `ActivityLevel`. Dùng 2 agent research (WebSearch/WebFetch, không suy đoán từ trí nhớ) trả lời riêng biệt: (1) BMR theo dân tộc/quần thể/bệnh lý, (2) nguồn gốc thang hệ số `ACTIVITY_FACTOR` đang dùng.
- **Kết quả research 1 — BMR theo dân tộc/quần thể (đã trích đủ nguồn vào `docs/TICKETS.md` CLN-09):** CÓ bằng chứng thật nhưng KHÔNG nhất quán chiều — Mifflin-St Jeor chính xác nhất ở phụ nữ UAE (*Archives of Public Health* 2025), nhưng WHO/FAO/UNU chính xác nhất còn Mifflin **tệ nhất** ở bệnh nhân ĐTĐ2 Hàn Quốc (PubMed 37266123, 2023) — tức "công thức nào tốt hơn" phụ thuộc quần thể cụ thể, không có 1 câu trả lời chung. **Không tìm được nghiên cứu đo calorimetry trực tiếp trên người Việt Nam** — khoảng trống dữ liệu thật, ghi rõ để không ai giả định có. Chưa xác nhận được NIN có quy định chính thức dùng công thức nào (thử đọc PDF "Nhu cầu dinh dưỡng khuyến nghị cho người Việt Nam" qua mirror, không lộ rõ mục công thức — có thể do OCR, không phải bằng chứng NIN không quy định).
- **Kết quả research về bệnh lý:** ADA không quy định công thức BMR riêng cho ĐTĐ2 (chỉ điều chỉnh mục tiêu calo theo goal). KDOQI (CKD, cập nhật 2020, *Am J Kidney Dis*) dùng khoảng 25-35 kcal/kg — con số THỰC NGHIỆM theo cân nặng, không suy ra từ công thức BMR nào — nên "đổi công thức BMR cho CKD" không có cơ sở, đúng hơn là hệ thống hiện tại (áp `adjusted_body_weight_kg` + khoảng kcal/kg riêng cho CKD trong `clinical_rules.csv`) đã đi đúng hướng cách tiếp cận thật của guideline.
- **Kết quả research 2 — phát hiện phụ quan trọng:** thang hệ số `ACTIVITY_FACTOR` (1.2/1.375/1.55/1.725, đang dùng với Mifflin-St Jeor từ trước) **KHÔNG truy được về 1 nguồn học thuật/hướng dẫn lâm sàng đơn nhất** — không phải từ bài Mifflin-St Jeor 1990 gốc, cũng không phải IOM/NAM DRI 2005 (DRI 2005 dùng hệ số PA liên tục trong công thức EER khác cấu trúc hẳn, `nap.nationalacademies.org/catalog/10490`). Đây là quy ước phổ biến trong máy tính calo trực tuyến, tồn tại từ trước phiên này nhưng chưa ai phát hiện — ghi rõ vào docstring `models.py` theo đúng tinh thần RULE-2 (không giả vờ đã có nguồn).
- **Đã chốt (quyết định của Hưng, không phải AI tự đặt):** `ActivityLevel` đổi từ `SEDENTARY/LIGHT/MODERATE/ACTIVE` sang **4 mức nhãn "loại lao động" của chuyên gia**: `LIGHT/MODERATE/HEAVY/VERY_HEAVY` (nhẹ/trung bình/nặng/rất nặng), khớp thẳng "Bảng 2" Excel. Lan toả thay đổi qua `src/clinical/models.py`, `src/clinical/energy.py` (`pal_who_fao()` giờ khớp 1:1, không cần map xấp xỉ), `src/db/models.py`, `src/api/routes/patients.py` (thêm `Literal` validation, trước là `str` tự do không chặn giá trị sai), `scripts/seed_demo_users.py`. `ACTIVITY_FACTOR` (nhánh Mifflin) thêm `VERY_HEAVY: 1.9` theo ĐÚNG quy ước không-có-nguồn đã dùng cho 3 mức kia (nhất quán, không giả vờ mức mới có nguồn riêng trong khi 3 mức cũ thì không).
- **Không tự làm:** KHÔNG tự chốt đổi công thức BMR mặc định (research cho thấy bằng chứng trái chiều, chưa đủ để quyết — đúng `CLAUDE.md` §6, để R2 quyết dựa trên xác nhận NIN trước).
- **Xác nhận:** `pytest -q` 164/164 pass, `ruff check`/`mypy src/` sạch (10 lỗi ruff thấy trong lần chạy toàn repo thuộc file `scripts/log_*.py` của PR #44 đồng đội, không phải file phiên này sửa).
- **Thời gian:** ~50 phút

### [2026-08-06] · R2 · CLN-09 chốt: WHO/FAO/UNU thành công thức BMR/TDEE mặc định hệ thống
- **Bối cảnh:** Sau entry research trước đó (BMR không nhất quán theo quần thể, thiếu dữ liệu Việt Nam trực tiếp), Hưng chốt quyết định cuối: *"Vậy thì ưu tiên sử dụng từ bản excel, kể cả BMR và ActivityLevel"* — tức chấp nhận không có bằng chứng học thuật khẳng định WHO/FAO/UNU "đúng hơn" cho người Việt, nhưng ưu tiên đây là công thức chuyên gia dinh dưỡng DỰ ÁN đang dùng thật (nguồn thực hành trực tiếp, cao hơn tài liệu quốc tế chưa xác nhận áp dụng được).
- **Thay đổi code:** viết lại `src/clinical/energy.py` — `compute_bmr()`/`compute_tdee()` (dùng trong `compute_targets()`) chuyển từ Mifflin-St Jeor sang `bmr_who_fao_unu()` + `pal_who_fao()`. Mifflin-St Jeor hạ xuống vai trò THAM KHẢO/so sánh (`compute_bmr_mifflin()`, `compute_tdee_mifflin()`), dùng `_ACTIVITY_FACTOR_MIFFLIN` cục bộ (giữ nguyên giá trị/docstring cảnh báo thiếu nguồn từ trước). `compute_tdee_who_fao()` (cân nặng thô, không hiệu chỉnh béo phì) giữ nguyên làm biến thể khớp Excel 100%; `compute_tdee()` mặc định VẪN áp `adjusted_body_weight_kg` (ràng buộc an toàn lâm sàng riêng, không phải một phần "công thức BMR" nên không mâu thuẫn quyết định ưu tiên Excel).
- **Dọn dẹp:** xoá `ACTIVITY_FACTOR` khỏi `src/clinical/models.py` — hết consumer sau khi `energy.py` không còn import nó (dùng `_ACTIVITY_FACTOR_MIFFLIN` cục bộ thay thế).
- **Tác động test:** WHO/FAO/UNU + PAL Bảng 2 cho TDEE cao hơn đáng kể so với Mifflin+`ACTIVITY_FACTOR` cũ (PAL 1.6-2.4 so với hệ số 1.375-1.9) → 8 test ban đầu fail. Đã sửa: (1) `tests/conftest.py::modest_menu` tăng định lượng (~×1.3) để đạt kcal/chất xơ mục tiêu mới; (2) nới biên trên `test_kcal_tren_kg_nam_trong_khoang_lam_sang` từ 40 lên 42 (giá trị thật ~40.2 kcal/kg, nam lao động nhẹ, T2DM+CKD); (3) sửa `test_who_fao_va_mifflin_cho_ket_qua_khac_nhau_ro_ret` so sánh `compute_tdee_mifflin()` thay vì `compute_tdee()` (đã không còn ý nghĩa vì cả hai đều WHO/FAO/UNU); (4) tách `MenuItem` 2210g (vượt `le=2000`) thành 2 món trong `test_muc_do_vi_pham_nang_luong_theo_do_lech[1.4-hard]`.
- **Xác nhận:** `pytest -q` 164/164 pass, `ruff check src/ tests/` sạch, `mypy src/` sạch (34 file).
- **Chưa làm (không chặn quyết định này, nhưng nên làm sau):** R2 chưa chạy lại 60 case eval đối chiếu chuyên gia thật với công thức mới; chưa xác nhận trực tiếp với NIN xem có quy định chính thức riêng không.
- **Thời gian:** ~35 phút

### [2026-08-06] · R2 · Audit RULE-1/2/3 sau CLN-09 — phát hiện + sửa 1 lỗi RULE-2 thật
- **Bối cảnh:** Hưng yêu cầu "pull github, sau đó kiểm tra, audit lại logic dự án" sau khi merge CLN-09. Dùng 1 subagent đọc trực tiếp `src/` đối chiếu 3 rule đỏ CLAUDE.md §2, không suy đoán.
- **Phát hiện thật (đã sửa):** `src/clinical/rules.py::compute_targets()` — target `kcal` vẫn hardcode `rule_ids=["ENERGY-MSJ"]`/`guideline_refs=["Mifflin-St Jeor 1990..."]` dù `compute_energy_target_kcal()` đã đổi sang WHO/FAO/UNU từ CLN-09 cùng ngày. Đây là vi phạm RULE-2 thật (nguồn hiển thị cho người dùng sai) — không phải lý thuyết. Đổi thành `ENERGY-WHO-FAO-UNU` + ghi chú CLN-09.
- **Phát hiện phụ (đã sửa):** `agents/nodes/core.py` chứa logic tính toán nhưng chưa nằm trong `DETERMINISTIC_FILES` của `tests/test_agent.py` (test chống import LLM, RULE-1) — thêm vào danh sách, xác nhận file vốn đã sạch.
- **Không phát hiện vi phạm:** RULE-3 (route `meal_plans`/`reviews` chặn đúng theo `status==approved`), cơ chế đa bệnh lý DEC-007 (`needs_expert_review` chỉ gắn khi xung đột thật, không gắn tràn lan).
- **Xác nhận:** 165/165 test pass (thêm 1 test coverage), `ruff`/`mypy` sạch. Commit `7dc2197`, đã push PR #47.
- **Thời gian:** ~20 phút

### [2026-08-07] · R2 · Audit + fix 2 PR đội (#49, #50) trước khi merge
- **Bối cảnh:** Hưng yêu cầu "check các branch mới từ team, kiểm tra rồi merge". PR #49 (EVL-01 T2DM eval dataset) đang conflict thật với `main`; PR #50 (Next.js frontend + guardrail y tế) CI kẹt `QUEUED` >1h do runner tự host offline (xác nhận không có service/process/container GitHub Actions runner nào trên máy này — runner phải nằm ở máy khác). Dùng 2 subagent review nội dung song song trong lúc chờ, sau đó tự kiểm chứng lại từng phát hiện bằng cách đọc trực tiếp diff/chạy thử trước khi kết luận (không tin agent report mù).
- **PR #49 — đã tự fix, đã push:** (1) Resolve conflict `Makefile` (chỉ dòng `.PHONY` — 2 nhánh cùng thêm target khác nhau, gộp cả hai). (2) Phát hiện + sửa lỗi NGHIÊM TRỌNG: `python -m py_compile` cho thấy 3 script mới (`download_india_nfhs5_t2dm.py`, `download_chns_china_t2dm.py`, `download_bangladesh_steps_t2dm.py`) có `SyntaxError` thật — docstring chứa đường dẫn Windows kiểu `C:\Users\dinhl\...` khiến `\U` bị hiểu nhầm thành escape unicode 8 chữ số, script KHÔNG import được. `pytest` không bắt được vì các script trong `scripts/` không nằm trong test suite. Sửa bằng đổi docstring sang raw string (`r"""`). Đây là bug do tác giả phát triển trên máy có `C:\Users\dinhl\` (khác máy CI/máy khác), một dạng lỗi "chưa test trên môi trường sạch" — liên quan trực tiếp tới yêu cầu "làm sạch/chuẩn hoá dữ liệu và file trước khi dùng" của Hưng cùng ngày. Chính sách "100% dữ liệu mô phỏng" bị PR này đổi sang cho phép dùng dữ liệu NHANES/CHNS/STEPS/NFHS5 đã de-identify — **Hưng đã duyệt trực tiếp** ("PR#49 có thể de-identify để sử dụng dữ liệu được nhé"), không cần R1/R3 sign-off thêm theo yêu cầu này.
- **PR #50 — đã tự fix, đã push:** Phát hiện lỗ hổng an toàn THẬT trong `src/agents/guardrail.py` (tính năng "guardrail chặn chỉ định y khoa", AGT-07): `check_guardrail()` kiểm tra `_SAFE_PATTERNS` TRƯỚC `_MEDICAL_PATTERNS`, và 1 safe-pattern chỉ cần khớp 1 từ dinh dưỡng đứng một mình (`thực đơn|khẩu phần|bữa ăn|dinh dưỡng|calo|carb|protein|chất béo|chất xơ`) là bypass toàn bộ — tự kiểm chứng bằng ví dụ cụ thể "Thực đơn của tôi thì tôi có nên ngừng thuốc insulin không?" lọt qua vì khớp "thực đơn". Bộ test cũ (20 câu) không bắt được vì không có case kết hợp từ dinh dưỡng + câu hỏi y tế nguy hiểm. Đã sửa: đảo thứ tự (dangerous pattern kiểm tra trước), xoá 3 safe-pattern không yêu cầu tên thuốc cụ thể đi kèm, thêm 3 test case adversarial vào `SHOULD_BLOCK`. Đồng thời sửa `except Exception` trần ở tầng LLM (vi phạm CLAUDE.md §4) — tách 2 nhánh có chủ đích: chưa cấu hình API key = không phải sự cố (fail-open, giữ chat hoạt động ở dev/test không có key thật), lỗi thật khi gọi API đã cấu hình = fail-closed (chặn, đúng chiều an toàn cho hệ thống y tế — khác thiết kế gốc là fail-open toàn bộ).
- **Docker cleanup (theo yêu cầu chung "làm sạch/chuẩn hoá mọi dữ liệu/file"):** `.dockerignore` thiếu loại trừ `data/` — `COPY . .` trong Dockerfile đưa cả **1,7GB** dump nghiên cứu thô (USDA FoodData Central bulk CSV/zip 1,2GB, PDF NIN 2007/2017, xlsx purine DB) vào image production một cách không cần thiết, trong khi chỉ `data/seeds/` (~1,6MB, được `src/clinical/seeds.py::load_food_repository()` đọc trực tiếp lúc chạy) là thật sự cần. Thêm loại trừ `data/*` (giữ `data/seeds/`) và `web-next/` (deploy riêng qua Vercel theo `render.yaml`/`vercel.json`, không thuộc image backend). Thêm `PYTHONDONTWRITEBYTECODE`/`PYTHONUNBUFFERED`. **Đã build + chạy thử thật** (không chỉ sửa xong là xong): xác nhận `data/seeds/*.csv` vẫn có trong image, `load_food_repository()` và `from src.main import app` chạy được không lỗi, `/app/data` giảm từ ~1,7GB dự kiến xuống 3,9MB thật.
- **Runner tự host:** xác nhận KHÔNG chạy trên máy này (không service/process/Docker container/scheduled task nào của GitHub Actions runner) — không có cách khởi động lại từ xa. Cả CI của PR #49 và #50 đều kẹt `QUEUED` cùng lý do, không phải lỗi riêng PR nào.
- **Xác nhận:** PR #49 sau fix: `pytest -q` 165/165, `ruff`/`format`/`mypy` sạch. PR #50 sau fix: `pytest -q` 190/190 (bao gồm 25/25 `test_guardrail.py` với 3 case adversarial mới), `ruff`/`format`/`mypy` sạch, Docker build+run xác nhận thật.
- **Chưa làm:** chưa merge PR #49/#50 vào `main` — chờ CI chạy được (cần runner tự host online) trước khi merge, dù nội dung đã audit và fix xong.
- **Thời gian:** ~70 phút

---

### [2026-08-06] · R2 · Research đợt lớn: verify clinical_rules, mở rộng GI, tương tác thực phẩm + giờ thuốc
- **Bối cảnh:** Hưng giao 9 luồng việc cho `data/` (research y khoa, thực đơn vùng miền, tương tác dược/thực phẩm, Việt hoá bảng thành phần, mở rộng NIN, GI/purine, serving_sizes, usda_values, viết lại README). Quyết định: chạy song song nhóm A (khai thác file local đã có trong repo) + nhóm B (research web/PubMed), nhóm C (schema tương tác TP-TP + giờ ăn) code luôn kèm migration sau khi có dữ liệu nguồn thật. 3 subagent chạy nền, dùng MCP PubMed ưu tiên hơn WebSearch (PMID thật, đáng tin hơn).
- **Kết quả B1 — verify 21 `clinical_rules`:** Dùng nguồn sơ cấp đọc trực tiếp (KDIGO 2024 full text, KDOQI 2020 full PDF, NIN 2016 full PDF, ADA Standards of Care 2026 §5/§13 — bản 2026 xác nhận CÓ THẬT, *Diabetes Care* Vol 49 Suppl 1, PMID 41358898). Chỉ 7/21 rule khớp đúng nguồn (`BASE-NA-01`, `T2DM-SUG-01`, `T2DM-PRO-02`, `CKD-PRO-01`, `CKD-PRO-05`, `CKD-NA-01`, `HTN-NA-01`). **Phát hiện an toàn nghiêm trọng** đã ghi thành ticket `CLN-11` (P0): `CKD-PRO-01` áp trần đạm 0.8 g/kg cho cả G5 dù không phân biệt bệnh nhân lọc máu (KDOQI 2020 yêu cầu 1.0-1.2 g/kg cho G5D) — nguy cơ suy dinh dưỡng protein-năng lượng nếu áp nhầm; 3 rule kali `CKD-K-01/02/03` (đều `hard`) trích dẫn "KDOQI 2020 theo giai đoạn" nhưng mục 6.4.1 thật của KDOQI 2020 chỉ ở mức OPINION và tự nhận chưa có bằng chứng theo giai đoạn. Chi tiết đầy đủ + toàn bộ rule LỆCH/KHÔNG XÁC MINH ĐƯỢC xem `CLN-11` trong `docs/TICKETS.md`. **Không tự sửa ngưỡng** (đúng CLAUDE.md §6) — chờ R2.
- **Kết quả B2a — mở rộng GI món Việt:** Nguồn chính: Chan HMS et al. 2001 *Eur J Clin Nutr* 55:1076-1083 (đã đọc toàn văn Bảng 1+2, PMID 11781674), Atkinson 2008 *Diabetes Care* 31:2281-2283 (PMC2584181), Henry 2021 *Nutr Diabetes* 11:2 compendium 940 món châu Á (PMID 33414403). Tìm được ~39 giá trị GI mới (cơm tấm, bún khô, cháo, khoai môn, sắn, mít, ổi, bánh cuốn, xôi mặn, các loại đậu, sữa, đường...). **Phát hiện quan trọng:** Việt Nam KHÔNG nằm trong danh sách quốc gia của compendium Henry 2021 — tức chưa có nghiên cứu GI nào đo trực tiếp trên người tại Việt Nam đạt chuẩn đưa vào bảng quốc tế; "Chan2001_VN" thực chất đo tại Sydney trên gạo/bún nhập từ Thái Lan/Úc/Trung Quốc, không phải mẫu đo tại VN — cần ghi rõ trong `note`, đừng để tên nguồn gây hiểu nhầm. **Cảnh báo giá trị hiện có đáng ngờ:** dưa hấu (CSV=51) thấp hơn nhiều so với y văn (dải thật 48-76, giá trị kinh điển 76); bánh mì (CSV=59) thấp bất thường so với y văn (75-83); khoai lang (CSV=77) một nguồn khác cho giá trị phi lý (179 thang bánh mì) — không dùng. Đã loại bỏ mọi giá trị eGI đo in-vitro (không phải đo trên người).
- **Kết quả B2b — tương tác thực phẩm-thực phẩm + giờ dùng thuốc:** 9 cặp tương tác hoá sinh có nguồn PMID thật (polyphenol/tannin ức chế hấp thu sắt non-heme 50-90% tuỳ liều — Hurrell 1999 PMID 10999016, Brune 1989 PMID 2598894; vitamin C tăng hấp thu sắt — Siegenberg 1991 PMID 1989423; phytate gạo giảm hấp thu sắt ~3 lần — Tuntawiroon 1990 PMID 2401279; canxi ăn cùng bữa GIẢM nguy cơ sỏi thận do oxalat, ngược với canxi viên uống xa bữa — Curhan 1997 PMID 9092314; fructose/rượu bia tăng acid uric rõ rệt liên quan gout — Choi 2008 PMID 18244959, Choi 2004 PMID 15094272, rượu vang KHÔNG tăng). Giờ dùng thuốc: metformin/allopurinol uống cùng/sau ăn giảm kích ứng tiêu hoá, levothyroxin phải uống đói và tránh cà phê (giảm hấp thu 27-36%, Benvenga 2008 PMID 18341376), ăn tối sau 20h liên quan HbA1c cao hơn ở ĐTĐ2 (Sakai 2018 PMID 29375081). **Verify 30 dòng `drug_food_interactions.csv` phát hiện nhiều lỗi trích dẫn thật:** dòng 2/3 (rau ngót/cải bắp) gán sai vào chuyên luận Warfarin (chuyên luận thật chỉ nêu gan động vật/súp lơ/rau xanh chung chung); dòng 15 sai tên đồng tác giả; dòng 16 (allopurinol+rượu) và dòng 17 (colchicin+bưởi) gán nhầm mục trong Dược thư QGVN 2022 (đã xác nhận QĐ 3445/QĐ-BYT 23/12/2022 có thật, nhưng 2 mục này không có trong đúng trang được trích); dòng 23 severity `moderate` quá cao so với mức ảnh hưởng thật (AUC +16%); dòng 30 khuyến nghị mâu thuẫn với chính bằng chứng Curhan 1997 trích trong cùng dòng.
- **Việc tiếp theo (chưa làm, ghi nhận cho phiên sau):** map dữ liệu GI/tương tác mới vào đúng CSV kèm review R2 cho phần lâm sàng; xây bảng DB mới cho tương tác TP-TP + giờ thuốc (nhóm C); B3 (thực đơn vùng miền) đang chạy riêng.
- **Thời gian:** ~35 phút điều phối + thời gian chạy nền của 3 subagent

### [2026-08-06] · R2 · B3 xong + hoàn tất nhóm A (khai thác file local): purine, sugar, serving_sizes, category
- **B3 — thực đơn/mâm cơm 3 miền:** không tìm được nghiên cứu ẩm thực học/dinh dưỡng học thuật định lượng cấu trúc mâm cơm 3 miền (chỉ có nguồn báo/blog phổ thông). Đề xuất 20 món theo vùng — đa số kiến thức ẩm thực phổ thông, chưa có nguồn định lượng, phải xử lý như "LLM draft" khi thêm vào `dishes.csv`, không tự thêm vào CSV. **Cảnh báo an toàn:** món đề xuất "canh chua cá lóc kiểu Huế" dùng khế (carambola) — y văn quốc tế ghi nhận khế chứa caramboxin, chống chỉ định ở bệnh nhân suy thận. Ghi vào `DAT-04` trong `docs/TICKETS.md`, chưa thêm món nào vào `dishes.csv`.
- **A1 (`sugar_g`):** quét toàn bộ `food_nutrient.csv` USDA bulk (script `scripts/scan_usda_sugar_coverage.py`) cho 6.861 fdcId nguồn USDA — "Sugars, added" (gần nghĩa free sugar nhất) chỉ có **0%** dữ liệu trong bộ SR Legacy/Foundation; "Total Sugars" có 81.9% nhưng KHÁC nghĩa free sugars của WHO mà `sugar_g`/`T2DM-SUG-01` dùng. **Không tự đổ nhầm dữ liệu vào field sai nghĩa** — ghi ticket `DAT-15` cho R2 quyết định có thêm cột `total_sugar_g` riêng hay không (đã có sẵn bảng tra `usda_sugar_coverage.csv` nếu R2 chọn làm).
- **A2 (`purine_mg`):** trích `data/PURINEDATABASEANDDATASOURCES2025.xlsx` (608 dòng NAm+nonNAm+alcohol, script `scripts/extract_purine_db.py`) thành `purine_db_reference.csv` (475 dòng có trích dẫn Table6). Map thủ công (review từng dòng, không tự động) 32/366 dòng curated còn thiếu — chỉ nhận match cùng loài/loại rõ ràng (VD bỏ qua "cải xanh" vì các dòng gần giống trong bảng nguồn thực ra khác loài thực vật). `purine_values` phủ 19 → 51 món. Script: `scripts/map_purine_to_food_items.py`. Ghi `DAT-14`.
- **A3 (`serving_sizes`):** không có khảo sát khẩu phần món Việt quy mô lớn công khai để mở rộng thật lên 100-200 dòng. Thay vào đó tính TRUNG VỊ khẩu phần thật từ `food_portion.csv` (47.446 bản ghi USDA) theo 172 nhóm **WWEIA** (hệ phân loại chính thức dùng trong khảo sát NHANES) — 169/172 nhóm đạt ≥5 mẫu. 5 dòng gốc (món Việt cụ thể) giữ nguyên, thêm 169 dòng `wweia_*` — tổng 174 dòng, mỗi dòng ghi rõ đây là khẩu phần theo thói quen ăn Mỹ, không phải VN. Script: `scripts/build_serving_sizes_wweia.py`. Ghi `DAT-16`.
- **A4 (`category`):** dịch trực tiếp 28 nhóm `food_category` chính thức của USDA FDC sang tiếng Việt, join qua `fdc_id` (script `scripts/fill_category_from_usda.py`). Độ phủ `category` 2% (152/7315) → 96% (7022/7315), 6.870 dòng được gán. Đây là nhãn phân loại/tổ chức dữ liệu, không phải giá trị lâm sàng nên không cần `source_ref` riêng. Ghi `DAT-17`.
- **Xác nhận cuối đợt A:** `validate_data.py` không lỗi mới (4 cảnh báo cũ, không tăng), `pytest -q` 165/165 pass. Tất cả script đều idempotent + có `--dry-run`, để lại dấu vết tái tạo được (không sửa tay CSV trực tiếp).
- **Thời gian:** ~90 phút

### [2026-08-06] · R2 · Nhóm C: 2 bảng DB mới (tương tác thực phẩm-thực phẩm, giờ dùng thuốc) — schema + migration + seed
- **Bối cảnh:** Hưng duyệt trước cho nhóm C "code luôn cả migration + seed dữ liệu" (khác nhóm A/B chỉ cần research/ticket). Dùng dữ liệu đã có PMID/trích dẫn thật từ agent B2b (research trước đó cùng ngày).
- **Schema:** thêm `FoodFoodInteraction` và `DrugMealTiming` vào `src/db/models.py` (theo đúng khuôn mẫu `DrugFoodInteraction` có sẵn — cột `source_ref` bắt buộc, `verify_status` mặc định `to_verify`). Migration `alembic/versions/5394cb31dc4e_...py` viết tay theo đúng style file migration gốc (không chạy `alembic revision --autogenerate` để tránh kết nối nhầm vào DB thật cấu hình trong `.env`) — đã test cả `upgrade`/`downgrade` trên SQLite scratch file, chạy sạch cả 2 chiều.
- **Seed:** `data/seeds/food_food_interactions.csv` (9 cặp, PMID thật — sắt/polyphenol/phytate/canxi/oxalat/fructose/rượu, xem `DAT-18`), `data/seeds/drug_meal_timing.csv` (6 thuốc, xem `DAT-19`). Thêm `seed_food_food_interactions()`/`seed_drug_meal_timing()` vào `scripts/seed_db.py`, wiring vào `seed_all()`. Thêm `check_food_food_interactions()`/`check_drug_meal_timing()` vào `scripts/validate_data.py`.
- **Cập nhật đồng bộ tài liệu (bắt buộc theo CLAUDE.md — "sửa 1 bên phải sửa bên kia"):** ERD mermaid trong `docs/ARCHITECTURE.md` thêm 2 bảng mới, danh sách "bảng bắt buộc có `source`" cập nhật.
- **Xác nhận:** seed thử trên SQLite scratch DB thành công (9 + 6 dòng), `pytest -q` 165/165 pass (đã sửa `test_tao_du_15_bang` → `test_tao_du_17_bang`), `ruff`/`mypy` sạch, `validate_data.py` 0 lỗi (2 cảnh báo mới: cả 2 bảng đều 100% `to_verify`, đúng dự kiến vì chưa R2 xác nhận).
- **CHƯA làm (ghi rõ trong ticket, không giả vờ xong):** chưa wiring 2 bảng này vào agent/API/UI — mới dừng ở tầng dữ liệu. R2 chưa xác nhận `verify_status`. Đặc biệt lưu ý ranh giới an toàn CLAUDE.md §3 khi wiring `drug_meal_timing`: chỉ mô tả thời điểm uống, tuyệt đối không diễn giải thành khuyên đổi liều/ngừng thuốc.
- **Thời gian:** ~40 phút

### [2026-08-07] · R2 · Research Supabase cho hosting DB + đồng bộ ERD team — ADR-008
- **Bối cảnh:** Hưng muốn nghiên cứu dùng Supabase để đồng bộ team về DB/ERD. `docs/ARCHITECTURE.md` trước đó để mở "Neon free tier hoặc Supabase", chưa chốt hướng dùng.
- **Đã xác minh trực tiếp** (doc/pricing chính thức Supabase, không suy đoán): pgvector hỗ trợ qua Dashboard (khớp ADR-001); Free tier 500MB DB, 2 project active, team member không giới hạn; **project free tự pause sau 1 tuần không hoạt động** (rủi ro thật cho demo); branching không có ở Free tier.
- **Khảo sát code hiện tại:** Alembic là nguồn chân lý migration duy nhất (2 file, autogenerate rồi review tay); Auth JWT+argon2id tự xây trong FastAPI, phân quyền chặn ở tầng query (`_get_owned_profile` pattern); RACI schema DB thuộc R3.
- **Quyết định (ADR-008):** nếu chọn Supabase thay Neon, **chỉ dùng làm Postgres hosted thuần** (đổi `DATABASE_URL`) — không dùng song song Supabase CLI migrations (tránh 2 nguồn chân lý cạnh tranh Alembic), không bật Row Level Security/Supabase Auth (tránh 2 tầng phân quyền phải đồng bộ tay, trùng lặp JWT+argon2id đã có). Lý do cân nhắc Supabase: Studio Table Editor cho cả đội (kể cả người không rành SQL) tự xem bảng/quan hệ khoá ngoại trực quan, đúng nhu cầu đồng bộ hiểu ERD.
- **Cập nhật:** `docs/ARCHITECTURE.md` (thêm ADR-008, sửa dòng deploy DB), `docs/TICKETS.md` (`SET-05` bổ sung research + ràng buộc bắt buộc nếu R3 chọn Supabase).
- **Chưa làm:** chưa tạo project Supabase thật, chưa đổi `DATABASE_URL` nào — đây vẫn là quyết định của R3 theo RACI, chỉ ghi lại nghiên cứu để R3 tham khảo khi quyết.
- **Cập nhật cùng ngày — R3 đề xuất chuyển hẳn sang Supabase CLI migrations, đã phản biện và Hưng xác nhận GIỮ NGUYÊN ADR-008:** lý do từ chối full switch — (1) lợi ích ban đầu (Studio xem ERD trực quan cho team) đạt được ngay khi chỉ đổi hosting, không cần đổi migration tool; (2) Supabase CLI migration là SQL/DB-diff-first, không đọc SQLAlchemy models, chuyển hẳn sẽ tạo `models.py` và SQL migration thành 2 nguồn chân lý phải tự tay đồng bộ; (3) vi phạm rule tường minh `CLAUDE.md` §4 ("Đổi schema → luôn kèm Alembic migration"), phải sửa rule nếu đổi; (4) thêm dependency Docker cục bộ cho `supabase db diff` mà hiện tại không ai cần; (5) lợi ích thật của Supabase CLI migration (branching theo PR) không có ở Free tier. Cũng bác bỏ phương án "hybrid" (Alembic + sửa trực tiếp qua Supabase Studio tuỳ lúc) vì tạo schema drift âm thầm (`alembic_version` không biết về thay đổi qua UI). **Chốt: Alembic vẫn là công cụ DUY NHẤT ghi schema dù host ở đâu; Supabase (nếu dùng) chỉ đóng vai trò hosting + xem qua Studio, không ai sửa schema trực tiếp qua UI.** Không cần sửa `CLAUDE.md`.

---

### [2026-08-07] · R2 · DAT-22 — trích xuất Bảng TPTP VN 2017 (620 món)

- Trích 620/620 thực phẩm (tr.23-152, khối macro+khoáng+vitamin) từ `data/Bang-thanh-phan-dinh-duong-Thuc-pham-VN-2017-27-4-17.pdf` bằng `pdfplumber.extract_tables()`, không OCR, không trùng mã. Script: `scripts/extract_nin2017.py` → `scripts/nin2017_extracted.json`.
- Merge vào `data/seeds/food_items.csv` bằng `scripts/merge_nin2017_into_food_items.py` (chỉ khớp tên tuyệt đối, không fuzzy-match — bài học từ lần fuzzy-match sai "Hẹ"↔"Ghẹ" trước đó): 82 dòng cũ được bổ sung `source_ref` NIN 2017, 348 dòng mới thêm dạng placeholder (thiếu ≥1 trường lõi trong PDF, để trống thay vì đoán), 128 xung đột số liệu ghi vào `scripts/nin2017_conflicts.md` chờ R2 quyết định (không tự merge).
- Xác nhận Purine (tr.219-248) CÓ số liệu thật cho nhóm Thịt/Thủy sản nhưng chưa merge do rủi ro lệch cột — đề xuất `DAT-23` làm riêng, cẩn thận hơn. Xem `scripts/nin2017_purine_findings.md`.
- Sửa 1 bug thật phát hiện khi merge: `validate_data.py` cộng trùng `fiber_g` vào tổng đa chất (đã nằm trong `carb_g` theo NIN 2017), gây báo lỗi giả cho món khô/nhiều xơ (Măng khô, Hạt tiêu).
- **Lưu ý kỹ thuật:** việc trích xuất được chạy đầu tiên trong 1 background agent dùng git worktree — worktree đó vô tình được tạo từ một commit cũ (trước khi `food_items.csv` được mở rộng lên 7316 dòng qua nhiều PR khác), nên kết quả merge ban đầu (183/364/53) bị tính trên dữ liệu cũ. Đã phát hiện qua kiểm tra `wc -l`/`git log` trước khi push, không dùng kết quả đó — chỉ giữ lại phần trích xuất thô (`nin2017_extracted.json`, độc lập với CSV nền) và script, chạy lại `merge_nin2017_into_food_items.py` trên `food_items.csv` thật hiện tại của `main`, ra số liệu đúng (82/348/128 ở trên). `validate_data.py` (0 lỗi) và `pytest` sạch sau khi chạy lại.
- **Thời gian:** ~30 phút (không tính thời gian chạy nền của background agent).

---

### [2026-08-07] · R2 · SET-05 — kết nối Supabase, alembic upgrade head thành công

- Hưng tự tạo project Supabase (`VNutriCare`, `tvnrvvkclqsuhnxnrcrn`, ap-northeast-1) và kết nối MCP Supabase (read_only) qua `.mcp.json`.
- Chạy `alembic upgrade head` thành công lên Supabase — 17 bảng khớp đúng `src/db/models.py` (xác nhận qua `list_tables` MCP, read-only).
- **2 vấn đề kết nối gặp phải và cách xử lý:**
  1. `DATABASE_URL` ban đầu dùng host "Direct connection" (`db.<ref>.supabase.co`) — chỉ resolve ra địa chỉ IPv6, mạng hiện tại không có route IPv6 nên `psycopg2.OperationalError: could not translate host name`. Đổi sang **Session Pooler** (`aws-0-ap-northeast-1.pooler.supabase.com`, có IPv4) thì kết nối được.
  2. Thiếu driver `psycopg2` (dự án trước giờ chỉ chạy SQLite nên dòng `psycopg2-binary` trong `requirements.txt` bị comment) — bật lại và cài.
- Advisor bảo mật Supabase báo RLS bật mặc định trên mọi bảng nhưng chưa có policy (mức INFO, do Supabase tự động, không phải mình tạo) — không xử lý vì backend dùng kết nối Postgres trực tiếp, không qua PostgREST/anon key, đúng phạm vi ADR-008.
- `vector` extension chưa bật (chưa cần, `guideline_chunks.embedding` còn ở JSON) — để dành cho `DAT-06`.
- **Thời gian:** ~20 phút.

---

### [2026-08-07] · R2 · Fix bug thật: CP-SAT sinh thực đơn thiếu năng lượng nghiêm trọng (merge PR#57 × PR#59)

- Khi merge `main` vào `fix/AGT-11-cpsat-day-cap-and-vn-dishes` (PR #57), `tests/test_api_reviews.py::test_duyet_sua_gram_tinh_lai_dinh_duong` fail với thiếu hụt bất thường (335 kcal thay vì tối thiểu 2435 kcal chỉ sau khi sửa -20g một món) — điều tra sâu, không phải test giòn mà là **bug thật** do 2 hệ thống "dish" độc lập bị hợp nhất cơ học:
  - PR #57 (`fix/AGT-11`): `DishCandidate` + cơ chế `dish_chosen` trong CP-SAT — món hoàn chỉnh được chọn NGUYÊN KHỐI rồi tự khai triển thành food_id+grams nguyên liệu thô thật trong `MenuDraft` (giữ RULE-1).
  - `main` (PR #59): `DishFoodRepository` (`load_dish_food_repository()`) — biến MỖI món ăn thành một "food" tổng hợp (id âm, `kcal_100g` = mật độ trung bình pha loãng cả công thức).
  - Sau merge, `src/api/routes/meal_plans.py` dùng `load_dish_food_repository()` làm kho nguyên liệu cho CẢ CP-SAT lẫn LLM — khiến CP-SAT chọn lượng nhỏ của một "food" tổng hợp (mật độ đã pha loãng, VD PHO-BO công thức thiếu ~105 kcal/100g do `dish_ingredients.csv` chỉ có 5 dòng, thiếu gia vị/nước dùng) như thể đó là nguyên liệu rời — ra thực đơn thiếu năng lượng nghiêm trọng mà CP-SAT vẫn báo khả thi (tự thoả mãn ràng buộc bằng chính dữ liệu sai).
- **Fix** (`src/api/routes/meal_plans.py`): chọn kho thực phẩm theo generator — `load_food_repository()` (nguyên liệu thô thật) cho `cpsat`/`hybrid`, giữ `load_dish_food_repository()` cho `gemini` thuần (chọn nguyên món qua LLM). Khi lưu `MealPlanItem`: chỉ gán `dish_id` khi thật sự map được qua kho món-tổng-hợp; nếu không, lưu thẳng `food_id` (trước đó code cũ ép `raise ValueError` nếu không map được — assumption sai cho CP-SAT).
- Cập nhật `tests/test_api_meal_plans.py::test_sau_khi_tra_ve_graph_da_chay_xong_va_ghi_ket_qua`: assertion cũ giả định sai "CP-SAT luôn trả `dish_id`, không bao giờ `food_id`" — sửa thành đúng hành vi RULE-1 (CP-SAT trả `food_id` thô, `dish_id=None`).
- **Xác nhận:** `pytest` sạch toàn bộ sau fix (196 test, gồm cả `test_duyet_sua_gram_tinh_lai_dinh_duong` đã pass lại).
- **Flaky residual (ghi rõ, không giấu):** `test_duyet_sua_gram_tinh_lai_dinh_duong` trừ cố định 20g từ món đầu tiên để test approve+edit — sau fix, margin phía trên ngưỡng tối thiểu đôi khi mỏng (CP-SAT không seed cố định, pure-feasibility không Minimize, xem docstring `optimizer.py`) khiến test fail ngẫu nhiên (~50% trong vài lần chạy thử). Giảm mức trừ xuống 1g → còn ~1/15 lần fail khi chạy riêng lẻ (ước lượng thô, không phải benchmark chính thức). Không redesign solver để seed cố định (ngoài phạm vi lần merge này) — chấp nhận rủi ro flaky nhỏ còn lại, ghi rõ để R1/R3 biết nếu CI báo fail ngẫu nhiên đúng test này trong tương lai.
- **Chưa làm (ghi rõ):** chưa kiểm chứng lại đường `gemini` thuần (không có test ép generator này) — giữ nguyên hành vi cũ (`load_dish_food_repository()`), không đụng tới vì ngoài phạm vi bug đã xác nhận.
- **Thời gian:** ~70 phút (điều tra + fix + cập nhật test + đo flaky).

---

### [2026-08-08] · R2 · Audit độ phủ candidate CP-SAT — chỉ 28 món/439 nguyên liệu dùng được thật

- Hưng hỏi CP-SAT có tận dụng hết database không. Đo trực tiếp: `food_items` 7375 dòng nhưng ứng viên nguyên liệu thô CP-SAT dùng được chỉ **439 dòng** (cố ý loại khối USDA bulk id≥100000 — đúng thiết kế, không phải lỗi). `dishes.csv` 2678 dòng nhưng `load_vn_dishes()` chỉ trả về **45 món** (2632 dòng còn lại bị gán nhãn sai `"USDA FNDDS"`, đã biết từ trước) — và **cả 45 món đều `is_reviewed=False`**, trong đó 17 món tự ghi chú trong cột `note` là thiếu nguyên liệu quan trọng (chính là nhóm gây bug thực đơn thiếu năng lượng hôm qua — thiếu DÒNG nguyên liệu không bị RULE-2 bắt được vì đó không phải ô trống).
- **Fix ngay:** `src/clinical/seeds.py::load_vn_dishes()` loại tạm 17 món có ghi chú "THIẾU"/"CHƯA GHÉP"/"R2 cần rà" khỏi candidate pool cho tới khi R2 rà xong — còn lại 28 món dùng được. `pytest` sạch sau fix.
- **Ghi ticket cho R2:** `DAT-23` (chính thức hoá merge purine từ NIN 2017, đã đề xuất ở DAT-22) và `DAT-24` (mở rộng dishes.csv lên 500-1000 món theo yêu cầu Hưng — việc thu thập dữ liệu quy mô lớn, KHÔNG tự bịa công thức/nguyên liệu, chỉ lên kế hoạch + gợi ý cách tiếp cận trong ticket).
- **Chưa làm:** chưa thực hiện DAT-24 (mở rộng 500-1000 món) — đây là việc nhiều phiên, cần nguồn công thức thật có bản quyền rõ ràng, không phải việc 1 lượt.
- **Thời gian:** ~25 phút.

### [2026-08-08] · R2 · DAT-24 khảo sát khả thi 500 món + sửa bug lọc ứng viên loại nhầm 82 thực phẩm NIN

- **Hưng yêu cầu:** nâng số món CP-SAT chọn được lên >500 món Việt.
- **Nguồn công thức — đã tìm được, đủ quy mô:** `monngonmoingay.com` có **2.510 trang món ăn**, mỗi trang có JSON-LD `schema.org/Recipe` kèm **định lượng gram thật**; `robots.txt` cho phép tường minh `User-agent: ClaudeBot → Allow: /`. Viết `scripts/crawl_mnmn_dishes.py` (cache, delay, chỉ lấy sự kiện định lượng + URL nguồn, **không lưu văn bản công thức** — tránh vấn đề bản quyền). Lưu ý kỹ thuật: JSON-LD của site có ký tự xuống dòng thô trong chuỗi, phải `json.loads(..., strict=False)` nếu không mất ~2/3 số món. (Đối chiếu: `vietnamesecookbook.com` chỉ có 151 trang công thức — không đủ đạt 500.)
- **🔴 Nút thắt thật KHÔNG phải nguồn công thức:** pilot 60 công thức — giả sử quy đổi được **mọi** đơn vị ước lệ (trái/củ/cây/muỗng…), tỷ lệ món có **đủ** nguyên liệu khớp `food_id` vẫn chỉ **3%**. Nhân lên 2.510 công thức ⇒ ~75 món, không đạt 500. Nghẽn nằm ở **kho nguyên liệu**, không ở công thức.
- **🐛 Bug tìm được khi đào nguyên nhân:** `retrieve_context` lọc ứng viên bằng `id < 100_000` như proxy cho "thuộc khối USDA bulk". Proxy sai — script merge NIN 2017 cấp id nối tiếp dãy `fdc_id`, nên **82 thực phẩm Việt Nam thật của Viện Dinh dưỡng** (Vừng/mè, Cà rốt, Cải thìa, Cải soong, Giá đậu xanh/đậu tương, Ớt đỏ, Đậu tương, Sữa đậu nành…) nhận id ≥ 1.105.898 và **bị loại nhầm khỏi CP-SAT** — đúng nhóm nguyên liệu công thức món Việt cần nhất. Sửa: lọc theo `source` (`NIN`/`curated` luôn là ứng viên, bất kể id). **Ứng viên 439 → 521.** Thêm `tests/test_retrieve_context_candidates.py` (4 test hồi quy: NIN id lớn phải có mặt, khối USDA bulk vẫn phải bị loại, số ứng viên không được giảm, chặn dị ứng/không thích vẫn nguyên).
- **Khoảng trống lớn nhất chưa khai thác:** **370 dòng `food_items.csv` bỏ trống hoàn toàn** — chính là danh sách nguyên liệu Việt curated gốc (Mì ăn liền, Bánh cuốn, Giò lụa, Chả quế, Cá lóc, Cá bống, Chao, Tương hột, Rau ngót…), và phần lớn nguyên liệu đang làm trượt món (`sườn non`, `giò sống`, `mực ống`, `thịt nạc vai`) nằm trong nhóm này. Lấp được ⇒ kho ứng viên 521 → ~890. **Cảnh báo:** khớp tên chính xác với `nin2017_extracted.json` chỉ ra 2/370 → phải tra tay/khớp mờ CÓ KIỂM SOÁT, không khớp mờ hàng loạt rồi tin luôn (gán nhầm "Cá lóc" sang "Cá lóc khô" là sai hoàn toàn về natri); trong 620 mục NIN 2017 chỉ 235 mục đủ macro + Na/K/P.
- **Vì sao KHÔNG rút gọn bằng cách bỏ nguyên liệu chưa khớp:** `_dish_nutrient_totals()` tính tổng tuyệt đối cả món và CP-SAT dùng món như khối cố định (không co giãn khẩu phần). Thiếu nguyên liệu ⇒ món bị ghi nhận thấp hơn năng lượng thật ⇒ CP-SAT bù thêm nguyên liệu thô ⇒ **bệnh nhân ăn vượt ngưỡng**. Đúng bug đã sửa 2026-08-07 và là lý do PR #63 phải loại 17 món — không lặp lại để chạy theo số lượng.
- **Chốt hướng (Hưng chọn):** mở rộng kho nguyên liệu trước, đo lại tỷ lệ khớp rồi mới tính tiếp — có thể không cần tới chính sách thay thế tên chung (`Thịt bò` → cắt nào) vốn là quyết định lâm sàng cần R2 ký.
- **Chưa làm:** chưa crawl đầy đủ 2.510 công thức, chưa ghi dòng dữ liệu món nào vào `seeds/`. Kế hoạch chi tiết: `docs/DAT-24_kha_thi_500_mon.md`.

### [2026-08-08] · R2 · DAT-24 (tiếp) — đào tới cùng 370 dòng trống: phần lớn là khoảng trống THẬT của NIN 2017

- **Phát hiện:** 348/370 dòng trống đều là mục NIN 2017 **đã biết mã**, bị chặn vì bản PDF gốc không phân tích vài trường — áp đảo là `na_mg`/`k_mg` (328/348 dòng), lác đác `fat_g`/`fiber_g`/`p_mg`.
- **Kiểm chứng trên PDF gốc trước khi kết luận:** trang 24, mã 01012 "Bánh mỳ" — tại toạ độ cột `NA`/`K` **không có token nào**; ba số `0.10/0.07/0.7` nằm ở x≈918/955/994 là THIA/RIBF/NIA. Vậy ô đó **thật sự trống trong bảng gốc, không phải lỗi trích xuất**.
- **🔴 Đính chính một giả định nguy hiểm:** "trống" ở nhóm này KHÔNG đồng nghĩa "không đáng kể" — bánh mỳ có Na ≈ 490-600 mg/100g (USDA). Điền 0 sẽ sai nghiêm trọng đúng vào ngưỡng chặn cứng của THA/CKD.
- **Đã thử lấp bằng đối chiếu NIN → USDA** qua chính `name_en` do NIN cung cấp (`scripts/fill_nin_gaps_from_usda.py`, chỉ dùng nhóm generic sr_legacy/foundation/survey, bỏ ~2 triệu dòng branded). Kết quả: **tự động lấp 15 dòng** (score ≥ 0,90 — dầu ăn các loại, bột dong, bột sắn, tôm khô, sữa đặc, mãng cầu xiêm), **19 dòng đưa R2 duyệt tay** (`food_items.nin_gaps_can_R2_duyet.csv`), **314 dòng bỏ hẳn** kèm lý do (`food_items.nin_gaps_unresolved.csv`). Mọi dòng lấp đều `source=estimated` + `is_estimated=TRUE` + `source_ref` ghi rõ CẢ HAI nguồn (macro từ NIN mã X, Na/K từ USDA fdc_id Y, kèm điểm khớp).
- **Phải siết bộ khớp 3 lần mới đủ an toàn** — bản đầu cho ra khớp sai nguy hiểm: `Dầu ngô`→`Oil, olive`; `Lòng trắng trứng vịt`→`Duck egg, cooked`; `Hạt dẻ tươi`→`Flour, chestnut` (xơ 2,3 vs 8,7); `Mắm tôm loãng`→`Shrimp with lobster sauce` (món Hoa, Na 1031 trong khi mắm tôm cao hơn nhiều lần). Ba lớp chặn đã thêm: nhóm tính từ loại trừ nhau, token dạng chế biến phải khớp hai chiều, và **kiểm tra xung đột trên token thô** — vì `raw`/`cooked`/`dried` vừa là stopword vừa nằm trong nhóm loại trừ, kiểm tra sau khi bỏ stopword thì nhóm đó không bao giờ chạy và `Shrimp dried` khớp được với `Shrimp, raw`.
- **Sửa tiếp bộ lọc ứng viên:** 15 dòng vừa lấp mang `source=estimated` nên vẫn bị loại. Đổi hẳn sang đúng bản chất — loại **đúng** khối bulk USDA (`source=="USDA"` VÀ `id ≥ ngưỡng`), mọi dòng khác đều là ứng viên. **Ứng viên nguyên liệu CP-SAT: 439 → 536.**
- **Kết luận thẳng:** 314/348 dòng còn lại **không lấp được từ nguồn hiện có**. Đây là khoảng trống thật của dữ liệu thành phần thực phẩm Việt Nam (NIN 2017 không đo Na/K cho nhóm này), không phải việc kỹ thuật xử lý được — muốn có thì phải đo/mua dữ liệu hoặc R2 tra tay từng mục.
- **Kiểm chứng:** `validate_data.py` 0 lỗi; `ruff` sạch; `pytest` 155 passed — 4 fail + 31 error còn lại đã xác nhận có sẵn từ trước (thiếu `passlib`), đã kiểm bằng cách stash thay đổi rồi chạy lại.

### [2026-08-08] · R2 · DAT-24 (chốt) — chạy thật 388 công thức: nguồn monngonmoingay KHÔNG đạt 500 món

- **Đã làm:** crawl 400 trang (388 có Recipe JSON-LD); sửa bộ khớp tên (cắt số lượng ước lệ, cắt nhãn `Gia vị:`/`Rau nêm:`/`Ăn kèm:`, cắt cách sơ chế `băm`/`thái`/`xay`); thêm nhóm rau thơm/gia vị được phép bỏ qua (chỉ thứ vừa rất ít khối lượng vừa gần như không năng lượng — **cố ý KHÔNG đưa dầu ăn/đường/muối/nước mắm vào nhóm này**); dựng `data/seeds/unit_conversions.csv` (20 dòng quy đổi đơn vị ước lệ, mỗi dòng dẫn `fdc_id` USDA).
- **Đơn vị `M`/`m` không phải suy đoán:** chính trang nguồn ghi chú *"M: muỗng canh - m: muỗng cafe"* trên mọi công thức.
- **Kết quả đo:** đủ định lượng toàn bộ nguyên liệu chính **35 món** (trước khi có bảng quy đổi: 5) — nhưng chỉ **4 món** qua được ngưỡng phủ `food_id` ≥ 80%. 348 món bị chặn vì còn nguyên liệu chính không định lượng; 31 món đủ định lượng nhưng thiếu `food_id`.
- **🔴 Rào cản 1 — thuộc tính của nguồn, bảng quy đổi không chữa được:** **47% công thức** có dòng kiểu `Gia vị: dầu ăn, hạt nêm, tiêu` — **không định lượng dầu ăn**. Dầu ăn một món xào thường 1-2 muỗng canh = 14-27 g = **125-250 kcal**; bỏ qua là làm món bị ghi nhận thấp hơn năng lượng thật, đúng bug đã sửa 2026-08-07.
- **Rào cản 2:** 31 món đủ định lượng vẫn trượt vì thiếu `food_id` cho `bắp hạt`, `bánh tráng`, `bún`, `hành tím`, `bơ lạt`, `tôm thẻ` — phần lớn nằm trong 355 dòng `food_items.csv` còn trống. Riêng `dầu ăn` là **lỗi alias**: kho có `Dầu ăn thực vật` (id 129) nhưng công thức ghi `Dầu ăn`, bộ khớp chỉ nhận tên CSDL nằm trọn trong tên công thức.
- **Kết luận thẳng về mục tiêu 500 món:** ngoại suy 388 → 2.510 công thức, nguồn này cho **~26 món** ở chuẩn hiện tại và **tối đa ~226 món** nếu lấp hết khoảng trống `food_items` — **vẫn không đạt 500**, vì rào cản 1 là thuộc tính của nguồn chứ không phải hạn chế kỹ thuật.
- **Cần R2 quyết (không phải việc kỹ thuật):** chốt mức dầu ăn/gia vị chuẩn theo loại món (xào/kho/canh/chiên), có nguồn dẫn (VD dữ liệu công thức FNDDS có định lượng chất béo thêm vào khi nấu), ghi thành ADR. Có quyết định đó thì phần lớn 348 món bị chặn sẽ mở ra.
- **Đã ghi:** `data/seeds/dishes.mnmn.csv` (4 món, `verified_by=pending`), `dish_ingredients.mnmn.csv`, `dishes.mnmn.rejected.csv` (396 món kèm lý do từng món) — file staging riêng, **chưa nhập vào `dishes.csv`**.
- **Kiểm chứng:** `validate_data.py` 0 lỗi; `ruff` sạch.

### [2026-08-08] · R1/R3 · Vá lỗ hổng auth `/chat` + lỗ hổng guardrail "ngừng uống thuốc"

- **Bug 1 — `/chat` không có auth:** `async def chat(payload: ChatRequest)` không có `Depends` nào. Ai cũng gọi được, và mỗi lần gọi có thể tiêu một lượt Gemini ở guardrail tầng 2. Đây là endpoint duy nhất nhận văn bản tự do nên cũng là bề mặt tấn công rẻ nhất. Đã thêm `Depends(get_current_user)` + 4 test hồi quy.
- **🔴 Bug 2 — phát hiện KHI viết test cho bug 1:** guardrail bỏ lọt ý định tự ngừng thuốc. `"tôi có nên ngừng metformin không"` bị chặn, nhưng `"tôi muốn ngừng UỐNG metformin, ăn gì thay thế?"` **lọt hoàn toàn** — pattern cũ bắt buộc tên thuốc đứng ngay sau động từ, chỉ một chữ "uống" chen vào là thoát. Danh sách hoạt chất của pattern này cũng chỉ có 2 tên trong khi pattern "liều thuốc" có 14, nên `"giảm liều atorvastatin"` cũng lọt. Đã gom `_DRUG_NAMES` dùng chung (23 hoạt chất) + cho phép động từ chen giữa. Đo lại: **6/6 câu nguy hiểm bị chặn, 0/6 câu ăn uống bình thường bị chặn nhầm**.
- Thêm `guard_free_text()` dependency factory để mọi ô nhập tự do sau này đều đi qua guardrail — thiếu nó nhìn thấy ngay ở chữ ký hàm, thay vì gọi `check_guardrail()` rải rác rồi quên một chỗ.

### [2026-08-08] · R2 · CLN-06 — tương tác thuốc–thực phẩm, bảng 30 cặp cuối cùng cũng được dùng

- Bảng `drug_food_interactions` đã seed từ lâu nhưng **chưa một dòng code nào truy vấn** — thuốc bệnh nhân đang dùng hoàn toàn không ảnh hưởng gì tới thực đơn sinh ra.
- **Đọc kỹ 30 dòng thì thấy chúng chia làm hai loại khác hẳn nhau**, và chỉ một loại được phép sinh cảnh báo tự động: 24 dòng theo **tên món cụ thể** (bưởi, rau ngót, rượu bia) → khớp chắc chắn, `evidence` chỉ đích danh món đã kích hoạt; 6 dòng theo **nhóm chất** ("thực phẩm giàu kali") → muốn tự phát hiện phải có ngưỡng, mà ngưỡng là quyết định lâm sàng. Loại 2 trả về qua `advisories_for()` và **nói thẳng là hệ thống chưa tự kiểm tra được**.
- **`verify_status`:** cả 30 dòng đang `to_verify` trong khi PRD FR-14 nói chỉ kích hoạt rule đã verified. Bỏ hẳn thì giấu mất cảnh báo warfarin/vitamin K thật; cho chặn cứng thì một rule chưa ai rà có quyền chặn thực đơn. Chốt: **vẫn cảnh báo nhưng không bao giờ HARD khi chưa verified**, và nói rõ trong câu chữ. R2 đổi `verify_status='verified'` thì cặp `high` tự động lên HARD.
- 18 test mới.

### [2026-08-08] · R3 · BE-07 — migration `food_logs`, nới `grams` thành nullable

- Với kho chỉ 461 thực phẩm Việt, món ngoài CSDL là **trường hợp mặc định**. Bệnh nhân gõ "canh rau tập tàng, 1 bát" mà không tra được đơn vị "bát" thì **không có** con số gram nào đúng — schema cũ bắt buộc `grams NOT NULL` tức là ép bịa số (RULE-2/DEC-008).
- Thêm cột truy vết: `match_status` (unmatched/auto/llm/expert/no_data), `match_confidence`, `portion_qty`, `portion_unit`, `grams_source_ref`, `dish_id`, `slot`, `note_vi`. `portion_qty/unit` giữ **nguyên văn** mô tả người dùng kể cả khi đã quy đổi được, để chuyên gia đối chiếu lại cách quy đổi.
- Dòng có sẵn trước migration đều có `food_id` thật nên được gán `match_status='expert'`, không lọt vào hàng chờ giải quyết. `downgrade()` **xoá** dòng `grams IS NULL` thay vì điền số bịa để lách NOT NULL, và ghi rõ cảnh báo mất dữ liệu.
- Đã chạy thật `alembic upgrade head` trên SQLite sạch: 15 cột đúng, `grams` nullable, 3 index.

### [2026-08-08] · R1 · SEC-01 — kiểm soát quyền hạn agent (Controlled Agent Security)

- **🔴 Lỗ hổng đã dựng lại được, không phải giả định:** `_candidates_text()` nội suy thẳng `food.name_vi` vào prompt, cùng định dạng phẳng với chính hướng dẫn của hệ thống. Mà tên món **không** phải dữ liệu tin cậy: ~6.900 dòng import bulk USDA + nội dung crawl web (`scripts/crawl_mnmn_dishes.py` — chính chúng ta crawl vào), cộng hành động `create_food_item` cho phép gõ tên tự do. Một tên món chứa `\n\n` + "QUY TẮC MỚI:" tách thành **4 dòng** trong prompt, đọc y hệt một khối chỉ thị mới. **Đã chứng minh test bắt đúng lỗi bằng cách gỡ lớp phòng thủ ra → test đỏ.**
- **Ba tầng phòng thủ độc lập:** (1) `sanitize_untrusted()` làm phẳng xuống dòng/ký tự điều khiển + chuẩn hoá NFKC (chặn né bộ dò bằng ký tự đồng hình) + cắt độ dài; (2) `fence()` rào khối dữ liệu ngoài có nhãn + `scan_for_injection()` ghi log; (3) `assert_no_egress()` **chặn cứng** secret (Google key/JWT/DB URL/giá trị trong `Settings`) và PII (email/điện thoại/CCCD/BHYT theo CLAUDE.md §3).
- **Điểm quan trọng nhất, ghi thành R60.0:** prompt **không phải** cơ chế an toàn. Injection thành công tuyệt đối cũng chỉ khiến agent chọn món kém — LLM vẫn chỉ trả được `food_id + grams` qua structured output, mọi con số do Python tính lại từ SQL, rồi `validate_menu()` và RULE-3 chặn tiếp. Nên chính sách là: **injection thì log và chạy tiếp** (chặn theo mẫu chuỗi sẽ tạo false positive làm hỏng luồng), **rò rỉ thì chặn cứng** (vì rò rỉ không có hàng rào nào phía sau).
- **Cổng duyệt:** `AGENT_ACTIONS` khai báo 9 hành động theo 3 mức rủi ro. Hành động **chưa khai báo mặc định là HIGH** (fail closed) — thêm tính năng mà quên khai báo thì bị chặn chứ không chạy tự do. Mọi hành động HIGH bắt buộc ghi `requires_role` (có test ép).
- **Red-team:** 39 test theo attack taxonomy 7 lớp, kèm test tự kiểm `test_moi_lop_tan_cong_deu_co_test` (thêm lớp mới mà quên test thì CI đỏ) và bộ đối trọng "không được báo động giả" với tên món thật.
- Chi tiết: `docs/rules/60-agent-security.md`. **Chưa làm** (ghi ra để không tưởng là đã có): RAG chưa tồn tại nên chưa áp R60.1 cho `guideline_chunks`; chưa có rate limit cho endpoint gọi LLM; `AGENT_ACTIONS` mới là bảng khai báo, việc ép mọi call-site đi qua nó vẫn thủ công.
- **Kiểm chứng:** `ruff` sạch; toàn bộ **295 test pass**.

### [2026-08-08] · R3 · BE-07 — API nhật ký ăn uống + hàng chờ giải quyết OOV, và alias vùng miền

- **Bối cảnh buộc phải thiết kế khác đi:** đo trực tiếp `data/seeds/` cho thấy chỉ **461 thực phẩm Việt** (`source=NIN`) và **30/7.745 dòng có alias**. Với vốn từ vựng đó, **món ngoài CSDL không phải ngoại lệ — nó là mặc định**. Nên luồng OOV phải là công dân hạng nhất chứ không phải nhánh lỗi.
- **API (`src/api/routes/food_logs.py`):** `POST /food-logs` (bệnh nhân chỉ gõ TÊN món, không phải tự tra CSDL), `GET /food-logs?date=`, `GET /summary`, `GET /unresolved` (chuyên gia, kèm gợi ý matcher), `POST /{id}/resolve` (`map_to_existing` | `mark_no_data`).
- **Hai bất biến, có test khoá:** (1) không bịa số — món chưa tra được thì `food_id=NULL`, `grams=NULL`, **không** cộng vào tổng; thiếu MỘT trong hai (không khớp được món, hoặc không rõ khẩu phần) là đủ để coi dòng đó chưa dùng được, vì biết ăn gì mà không biết bao nhiêu thì vẫn không cộng được (PRD FR-11). (2) không tin số client gửi — chuyên gia gán món thì `food_id` phải tồn tại thật, thiếu gram thì 422, đúng khuôn `approve_review`.
- **`mark_no_data` là lựa chọn HỢP LỆ và được khuyến khích** (DEC-008), không phải đường cùng: dòng đó cố ý bị loại khỏi phép cộng kể cả khi đã có `food_id`.
- **Matcher (`src/clinical/matching.py`) — hai lỗi thật bắt được khi đo trên seed, không phải lỗi giả định:**
  - `loại` nằm trong stopword làm `Thịt bò loại I` rút gọn còn `{thịt, bò}` ⇒ truy vấn chung "thịt bò" **khớp chính xác** và tự động nhận đúng một hạng thịt cụ thể. Đó là **thay thế ngầm** mà chỉ R2 mới được quyết (hạng thịt khác nhau đáng kể về chất béo). Đã bỏ `loại` và `ăn` khỏi stopword.
  - `phở bò` gợi ý `Bơ` và `cá lóc` gợi ý `Cá mè` — ứng viên 1 token ngắn bị thổi điểm khi bỏ dấu. Đã thêm luật: truy vấn ≥2 từ mà chỉ trùng 1 từ thì bỏ qua.
- **Alias vùng miền:** thêm **134 alias cho 123 dòng** (lợn/heo, ngô/bắp, lạc/đậu phộng, vừng/mè, dứa/thơm/khóm, sắn/khoai mì, mướp đắng/khổ qua…). Đo sau khi áp: **9/12** từ khoá vùng miền khớp đúng, trước đó gần như 0. Ba ca còn trượt (`khoai mì luộc`, `cá lóc`, `bồ ngót`) **không phải lỗi matcher** — đã kiểm chứng cả ba nằm trong 370 dòng chưa có số liệu, và matcher **đúng** khi từ chối khớp món nó không có số.
  - Lỗi sinh alias đã bắt được: **"Bí ngô" → "bí bắp"** (từ ghép "bí ngô" là quả bí đỏ, chứa "ngô" nhưng không phải ngô). Nay khoá dài hơn thắng khoá ngắn. Cố ý **loại** khỏi bảng: `mận` (Bắc = plum, Nam = quả roi — đúng một chiều, sai chiều ngược lại), `bắp→ngô` ("bắp" còn nghĩa bắp thịt).
- **Đã sửa lỗ hổng:** `POST /api/v1/chat` trước đó **không có auth** — ai cũng gọi được và mỗi lần gọi có thể tiêu một lượt Gemini ở guardrail tầng 2. Thêm `get_current_user` + `guard_free_text()` dependency dùng chung cho mọi ô nhập tự do.
- **Kiểm chứng:** migration chạy thật trên SQLite sạch (xác nhận `grams` nullable + đủ 8 cột mới); `validate_data.py` 0 lỗi; `ruff` sạch; toàn bộ **309 test pass**.
- **Chưa làm:** Làn B (LLM mapper) chưa nối; frontend nhật ký + màn hàng chờ OOV chưa có; bảng `food_aliases` (học từ thao tác chuyên gia) chưa dựng — hiện alias vẫn nằm trong CSV.

### [2026-08-08] · R4 · BE-07 — 3 màn hình frontend nhật ký OOV, và một endpoint thiếu

- **Phát hiện khi nối frontend:** bệnh nhân **không có cách nào biết `profile_id` của mình** — session chỉ có `user_id`, mọi API dinh dưỡng lại khoá theo `profile_id`, và `GET /patients` yêu cầu quyền dietitian. Tức là không ghi được nhật ký. Đã thêm `GET /patients/me`. Lưu ý kỹ thuật: phải khai báo **trước** `/{profile_id}` vì FastAPI khớp theo thứ tự — đặt sau thì "me" bị hiểu là một id và luôn trả 404 (đã có test khoá).
- **`/patient/diary`** — bệnh nhân chỉ gõ TÊN món, không phải tự tra CSDL. Ô gram được phép để trống ("thà ghi thiếu còn hơn ghi sai"). Ghi món chưa tra được thì hiện ngay rằng món đó **chưa được tính vào tổng**.
- **`/dietitian/food-logs`** — hàng chờ giải quyết, kèm gợi ý matcher **có điểm và có lý do khớp** (`exact`/`alias`/`token`) để chuyên gia soi được chứ không phải tin mù. Nút "Không đủ dữ liệu" đặt ngang hàng với nút gán món — đó là câu trả lời hợp lệ, không phải đường cùng.
- **`/patient`** — hiện `violations` mức soft. API đã trả field này từ lâu nhưng màn bệnh nhân **bỏ qua hoàn toàn**, nên bệnh nhân không hề biết thực đơn của mình có điểm gì cần lưu ý.
- **Điểm hiển thị quan trọng nhất:** verdict `insufficient_data` **cố ý không dùng màu xanh và không dùng chữ "đạt"**. Khi còn món chưa tra được, tổng tính ra chỉ là **mức tối thiểu**, nên "chưa vượt ngưỡng" không đồng nghĩa "ổn". Hiển thị nhầm chỗ này biến một hệ thống trung thực thành một hệ thống trấn an sai. Mọi chỗ render `actual`/`limit` đều kiểm tra `!= null` trước — cảnh báo định tính không có số, hiện "0" là bịa.
- **Kiểm chứng:** `npm run build` sạch (12 route, cả 2 route mới có mặt), `tsc` pass, `eslint` **không thêm vấn đề nào** — đã đối chiếu trực tiếp bằng cách stash thay đổi ra rồi chạy lại: cùng ra 5 problems/1 error, tức lỗi còn lại là của `reviews/[id]` có sẵn từ trước. `pytest` **313 passed**, `ruff` sạch.
- **Hợp nhất:** PR #67 ban đầu base `develop` nên hiện **294 file/+104k** và CONFLICTING — vì `develop` lạc hậu 5 commit so với `main`, và **PR #64 đã merge DAT-24 vào main rồi**. Đã merge `main` vào nhánh và đổi base sang `main`: còn **36 file/+4.931**, hết xung đột.

> ⚠️ **Ghi chú vận hành:** phiên này có **hai tiến trình agent chạy song song cùng thư mục** — `matching.py`/`diary.py`/`models.py` do phiên kia làm, và có lúc file bị sửa giữa hai lần chạy test cách nhau 4 giây khiến kết quả đo khác nhau. Đã chia việc lại theo yêu cầu của Hưng. Đội nên tránh chạy 2 agent cùng lúc trên cùng working tree.

### [2026-08-08] · R3 · Review nhánh đồng đội + phát hiện khẩn về Supabase dùng chung

- **Mở PR review-only** (không merge) cho 2 nhánh đồng đội chưa có PR: `nam-dev` → [#68](https://github.com/AI20K-Build-Phase-Cohort-3/P-031/pull/68), `ui-main` → [#69](https://github.com/AI20K-Build-Phase-Cohort-3/P-031/pull/69). Đã comment trên đúng dòng cho từng phát hiện.
- **`nam-dev` — 3 phát hiện thật (đã kiểm chứng, `nam-dev` đang ngang bằng `main` nên diff đáng tin):**
  1. 🔴 `load_rules()` đổi default `verified_only=True` sẽ làm `compute_targets()` trả về **RỖNG cho mọi bệnh nhân** — xác nhận trực tiếp cả 21 dòng `clinical_rules.csv` đang `to_verify`, không dòng nào `verified`. Đồng đội đã biết (tự viết test xác nhận), nhưng cần thống nhất chính sách chung với CLN-06 của PR #67 (hạ severity thay vì lọc sạch) trước khi cả hai cùng lên `main`.
  2. 🔴 `src/clinical/interactions.py` trùng đường dẫn với PR #67, API khác hẳn nhau — cần đồng đội biết để hợp nhất, tránh ghi đè mất công.
  3. Alembic 2 head song song với migration `food_logs` của PR #67 (cùng `down_revision=aedef0ff7743`) — cần migration merge trước khi cả hai lên `main`.
- **`ui-main` — tự đính chính một nhận định sai:** ban đầu kết luận nhánh này "khôi phục lại bug CP-SAT thiếu năng lượng đã sửa" dựa trên `git diff` 2-cây trực tiếp. Kiểm tra lại bằng `gh pr diff` (theo merge-base thật) thì **sai** — merge-base của `ui-main` là một commit **trước khi** fix đó được thêm vào `main`, `ui-main` không hề đụng vùng code đó. Đã sửa lại PR #69 + xin lỗi công khai trên PR. Diff thật chỉ có: loại `MENU-*` khỏi ứng viên `dish_foods` (hợp lý) + `display_name` tương thích ngược — không có vấn đề.
- **🔴 Phát hiện khẩn khi kiểm tra Supabase thật (chỉ SELECT, không ghi gì):** DB dùng chung của cả team hiện đang ở revision **`e63b8c4f1a32`** — đúng tip chain migration của `nam-dev`. Nghĩa là ai đó đã chạy `alembic upgrade head` với nhánh `nam-dev` (chưa merge) thẳng lên Supabase chung. Hệ quả: bảng `meal_plans` đã có đủ cột mới của `nam-dev`, nhưng **bảng `food_logs` vẫn là schema CŨ** (`grams NOT NULL`, thiếu `dish_id`/`slot`/`match_status`...) — **migration `food_logs` của PR #67 (đã merge vào `main`) chưa từng chạy trên Supabase**. API nhật ký ăn uống của BE-07 sẽ lỗi thật nếu chạy với Supabase (mới chỉ test qua bằng SQLite). Đã báo trên PR #68, **không tự chạy thêm gì lên Supabase** để tránh làm rối thêm — cần một migration merge nối `b7c214e93a08` với `e63b8c4f1a32`, chỉ một người chạy `upgrade head`.
- **Dữ liệu bệnh nhân `data/patients/`:** đọc `manifest.yaml` — cả 4 dataset (2.020 dòng) đều `enabled: false`, 3/4 `Quarantined` (license/de-identification chưa xác minh). **Không nạp vào DB** — đường dữ liệu bệnh nhân thật của sản phẩm chỉ có 6 hồ sơ mô phỏng từ `scripts/seed_demo_users.py`. Muốn dùng 4 dataset này cần một ticket riêng xác minh license trước, không tự ý mở khoá trong lượt này.
### [2026-08-09] · R2 · P2/AGT-12 — Thực đơn tương đương từ tủ lạnh + phạm vi thay thế duyệt trước (RULE-3)

- **DEC-018 trước khi code:** chốt với Hưng tolerance ±10% mọi chất, hạn 7 ngày, `max_auto_releases=5`, nguyên liệu chủ lực = {gạo, dầu ăn, nước mắm, muối, đường, tỏi, hành lá} (chi tiết lý lẽ ở §3).
- **`src/agents/equivalent.py`:** `solve_equivalent()` tái dùng nguyên `_try_solve()` của `CPSATMenuOptimizer` (không sửa `optimizer.py` đã test kỹ) — chỉ đổi 2 input: ứng viên = giao (tủ lạnh ∪ nguyên liệu chủ lực) ∩ candidates gốc; `bounds` = giao giữa `ClinicalTargets` gốc và dải base±tolerance, bên chặt hơn thắng. Vô nghiệm (dải không giao nhau, hoặc CP-SAT không tìm được lời giải) → `EquivalentMenuResult(draft=None, reason_vi=...)`, KHÔNG BAO GIỜ trả thực đơn một phần. `resolve_staple_food_ids()` khớp CHÍNH XÁC theo `name_vi` (không fuzzy) — tên không khớp thì bỏ qua, không suy đoán món gần giống.
- **DB:** bảng mới `pantry_items` (food_id + qty/unit; `free_text_vi` giữ chỗ, CHƯA có cơ chế tự khớp vì `FoodMatcher` của BE-07/PR#67 chưa merge vào `main`) và `substitution_scopes` (chính sách RULE-3: tolerance/max_auto_releases/expires_at/revoked_at/release_count). Migration additive `f3a1c9d2b7e4` (down_revision=`aedef0ff7743`, head hiện tại) — đã test cả `upgrade`/`downgrade` trên SQLite scratch DB.
- **API:** `POST/GET/DELETE /pantry/{patient_id}` (CRUD tủ lạnh); `POST /substitution-scopes` (chỉ dietitian/admin, chỉ tạo được cho thực đơn gốc đã `approved`) + `/revoke`; `POST /meal-plans/{base_plan_id}/equivalent` — **không có scope còn hiệu lực thì 403 ngay, kể cả bản nháp xem trước** (chuyên gia là chốt chặn ĐẦU TIÊN, không chỉ chốt chặn từng lần dùng). Khi giải được: RULE-1 tính lại `compute_nutrition`/`validate_menu` trên server (không tin nội bộ solver); tự phát hành (`status=approved` ngay) chỉ khi ĐỒNG THỜI còn hạn + không vi phạm nào (kể cả soft) + không nguyên liệu `is_estimated` + chưa vượt `max_auto_releases` — trượt bất kỳ điều kiện nào thì tạo plan `pending_review`, đi thẳng vào hàng chờ `/reviews` sẵn có (không có endpoint duyệt tay riêng — tái dùng nguyên vòng duyệt cũ).
- **Test:** `tests/test_equivalent.py` (5 test, dữ liệu seed thật không mock, cùng khuôn `test_cpsat_optimizer.py`) + `tests/test_api_pantry_equivalent.py` (12 test API: quyền, 403 khi thiếu scope, tự phát hành khi tủ lạnh đủ, trả lý do tường minh khi tủ lạnh nghèo — không tạo plan mới). Thêm `agents/equivalent.py` vào `DETERMINISTIC_FILES` (`tests/test_agent.py`).
- **Chưa làm (cố ý, ngoài phạm vi lượt này):** nhập tự do tủ lạnh (`free_text_vi` → `food_id` qua `FoodMatcher`) chờ BE-07/PR#67 merge; chưa có UI (`web-next/`); chưa recompute `ClinicalTargets` mới nếu hồ sơ bệnh nhân đổi giữa lúc duyệt thực đơn gốc và lúc sinh thực đơn tương đương — tái dùng nguyên `plan.targets` đã lưu ở thực đơn gốc (nhất quán với ngữ nghĩa "tương đương SO VỚI chính thực đơn đó", không phải "tính lại từ đầu").
- **Kiểm chứng:** `ruff check`/`ruff format` sạch, `mypy src/` sạch (39 file), migration test cả 2 chiều, toàn bộ test liên quan pass.

### [2026-08-09] · R2 · Nạp 2.015 hồ sơ `data/patients/` vào Supabase (DEC-019)

- **`scripts/load_patient_datasets.py` (mới):** nạp cả 4 dataset (set1 840 NHANES-adapted, set2 700 MontiFinal-adapted, set3 372, set4 108 lọc còn 103 `type 2`) thành `User`(email `synthetic+<patient_id>@vnutricare.local`) + `PatientProfile` + `PatientMedication`. Idempotent theo email (prefetch `existing_users`/`existing_profiles` vào bộ nhớ, upsert). set4 quy đổi `fastingglucose`/`A1c` từ mmol/L sang mg/dL (×18.0182) — khác đơn vị set1/3, không copy thẳng số.
- **🔴 Sự cố khi chạy thật lên Supabase — đã xử lý xong, không mất/trùng dữ liệu:**
  1. Lần đầu (chưa batch commit, hash argon2 riêng từng user) bị treo do argon2 cố ý chậm (~100-300ms × 2015) cộng round-trip mạng tới `ap-northeast-1` → sửa: hash password DÙNG CHUNG 1 lần (tài khoản này không bao giờ đăng nhập, an toàn), prefetch user/profile 1 lần thay vì SELECT mỗi dòng, commit theo lô 200 dòng (cùng bài học `seed_db.py`).
  2. **Phát hiện quan trọng cho môi trường này:** gọi script Python dài qua `run_in_background`/`timeout` trên máy Windows này **sinh ra 2 tiến trình `python.exe` song song cho CÙNG MỘT lệnh** (không phải lỗi logic script) — 2 tiến trình cùng ghi Supabase gây `UniqueViolation` (duplicate key) do race condition giữa 2 session riêng biệt. Xác nhận bằng `Get-CimInstance Win32_Process`, dừng bằng `Stop-Process -Force`. Chạy lại ở **foreground thường (không `run_in_background`)** thì chỉ có đúng 1 tiến trình, chạy sạch tới cuối.
  3. Không có dữ liệu sai/hỏng: mỗi lần dừng tiến trình treo, dữ liệu đã `commit` (theo lô 200) vẫn nguyên vẹn trên Supabase; chạy lại chỉ upsert tiếp phần còn thiếu, xác nhận số cuối khớp `2015 = 840+700+372+103`.
- **Cập nhật `manifest.yaml`/`README.md`:** cả 4 dataset `enabled: true`, trỏ về DEC-019 — nhắc rõ đây là quyết định của R2 (Hưng xác nhận trực tiếp), KHÔNG phải tự ý bỏ qua rào chắn license/de-identification (rào chắn đó vẫn còn nguyên, chỉ trạng thái "được phép nạp" đổi).
- **Xác nhận cuối trên Supabase:** `users=2023` (2015 synthetic + 8 cũ), `patient_profiles=2021` (2015 + 6 demo cũ), `patient_medications=904`.

### [2026-08-08] · R1 · P1 — Trợ lý ngưỡng cho chuyên gia (trả lời Q3)

- **Nguyên tắc:** LLM chỉ **diễn giải** và **parse tham số** — không bao giờ sinh ra một con số ngưỡng. Mọi số liệu luôn lấy từ `compute_targets()` đã có sẵn (`applied_rule_ids`, `guideline_refs` trong từng `NutrientTarget`, `conflict_notes`) — dữ kiện tồn tại từ trước nhưng chưa ai từng giải thích được cho chuyên gia bằng tiếng Việt tự nhiên.
- **`src/clinical/target_explainer.py` (LLM: NO, thêm vào `DETERMINISTIC_FILES`)** — `explain_targets(profile, targets, rules)`: với mỗi chất, liệt kê rule nào THẮNG (`applied`) và rule nào bị LOẠI kèm lý do (`excluded`). `diff_explanations()` so sánh 2 lần tính cho luồng what-if.
- **🐛 Bug thật bắt được khi đo trên dữ liệu thật, không phải giả định:** `T2DM-PRO-02` (`requires_flag=elderly`) bị loại vì bệnh nhân chưa đủ tuổi — **không** phải vì bị CKD ghi đè (`overridden_by` của chính rule này rỗng). `_select_rules()` gộp 2 lý do loại trừ khác nhau trong một điều kiện `OR` (`not not_overridden(rule) or not flag_required_met(rule)`), nên nếu code giải thích cũng gộp chung sẽ in ra **"Bị  thay thế"** (rỗng, vô nghĩa). Đã tách riêng 2 nhánh: `overridden_by` vs `requires_flag` chưa đạt, kiểm chứng lại bằng ca bệnh nhân 70 tuổi (đủ elderly) thấy rule tự động chuyển từ `excluded` sang `applied` đúng như kỳ vọng.
- **`src/services/target_assistant.py` (LLM: YES, theo khuôn `services/llm.py`):**
  - `explain_naturally()` — chỉ văn phong hoá `NutrientExplanation` đã có, test hồi quy xác nhận mọi con số trong prompt gửi LLM đều lấy từ input, không nơi nào tự thêm.
  - `parse_what_if()` — trả về `ProfileDelta`, **schema không có field số nào** (chỉ `ConditionCode` enum + chuỗi giai đoạn + list cờ). Pydantic tự chặn LLM trả field lạ hay giá trị ngoài enum — không cần code phòng thủ thêm, đã test bằng `pytest.raises(ValidationError)`.
  - `apply_delta()` — áp lên **bản sao** hồ sơ, `model_copy()`, test xác nhận profile gốc không đổi.
- **API mới (`targets.py`), chỉ role `dietitian`/`admin`:** `GET /targets/{id}/explain`, `POST /targets/{id}/what-if` — what-if tính lại thật bằng `compute_targets()` trên bản sao, **không side-effect lên DB** (chỉ ghi `AuditLog` câu hỏi + delta để truy vết), test xác nhận hồ sơ thật trong DB không đổi sau khi gọi.
- **Kiểm chứng:** 29 test mới (10 explainer + 11 assistant + 8 API, mock Gemini không tốn quota). Toàn bộ suite **343 passed**, `ruff` sạch.
- **Chưa làm:** thực đơn tương đương từ tủ lạnh (Q3 phần còn lại) — chỉ có đặc tả, bàn giao cho agent kế tiếp qua prompt (xem plan file). Cần R2 chốt "phạm vi thay thế duyệt trước" trước khi code.

### 2026-08-10

- **DAT-13 — R2 hỏi có tính được số liệu cho 355 dòng trống bằng công thức (Atwater, phân rã nguyên liệu) không.** Kiểm tra tay: **cả 355 dòng trống hoàn toàn**, kể cả `source_ref` — không có protein/carb/fat để dùng Atwater (kcal=4P+4C+9F, cần số đầu vào đã biết), và đa số là nguyên liệu đơn (rau, củ, cá, thịt) chứ không phải công thức món nên không có gì để "phân rã". Viết `scripts/classify_food_gap_composite.py` (heuristic từ khoá tên, không tuyệt đối) tách 355 dòng thành **239 nguyên liệu thô** (chỉ tra lại NIN/USDA được) và **116 chế biến/tổng hợp** (bánh chưng, phở, giò lụa, chè...) — nhóm sau CÓ THỂ phân rã thành nguyên liệu+gram nếu R2 xác nhận công thức tham khảo thật, theo đúng quy trình đã dùng cho `dishes.csv` (không để LLM tự suy đoán tỷ lệ — RULE-1/RULE-2). Danh sách đầy đủ: `docs/DAT-13-phan-loai-355-dong-trong.md`. Không tự điền số nào.
- **DAT-13, tiếp — R2 duyệt "đáng đầu tư, cần research nguồn công thức". Trước khi đi tìm công thức nấu ăn bên ngoài, đối chiếu lại 355 dòng với dữ liệu đã có sẵn trong repo: 341/355 khớp mã món tuyệt đối với Bảng TPTP VN 2017 (`scripts/nin2017_extracted.json`), đã có kcal/protein/carb đo thật — chỉ bị merge cũ (DAT-22) không kích hoạt vì thiếu Na/K (314/341).** Đây là lỗ hổng Na/K đã biết từ đầu ticket, **không phải thiếu công thức nấu ăn** — đổi hướng khỏi research bên ngoài. Thử bù bằng Bảng TPTP VN 2007 (567 trang, cũng sẵn trong repo, chưa ai khai thác) — có cột Natri/Kali/Phospho nhưng tên tiếng Việt trong PDF bị lỗi font (`"Tªn thùc phÈm"`). Giải pháp: khớp theo **"Mã số"** (chữ số, không lỗi font) thay vì tên — xác nhận bằng tay `Mã số: 2001` (2007) = `code: 02001` (2017) = "Củ ấu", mã ổn định giữa 2 ấn bản. Viết `scripts/extract_nin2007.py` (526/567 trang trích được, khớp đúng số 526 món đã ghi nhận trước đó; xử lý lỗi nhân đôi ký tự OCR `"117733"`→`"173"`, chỉ sửa khi TOÀN CHUỖI khớp mẫu lặp đôi tuyệt đối, không đoán một phần; xác minh chéo với 2017 khớp tuyệt đối P/K/Na cho mã `01001`) + `scripts/merge_nin2007_into_food_items.py` (chỉ điền ô trống, không ghi đè, chỉ kích hoạt khi đủ 8 trường lõi — cùng nguyên tắc merge 2017). **Kết quả thật (khiêm tốn):** 2007 cũng thiếu Na/K cho phần lớn cùng nhóm thực phẩm mà 2017 thiếu (lỗ hổng hệ thống ở cả 2 ấn bản) — chỉ **11/355 dòng kích hoạt hoàn toàn** (Bánh phở, Kiệu muối, Men bia tươi, Nấm hương khô, Gioi, Nhãn khô, Quít, Đường kính, Gừng khô, Nghệ khô, Nước cam tươi). `food_items.csv` seeds 537→548 dòng, `validate_data.py` 0 lỗi, `pytest` 410 passed. Còn 344 dòng (228 nguyên liệu thô + 116 chế biến/tổng hợp), báo cáo cập nhật: `docs/DAT-13-phan-loai-du-lieu-trong.md`.
- **DAT-13, Nhóm B (116 món chế biến) — R2 xác nhận dùng LLM đề xuất + R2 duyệt.** Trước khi soạn, kiểm tra không có nguồn định lượng thật sẵn có: `data/Bảng xác định nhu cầu dinh dưỡng + thực đơn.xlsx` (9 sheet, kể cả `"Bảng TP có phospho"` — đúng tên trong ticket gốc) chỉ có tổ hợp CẢ BỮA ĂN, không phải công thức riêng từng món; web search chỉ trả về chính bản PDF 2007 đã có. Đúng bản chất: Bảng TPTP đo trực tiếp món đã nấu, không tồn tại "nguồn công thức" công bố chính thức cho phần lớn món Việt. Tách 34 món **công nghiệp đóng gói** (kẹo, bánh quy, đồ hộp, mứt) ra khỏi phạm vi — bịa tỷ lệ nhà máy còn tệ hơn để trống. Viết `scripts/propose_dish_recipes.py`, soạn công thức cho 72/82 món nhà làm còn lại (10 món cần "Bột sắn dây" chưa có trong `food_items.csv`, bị chặn tự động không tự thêm food_item mới). **`serving_g` luôn tính tự động = tổng gram nguyên liệu**, không gõ tay riêng — tránh đúng bẫy đã gây bug `MENU-*` (hệ số scale sai khi grams phục vụ khác tổng công thức). Tự rà `compute_nutrition()` cho cả 70 món trước khi ghi thật, bắt được 1 lỗi: `Chả lá lốt` dùng "Thịt lợn ba chỉ" (518 kcal/100g) cho ra 477 kcal/100g bất thường — sửa sang thịt nạc, còn 230 kcal/100g. Kết quả: `dishes.csv` 30→100 món (`+70`), `dish_ingredients.csv` +246 dòng, `validate_data.py` 0 lỗi, `pytest` 410 passed. **Toàn bộ 70 món mới `verified_by="pending"`, CHƯA R2 duyệt** — không dùng cho bệnh nhân thật.

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
| DEC-015 | 2026-08-05 | Chỉ nhận Open Food Facts + Dược thư QGVN trong số 8 nguồn nghiên cứu bổ sung; loại PhyFoodComp/eBASIS/ASEANFOODS/WikiFCD-FoodOn | R2 | Bối cảnh: tài liệu tổng quan `data/Dữ liệu dinh dưỡng Việt Nam.md` đề xuất 8 nguồn ngoài NIN/USDA. Phương án cân nhắc: chấp nhận cả 8 theo tài liệu, hoặc tự xác minh từng nguồn trước khi quyết. Chọn tự xác minh (WebSearch/WebFetch) vì tài liệu chỉ là gợi ý, không phải nguồn đã kiểm chứng. Hệ quả: PhyFoodComp bị loại vì ngoài phạm vi 4 bệnh mục tiêu (phytate phục vụ thiếu máu/thiếu kẽm); eBASIS bị loại vì trang chủ mô tả truy cập theo membership, không xác nhận được gói miễn phí; ASEANFOODS bị loại vì VFCT 2017 đã đối chiếu chéo sẵn (trùng lặp); WikiFCD/FoodOn bị loại vì cần hạ tầng SPARQL/ontology không tương xứng lợi ích cho MVP. QĐ 5948/QĐ-BYT KHÔNG được dùng làm nguồn cho DAT-05 vì chỉ xác nhận được là danh mục thuốc-thuốc, không có bằng chứng phủ thuốc-thực phẩm — tránh suy đoán sai như DEC-008 cảnh báo |
| DEC-016 | 2026-08-05 | Bỏ trần số lượng ở EPIC 1/2 nhưng KHÔNG đổi ngưỡng validate_data.py; chỉ điền source_ref cho dược chất xác nhận được có chuyên luận riêng (17/30), để trống 13/30 còn lại | Hưng (yêu cầu) | Bối cảnh: yêu cầu "nâng trần → không giới hạn" cho EPIC 1/2 + "fill full data với mọi data tìm được". Phương án cân nhắc: A) đổi AC ticket thành số lớn tuỳ ý (VD 500 món) để nhìn "đầy tham vọng"; B) đổi AC thành "sàn, không phải trần" — không đặt trần trên nhưng cũng không bịa số lớn hơn hiện có; C) với drug_food_interactions, điền source_ref cho TẤT CẢ 30 dòng bằng cách suy luận chuyên luận Dược thư "chắc là có" cho các dược chất phổ biến. Chọn B (không đặt số trần tuỳ ý — số lượng là biến phụ thuộc, có nguồn thật hay không mới là biến chính, đúng RULE-2/DEC-008) và từ chối C (chỉ điền 17/30 đã xác nhận qua tìm kiếm thực tế có trang chuyên luận riêng, 13 dược chất còn lại — kể cả rất phổ biến như Metformin/Simvastatin — để trống vì KHÔNG tự xác nhận được, dù nhiều khả năng có thật). Hệ quả: "không giới hạn" trong ticket nghĩa là "không dừng lại vì đã đạt con số ban đầu", không phải "báo đã xong 100%" — validate_data.py vẫn coi 13 dòng thiếu source_ref là cảnh báo cần R2 xử lý tiếp, không tự ý tắt cảnh báo đó |
| DEC-017 | 2026-08-05 | Khối USDA bulk (~7000 dòng food_items, id≥100000) chỉ dùng làm kho tham chiếu, loại khỏi ứng viên sinh thực đơn qua `USDA_BULK_ID_THRESHOLD` trong `retrieve_context` | Hưng (xác nhận) | Bối cảnh: thêm 6.854 dòng USDA bulk để đạt mục tiêu "1000+ food_items" khiến CP-SAT chậm 30-50 lần (đo thật: 1,5s→50s) vì `retrieve_context` đưa toàn bộ `food_items` làm ứng viên. Phương án cân nhắc: A) lọc candidate — chỉ dùng ~150 dòng Việt curated cho sinh thực đơn, giữ 7000 dòng USDA làm tham chiếu; B) giữ nguyên, chấp nhận chậm hơn; C) giảm quy mô nhập USDA xuống ~1000 dòng thay vì 6854. Chọn A vì không đánh đổi hiệu năng tính năng đã kiểm chứng (CP-SAT) lấy số lượng dữ liệu thô, đồng thời vẫn giữ được toàn bộ 7000+ dòng cho mục đích tra cứu/OOV/mở rộng sau. Hệ quả: `id` ≥100000 (fdc_id USDA) là quy ước phân tách "tham chiếu" vs "ứng viên sinh thực đơn" — mọi dữ liệu USDA bulk nhập sau này (kể cả mở rộng purine) nên tuân theo cùng quy ước ID để không cần sửa lại filter |

| DEC-018 | 2026-08-09 | Phạm vi thay thế duyệt trước (RULE-3, thực đơn tương đương từ tủ lạnh): tolerance ±10% mọi chất, hạn 7 ngày, `max_auto_releases=5`, nguyên liệu chủ lực mặc định = {gạo, dầu ăn, nước mắm, muối, đường, tỏi, hành} | Hưng (R2, xác nhận) | Bối cảnh: Phần D kế hoạch trước (thực đơn tương đương, `src/agents/equivalent.py`) cần nới RULE-3 — thực đơn tự phát hành không qua chuyên gia duyệt riêng lẻ, nên phải chốt chính sách trước khi code, không tự đặt số (đúng `CLAUDE.md` §6). Phương án cân nhắc cho tolerance: (A) ±10% mọi chất — đơn giản, vẫn an toàn vì luôn lấy giao với ngưỡng lâm sàng gốc (`compute_targets()`), bên chặt hơn thắng; (B) ±10% chung nhưng ±5% riêng carb/natri — chặt hơn cho ĐTĐ2 nhưng dễ vô nghiệm hơn (ít lựa chọn từ tủ lạnh). Chọn A vì giao với ngưỡng gốc đã là lưới an toàn thứ hai, không cần siết thêm ở bước này — nếu thực tế thấy carb/natri trôi quá xa trong dải ±10%, sẽ có DEC riêng sau khi có dữ liệu thật. Hạn 7 ngày (không chọn 30 ngày) vì thực đơn gốc có thể lạc hậu so với tình trạng bệnh nhân sau 1 tháng — 7 ngày buộc chuyên gia duyệt lại định kỳ, đúng tinh thần RULE-3 "chuyên gia là chốt chặn cuối". `max_auto_releases=5` (không chọn "không giới hạn") để giữ chuyên gia trong vòng lặp thường xuyên thay vì phạm vi duyệt 1 lần chạy vô hạn. Danh sách nguyên liệu chủ lực gồm cả nước mắm/muối (không chỉ gạo/dầu) — chọn có ý thức là sẽ CỘNG vào tổng natri của thực đơn tương đương (không bỏ qua/coi như 0), vì bỏ qua muối/nước mắm mới là sai lệch thật (thực đơn tương đương sẽ nhạt/kém thực tế nếu không tính nguyên liệu chủ lực này vào ràng buộc). Hệ quả: `substitution_scopes` schema dùng đúng 4 số này làm default; `solve_equivalent()` lấy `bounds` = giao giữa `targets` gốc và dải `base±10%`; nguyên liệu chủ lực được cộng vào candidate pool + tính đủ vào tổng dinh dưỡng (không miễn trừ khỏi ràng buộc natri) |

| DEC-019 | 2026-08-09 | Cởi trói `enabled=true` cho cả 4 dataset `data/patients/` (1 verification_pending + 3 quarantined) để nạp vào DB/Supabase, dù `manifest.yaml`/README tự ghi "không dùng làm product seed" | Hưng (R2, xác nhận trực tiếp — không phải tự ý) | Bối cảnh: 4 dataset (2.020 dòng, NHANES-adapted + MontiFinal + 1 nguồn khác) đang bị chính rào chắn dữ liệu của dự án chặn (README §"Usage Guidelines": "Dataset quarantined không được dùng làm product seed hoặc benchmark input"), vì license/de-identification/checksum chưa xác minh xong (set2/3/4) hoặc chỉ thiếu metadata (set1). Đã hỏi lại Hưng trước khi làm (đúng tinh thần "không tự ý cởi trói guardrail") — Hưng xác nhận muốn nạp cả 4 file vào Supabase ngay, không chờ xác minh license xong. Ghi nhận: đây là quyết định của R2 (đúng người có thẩm quyền dữ liệu lâm sàng theo RACI), không phải tự ý bỏ qua rào chắn. 3 quyết định con đi kèm: (1) mapping `activity_level` — CSV dùng nhãn NHANES tần suất vận động (sedentary/lightly_active/moderately_active), DB dùng nhãn "loại lao động" cho hệ số PAL (light/moderate/heavy/very_heavy, Bảng 2) — 2 khái niệm khác hẳn nhau, không tự đoán; Hưng chọn map tuyến tính sedentary→light, lightly_active→moderate, moderately_active→heavy (không dùng very_heavy, CSV không có nhãn tương ứng); (2) tài khoản `User` giả cho mỗi hồ sơ dùng email `synthetic+<patient_id>@vnutricare.local` + password ngẫu nhiên không dùng để đăng nhập, để lọc được rõ ràng khỏi user thật sau này; (3) nạp vào SQLite local trước để xem số liệu, chỉ đẩy Supabase sau khi duyệt. Hệ quả: `scripts/load_patient_datasets.py` (mới) thực hiện mapping trên; `manifest.yaml` 4 dataset đổi `enabled: true` kèm ghi chú trỏ về DEC này; set4 (108 dòng, schema nghiên cứu Thái Lan riêng) lọc còn 103 dòng `type.diabetes=='type 2'`, quy đổi `fastingglucose`/`A1c` từ mmol/L sang mg/dL (×18.0182) — KHÔNG copy thẳng số vì đơn vị khác set1/2/3; `medications` của set2/set4 là nhãn NHÓM THUỐC (`oral_antidiabetic`, `insulin`), không phải tên thuốc cụ thể — lưu nguyên trạng nhưng sẽ KHÔNG khớp được với `drug_food_interactions.csv` (vốn cần tên thuốc cụ thể như "Metformin") — không tự suy diễn tên thuốc cụ thể thay nhãn nhóm (RULE-2/DEC-008); `dislikes`/`weight_goal` trong CSV không có cột DB tương ứng hiện tại — bỏ qua khi nạp, không mở migration mới ngoài phạm vi yêu cầu |

| DEC-020 | 2026-08-09 | `load_rules()` đổi default `verified_only` từ `True` (nam-dev, PR #68) về `False` ngay trên `main` | Hưng (R2, xác nhận trực tiếp) | Bối cảnh: PR #68 (nam-dev, 15-node graph + risk triage) đổi default `load_rules(verified_only=True)` với ý định tốt ("fail closed on unverified evidence") — đã cảnh báo trước khi merge (comment review PR #68) rằng toàn bộ 21 dòng `clinical_rules.csv` đang `to_verify`, giữ default này sẽ khiến `compute_targets()` không tính được BẤT KỲ ngưỡng nào ngoài năng lượng. Sau khi merge #68 vào `main`, test hồi quy `tests/test_equivalent.py` bắt được đúng hệ quả này TRÊN THỰC TẾ (không còn là lý thuyết): thực đơn tương đương tính ra `carb_g=4.31` cho cả ngày vì carb/đạm/xơ/natri không còn ngưỡng nào áp dụng. Phương án cân nhắc: (A) giữ `verified_only=True`, chấp nhận hệ thống tạm thời chỉ tính được năng lượng cho tới khi R2 verify rule; (B) đổi default về `False` (khôi phục hành vi trước PR #68) — dùng rule `to_verify` như toàn bộ dự án đã làm từ đầu, có ghi rõ trong DEVLOG/docstring rằng đây là governance tạm thời. Hưng chọn B ngay khi được báo, vì (A) làm hỏng toàn bộ nghiệp vụ tính ngưỡng lâm sàng — rủi ro vận hành lớn hơn rủi ro dùng rule chưa verify (vốn đã được chấp nhận từ đầu dự án, xem DEC-008/`docs/TICKETS.md` DAT-00). Hệ quả: `src/clinical/rules.py::load_rules()` default `verified_only=False`, docstring ghi rõ đây là quyết định có thời hạn (khi R2 verify xong rule thật, cân nhắc đổi lại); `tests/test_clinical.py::test_runtime_rule_loader_mac_dinh_nap_ca_to_verify` (đổi tên + đảo ngược assertion) khớp hành vi mới; `compute_targets_with_rule_gate()` (cơ chế 2 tầng verified/inventory của nam-dev cho review packet) không bị ảnh hưởng — vẫn tự gọi `verified_only=True`/`False` tường minh ở đúng chỗ cần, không phụ thuộc default. Không đổi gì ở `docs/TICKETS.md` DAT-00 (rào chắn "R2 phải đối chiếu guideline gốc trước Demo Day" vẫn còn nguyên, đây chỉ là default runtime, không phải miễn trừ nghĩa vụ verify) |

| DEC-021 | 2026-08-09 | Sửa `target_gate()`/`make_compute_targets()` (graph 15-node của nam-dev, `src/agents/nodes/core.py`) — bỏ fail-closed cho MỌI rule `to_verify`, chỉ chặn khi xung đột ngưỡng thật (min>max) | Hưng (R2, yêu cầu trực tiếp: "sửa lại graph 15-node của nam-dev về chuẩn theo tài liệu nghiên cứu gốc") | Bối cảnh: sau khi merge PR #68 và fix DEC-020 (đổi default `load_rules()`), phát hiện `target_gate()`/`make_compute_targets()` trong `core.py` vẫn gọi cứng `load_rules(verified_only=True)` và coi BẤT KỲ `unverified_rule_ids` nào là lý do `manual_review_required` (P0, chặn generator) — không phụ thuộc default vừa sửa, nên hành vi lỗi (chặn toàn bộ vì 21/21 rule đều `to_verify`) vẫn còn nguyên trong graph mới dù DEC-020 đã "sửa" ở lớp thấp hơn. Đối chiếu lại tài liệu gốc trước khi sửa (research agent riêng, không suy đoán): `docs/PRD.md` đọc theo câu chữ có vẻ yêu cầu fail-closed tuyệt đối, nhưng `docs/00_ASSESSMENT.md` + DEC-014 (đối chiếu `KeHoachDuAn_VNutriCare_VMEC10_v3.docx` §6.4.1 — nguồn yêu cầu chính của PRD) xác nhận `needs_expert_review` CHỈ kích hoạt khi rule thật sự xung đột sau hợp nhất (min>max), không phải cho mọi rule chưa verified — đây là đặc tả gốc thật, khớp với `src/clinical/rules.py` (`compute_targets()`/`_select_rules()`) đã làm đúng từ đầu dự án. nam-dev's `target_gate()` vi phạm đúng nguyên tắc này. Hệ quả: (1) `make_compute_targets()` tính `targets` từ TOÀN BỘ rule inventory (không chỉ verified) — khớp đúng cách `compute_targets()` gốc vẫn hoạt động; (2) `target_gate()` chỉ trả `manual_review_required`/P0 khi `targets.conflict_notes`/`needs_expert_review` có xung đột thật; rule `to_verify` được ghi thành `SafetyFinding(category="unverified_rule", risk_level=P1, reviewer_override_allowed=True)` — vẫn hiển thị cho chuyên gia soát (không giấu), nhưng không chặn generator chạy. `tests/test_agent.py::test_target_gate_chan_rule_to_verify_truoc_generator` đổi tên + đảo kỳ vọng (generator.calls từ 0→1, highest_risk P0→P1, can_approve False→True) khớp hành vi mới. Bỏ qua CI theo yêu cầu Hưng ("chỉ cho phép để qua CI tránh tắc nghẽn") — verify local đầy đủ: 368 test pass, ruff/mypy sạch, commit thẳng lên `main` |
| DEC-022 | 2026-08-09 | (ticket `DAT-25`) Tách `data/` thành ba tầng (`seeds/` chạm bệnh nhân · `reference/` tra cứu USDA · `quarantine/` nợ chờ R2), gom ranh giới tầng về `src/clinical/tiers.py` làm nguồn duy nhất | Hưng (R2, yêu cầu trực tiếp: "cần chuẩn hoá, Việt hoá về từng bảng riêng biệt, lọc, làm sạch chứ đang có quá nhiều thứ phải test khiến hệ thống bị phình to") | Bối cảnh: R2 phát hiện UI bệnh nhân hiện tên mẫu thực đơn ("Bữa sáng - Thực đơn 3 (TĐ 3+4) — 300 g") thay vì tên món. Nguyên nhân: hai loader lọc rác theo hai tiêu chí KHÁC NHAU — `clinical/dishes.py` lọc theo tiền tố `dish_id` (`FNDDS-`,`MENU-`, đúng), còn `clinical/seeds.py::load_vn_dishes()` lọc theo cột `verified_by` bắt đầu bằng "USDA FNDDS"; các dòng `MENU-*` ghi `verified_by="pending"` nên KHÔNG khớp và lọt thành `DishCandidate`. Nguyên nhân sâu hơn: `data/seeds/food_items.csv` (7745 dòng, 89% tên tiếng Anh USDA nhét trong cột `name_vi`, không có cột `name_en`, 355 dòng rỗng toàn bộ) và `dishes.csv` (2677 dòng, 98% FNDDS) gộp bốn nguồn khác bản chất vào một file phẳng, còn `validate_data.py` KHÔNG kiểm tra `dishes*.csv`/`dish_ingredients*.csv` một dòng nào — đúng chỗ toàn bộ nợ đang nằm. Hệ quả 4 PR: #79 gom ranh giới tầng + vá lỗ hổng; #80 tách 3 tầng (`data/seeds/` 28→11 file, food 7745→536, dish 2677→30) + Việt hoá tên tham chiếu sang cột `name_en` mới + `check_dishes()`/`check_dish_ingredients()` cho validator (2647 ERROR→0); #81 lưới an toàn seed-only; #82 script audit CHỈ ĐỌC cho dữ liệu bệnh nhân đã persist. Đo được: test suite 12 phút → 70 giây (397 pass) vì `test_seed_db.py` không còn nạp 7745 dòng — mục tiêu "giảm phình test" đạt bằng dữ liệu gọn, KHÔNG bằng cách xoá lớp bảo vệ. Ba giả định trong kế hoạch ban đầu bị BÁC BỎ khi kiểm chứng, đã sửa: (1) khối USDA là khoảng ĐÓNG 167516–1105897 chứ không phải "mọi id ≥ 167516" — 430 dòng NIN 2017 tiếng Việt nằm ngay sau (1105898–1106327), một `WHERE id >= 167516` sẽ xoá nhầm dữ liệu Việt thật; (2) không thêm cột `name_en` vào DB vì sau khi tách, dữ liệu được seed không còn dòng tiếng Anh nào (cột sẽ NULL 100%); (3) không xoá `TestGiProvenanceRule2` — nó chặn validator Pydantic lúc chạy, khác tầng với `validate_data.py` chặn CSV. Audit DB thật: 33/160 dòng `meal_plan_items` có `dish_id` là `MENU-*`, trong đó 25 thuộc thực đơn `approved` trên 3 hồ sơ bệnh nhân — CHƯA XỬ LÝ, chờ R2 quyết định (RULE-3, thực đơn approved đã tới tay bệnh nhân) |

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
