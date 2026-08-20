# Phân công toàn lộ trình và checkpoint — VNutriCare

Ngày tạo: 2026-08-17 · Cập nhật: 2026-08-17 (Bạn = R3+R4 gộp backend/frontend/DevOps; R3 mới = Data Engineer, một trong bốn người phát triển sản phẩm) · T0 = Thứ 2 17/08/2026

Bộ ba tài liệu:

| Tài liệu | Trả lời câu hỏi |
|---|---|
| [`PRODUCTION_READINESS_MASTER_PLAN.md`](./PRODUCTION_READINESS_MASTER_PLAN.md) | **Làm gì và vì sao** — bảy chặng, sáu quyết định kiến trúc, tiêu chí sẵn sàng |
| [`PATIENT_EXPERIENCE_MASTER_PLAN.md`](./PATIENT_EXPERIENCE_MASTER_PLAN.md) | **Tính năng trông ra sao** — đặc tả F1–F8, sơ đồ, ràng buộc an toàn |
| **Tài liệu này** | **Ai làm, khi nào, và làm sao biết đã xong** |

---

## 0. Cách dùng tài liệu này

Toàn bộ hành trình là **10 checkpoint**, không phải 10 tuần cố định. Checkpoint là *cổng chất lượng*, không phải *mốc thời gian*. Ước tính thời gian lấy từ `PRODUCTION_READINESS_MASTER_PLAN.md` mục 6 (8–10 tuần, cộng tối thiểu 2 tuần shadow mode).

Ba nguyên tắc chi phối mọi phân công dưới đây:

1. **Một tệp có đúng một chủ.**
2. **Không ai phải ngồi chờ ai.**
3. **Chưa xong thì ghi là chưa xong.**

### Mô hình vai trò của bản này — lần đổi thứ ba

Bạn giữ chỗ **R4** trong `TEAM.md`, nhưng nhận thêm toàn bộ việc của **R3 cũ** — nghĩa là bạn viết mọi thứ ở tầng ứng dụng: backend, cả hai giao diện, schema, DevOps, deploy, deliverables.

**R3** không còn là backend/DevOps, và cũng **không phải vai trò kiểm tra hay QA riêng**. R3 là người phát triển sản phẩm thứ tư, cùng xây dựng như R1 và R2 — chỉ khác **tầng**: R1 xây tầng agent, R2 xây/duyệt tầng nội dung lâm sàng, **R3 xây tầng dữ liệu**.

| Vai trò | Trước đây | Bây giờ |
|---|---|---|
| **Bạn (R4)** | Frontend + Deliverables | **Người viết chính tầng ứng dụng** — API, cả hai giao diện, schema/migration, DevOps/CI/deploy, deliverables |
| **R1** | Agent Engineer + PM | Không đổi — tầng agent |
| **R2** | Clinical & Data Engineer + Eval | Không đổi — tầng nội dung lâm sàng, người duyệt cuối cho mọi con số |
| **R3** | ~~Backend Engineer + DevOps~~ | **Data Engineer** — tầng dữ liệu: đối chiếu/hợp nhất nguồn dữ liệu, cơ chế versioning cho release, pipeline RAG còn đang là schema trống, chất lượng dữ liệu vận hành, phân tích dữ liệu thật cho shadow mode |

**Vì sao tách được rõ ràng, không giẫm chân R2:** R2 là **thẩm quyền nội dung** — quyết định một rule đúng hay sai, một món có dùng được cho bệnh nhân hay không, ký release. R3 là **người xây hạ tầng chứa nội dung đó** — cách dữ liệu được nạp vào, đối chiếu, versioning, truy hồi. R2 vẫn là người duyệt cuối cùng cho bất kỳ dòng dữ liệu nào R3 đưa vào hệ thống — ranh giới này giữ nguyên `CODEOWNERS` hiện có (`/data/seeds/ → R2`), R3 làm việc trên **pipeline và script**, không tự ý sửa nội dung.

**Xác nhận checkpoint không còn là việc riêng của một người.** Mỗi checkpoint do đúng người có thẩm quyền trên phần đó xác nhận: bạn tự xác nhận phần ứng dụng chạy được (build, test, deploy), R1 xác nhận phần agent, R2 xác nhận phần nội dung lâm sàng, R3 xác nhận phần dữ liệu đúng và nhất quán. Không có một "người kiểm" đứng ngoài toàn bộ hệ thống.

### Mô tả chi tiết từng vai trò

Theo đúng khuôn của `TEAM.md` §2 (Chính / Kiêm / Quyền đặc biệt / Không làm / Cột mốc), cập nhật cho mô hình bốn người này.

#### Bạn (giữ chỗ R4) — Full-stack Engineer + DevOps + Deliverables

- **Chính:** viết toàn bộ tầng ứng dụng — mọi route trong `src/api/**`, mọi màn hình trong `web-next/src/app/**` (cả không gian bệnh nhân lẫn chuyên gia), mọi thay đổi schema (`src/db/models.py`, tự viết và tự chạy `alembic revision`/`upgrade`).
- **Kiêm DevOps:** Dockerfile, `docker-compose.yml`, GitHub Actions, deploy Render + Vercel, secrets, staging, theo dõi chi phí hạ tầng.
- **Kiêm Deliverables:** README, chụp màn hình liên tục, video demo, pitch deck — không dồn cuối kỳ.
- **Quyền đặc biệt:** người duy nhất chạy migration — không ai khác được `alembic revision` để giữ đúng một đầu Alembic (lý do Chặng 1 phải tốn công dọn dẹp).
- **Không làm:** không tự ý sửa nội dung `data/seeds/**` (rule, món, ngưỡng) — mọi thay đổi nội dung phải qua R2 duyệt, kể cả khi R3 đề xuất qua pipeline; không tự quyết ngưỡng lâm sàng.
- **Cột mốc:** CP1 (nền móng dựng lại được) tự xác nhận bằng ba lệnh Alembic chạy sạch trên máy trắng · CP4 (F1 chạy đầu-cuối trên API thật) · CP6 (bốn tính năng phía bệnh nhân chạy ổn định).

#### R1 — Agent Engineer + PM

- **Chính:** `src/agents/**` — graph, node, guardrail, prompt, CP-SAT, tích hợp pipeline truy hồi của R3 vào node trợ lý.
- **Kiêm PM:** theo dõi tiến độ 10 checkpoint trong tài liệu này, chủ trì standup, canh thứ tự merge, chốt tranh luận kỹ thuật.
- **Quyền đặc biệt:** người duy nhất xác nhận `highest_risk` khớp `risk_triage` — không ai khác đủ ngữ cảnh để nói badge P0/P1/P2 có nói đúng sự thật hay không.
- **Không làm:** không viết business logic tầng API hay giao diện (của bạn); không tự đặt ngưỡng lâm sàng (của R2); không tự nạp dữ liệu vào `guideline_chunks` (của R3) — chỉ tiêu thụ kết quả truy hồi.
- **Cột mốc:** CP1 xác nhận `highest_risk` đúng thật · CP5 xác nhận vá vùng miền hoạt động đúng bằng dữ liệu thật · CP6 tự hỏi trợ lý một câu vượt ranh giới để xác nhận leo thang, và xác nhận trợ lý trích dẫn được nguồn thật từ pipeline RAG.

#### R2 — Clinical & Data Content Engineer + Eval

- **Chính:** `src/clinical/**`, nội dung `data/seeds/**` (rule, món, ngưỡng, tương tác thuốc), bộ eval, liên hệ chuyên gia thật.
- **Kiêm Eval:** đánh giá lâm sàng trong shadow mode — hệ thống có bỏ sót ca nguy hiểm, có cảnh báo thừa không, dựa trên số liệu R3 chuẩn bị.
- **Quyền đặc biệt:** **người duy nhất ký** rule release và data release — không có chữ ký của R2, không dòng dữ liệu nào được chạm tới bệnh nhân, kể cả khi R3 đã đối chiếu xong về mặt kỹ thuật. Cũng là người duyệt danh sách nguồn hướng dẫn lâm sàng trước khi R3 ingest vào `guideline_chunks`.
- **Không làm:** không viết pipeline/script (của R3); không viết code ứng dụng (của bạn).
- **Cột mốc:** CP2 ký hai release · CP3 xác nhận ba phương án CP-SAT hợp lý lâm sàng · CP6 xác nhận nội dung trích dẫn RAG không sai lệch · CP9 kết luận lâm sàng dựa trên số liệu shadow mode.

#### R3 — Data Engineer

- **Chính:** đối chiếu và hợp nhất nguồn dữ liệu (Supabase cũ với release mới), thiết kế cơ chế versioning cho release, xây pipeline `src/rag/` (ingest + truy hồi cho `guideline_chunks` — hiện là schema trống, chưa có dòng code nào), theo dõi chất lượng dữ liệu vận hành (food log map được/chưa map được, tỉ lệ ước tính).
- **Kiêm phân tích cho shadow mode:** tổng hợp dữ liệu thật thành số liệu để R1/R2 ra kết luận ở CP9 — không tự kết luận lâm sàng thay R2.
- **Quyền đặc biệt:** người duy nhất quyết định *cơ chế kỹ thuật* để phân biệt dữ liệu "release đang hoạt động" với dữ liệu legacy/quarantine — nhưng quyết định *nội dung nào được ký vào release* vẫn luôn là R2.
- **Không làm:** không tự sửa nội dung `data/seeds/**` — chỉ viết script/pipeline nạp và đối chiếu, mọi thay đổi nội dung qua R2 duyệt trước khi chạy trên production; không viết `alembic revision` — báo bạn cột/bảng cần thêm; không viết business logic API hay giao diện.
- **Cột mốc:** CP2 đối chiếu xong 7.403 thực phẩm/2.747 món với release đã ký, có số liệu cụ thể chứng minh dữ liệu chưa duyệt không lọt vào luồng bệnh nhân · CP4/CP6 pipeline RAG ingest xong danh sách nguồn đã duyệt và truy hồi đúng ngữ cảnh · CP9 có bảng số liệu đầy đủ cho sáu câu hỏi shadow mode.

---

## 1. Toàn cảnh 10 checkpoint

```text
CHẶNG 1  ~1 tuần        CP1  · Nền móng dựng lại được
CHẶNG 2  1–2 tuần       CP2  · Rule và dữ liệu đã được R2 ký, R3 đối chiếu xong
CHẶNG 3  1–2 tuần       CP3  · Sinh được nhiều phương án hợp lệ
                        CP4  · Duyệt gắn phiên bản + F1 chạy thật
CHẶNG 4  ~2 tuần        CP5  · Tái sử dụng thực đơn (F2, hai tầng) chạy được
                        CP6  · Nhật ký, trợ lý có leo thang và trích dẫn thật, chỉ số (F3–F5)
CHẶNG 5  1–2 tuần       CP7  · Tổ chức B2B + worker bền vững
CHẶNG 6  tối thiểu 2 tuần CP8 · Shadow mode bắt đầu chạy
                        CP9  · Shadow mode đủ bằng chứng
CHẶNG 7  mở dần         CP10 · Go/No-Go production
```

Ba checkpoint có quyền **bắt cả đội dừng lại**: CP1, CP2, CP9.

---

## 2. Bản đồ sở hữu tệp — áp dụng suốt lộ trình

| Vùng tệp | Chủ | Ghi chú |
|---|---|---|
| `src/agents/**` | **R1** | Graph, node, guardrail, prompt, CP-SAT |
| `src/clinical/**`, `eval/**` | **R2** | Nội dung và ngưỡng lâm sàng |
| `data/seeds/**` | **R2 duyệt nội dung, R3 vận hành pipeline** | R3 viết script nạp/đối chiếu, R2 là người duyệt trước khi bất kỳ dòng nào được dùng cho bệnh nhân — CODEOWNERS giữ nguyên |
| `src/rag/**` (mới) | **R3** | Ingestion và truy hồi cho `guideline_chunks` — hiện là schema trống, chưa có pipeline |
| `scripts/` liên quan dữ liệu (đối chiếu, versioning release, kiểm tra chất lượng) | **R3** | |
| `src/api/**`, `src/models/schemas.py` | **Bạn** | Toàn bộ business logic tầng API |
| `src/db/models.py`, `alembic/versions/**` | **Bạn** | Bạn viết và chạy migration |
| `.github/**`, `Dockerfile`, `docker-compose.yml`, CI | **Bạn** | |
| `web-next/src/**` (cả hai không gian, components, lib) | **Bạn** | |
| `render.yaml`, cấu hình deploy, staging | **Bạn** | |
| `presentation/**`, README, video, pitch deck | **Bạn** | |
| `docs/**` | **R1** | Trừ tài liệu này, do bạn giữ |
| `DEVLOG.md` | Tất cả | Chỉ nối thêm vào **cuối tệp** |

### Một quy tắc còn lại

**Migration liên quan dữ liệu (bảng release, versioning):** R3 xác định cần cột/bảng gì để phục vụ pipeline dữ liệu, báo bạn **trước 12:00 ngày đầu mỗi chặng**, bạn viết và chạy migration như mọi migration khác. R3 không tự chạy Alembic — vẫn giữ đúng một đầu, một người chạy.

---

## 3. Quy tắc git và nhịp làm việc

**Nhánh:** `feature/<mã việc>-mô-tả-ngắn`.

**PR dưới 400 dòng**, có mô tả và cách test.

**Trước khi merge:** người sở hữu vùng tệp đó tự chạy `make check`/test liên quan xanh. PR chạm `data/seeds/**` hoặc nội dung do R3 nạp vào bắt buộc **R2 duyệt nội dung** trước khi merge — không đổi so với CODEOWNERS gốc.

**Không push thẳng `main`. Không force push. Không `--no-verify`.**

**Nhịp:** standup async 21:00 hằng ngày, demo nội bộ cuối mỗi chặng, ghi DEVLOG cuối mỗi buổi. Vướng quá 90 phút phải kêu.

---

## 4. Phân công theo chặng

### Chặng 1 → CP1 · Nền móng dựng lại được

Ước tính một tuần. T0 = Thứ 2 17/08. Chặng này chủ yếu là ứng dụng — R3 khảo sát để chuẩn bị cho Chặng 2.

| Mã | Việc | Người | Tệp |
|---|---|:-:|---|
| `C1-SET-01` | **Xác minh Alembic.** Local hiện báo một đầu duy nhất `c41a7d92e610`, và merge `1778fd77cbec` đã nối `c95f302a587e`. Dựng Postgres trắng, `upgrade head`, `downgrade base`, so schema với `models.py` | Bạn | `alembic/**` |
| `C1-SET-02` | Backup production, viết quy trình khôi phục, tự thử khôi phục trên database tạm | Bạn | hạ tầng |
| `C1-BE-01` | **Khoá lỗ hổng đăng ký:** `/auth/register` công khai chỉ tạo được role `patient`; `dietitian` chuyển sang cơ chế mời | Bạn | `src/api/routes/auth.py` |
| `C1-FE-01` | **Sửa nút nổi bị cắt nửa ngoài mép phải.** Đã xác minh trên mọi trang ở cả 1280px và 1440px | Bạn | `components/experience-tools*` |
| `C1-FE-02` | **Badge P0/P1/P2 trên từng dòng hàng chờ.** `MealPlanOut` đã trả sẵn `highest_risk` | Bạn | `app/dietitian/reviews/**` |
| `C1-FE-03` | Lọc và sắp xếp danh sách hồ sơ — hiện 2021 hồ sơ, 102 trang | Bạn | `app/dietitian/patients/**` |
| `C1-AGT-01` | **Kiểm chứng `highest_risk` khớp `risk_triage`** trên dữ liệu thật | R1 | `src/agents/**`, `tests/` |
| `C1-CLN-01` | **Sửa bug dữ liệu ngày `2031-03-03`** — lệch 5 năm, hiện trên cả dashboard lẫn hàng chờ | R2 | `scripts/seed_*.py` |
| `C1-DAT-01` | **Khảo sát nguồn dữ liệu:** liệt kê chính xác chênh lệch giữa Supabase (7.403 thực phẩm, 2.747 món) và seed hiện tại (547 thực phẩm, 100 món) — bảng nào là FNDDS chưa duyệt, bảng nào đang được thực đơn cũ tham chiếu. Đầu ra là báo cáo, chưa sửa gì | R3 | `scripts/`, `docs/` |

**CP1 — bằng chứng phải có:**

```bash
alembic heads             # in ra ĐÚNG 1 dòng
alembic upgrade head      # trên database trắng, chạy hết không lỗi
alembic downgrade base    # quay về được
```

- Đăng ký công khai với `"role":"dietitian"` bị từ chối, có test chứng minh
- Backup production đã khôi phục thử thành công trên database tạm
- Ảnh chụp nút nổi không còn bị cắt ở 1280px và 1440px
- Badge P0/P1/P2 hiện trên hàng chờ và R1 đã xác nhận khớp `risk_triage`
- Báo cáo khảo sát chênh lệch dữ liệu của R3 sẵn sàng làm đầu vào cho Chặng 2

> **Không qua CP1 thì dừng toàn bộ việc chạm schema**, cả đội dồn vào gỡ `C1-SET-01`.

---

### Chặng 2 → CP2 · Rule và dữ liệu đã được R2 ký, R3 đối chiếu xong

Ước tính một đến hai tuần. **Đây là chặng chính của R3** — song song với R2, không phụ thuộc nhau tới cuối chặng.

| Mã | Việc | Người | Tệp |
|---|---|:-:|---|
| `C2-CLN-01` | Verify từng clinical rule, **rủi ro cao nhất trước**: natri, kali, protein cho CKD, tương tác thuốc mức `high` | R2 | `data/seeds/clinical_rules.csv` |
| `C2-CLN-02` | **Data release món Việt đầu tiên** — mục tiêu 24 món thật sạch, đủ vai trò tinh bột, đạm, rau, canh, bữa phụ | R2 | `data/seeds/**` |
| `C2-CLN-03` | Ký rule release và data release. **Không có chữ ký của R2 thì không rule nào được chạm bệnh nhân** | R2 | `docs/` |
| `C2-DAT-01` | **Thiết kế cơ chế versioning cho release** — thế nào là "release đang hoạt động", dòng legacy đánh dấu ra sao mà không xoá, ai được đổi trạng thái. Báo bạn cột/bảng cần thêm | R3 | `docs/`, `scripts/` |
| `C2-BE-01` | Thêm cột/bảng theo thiết kế của R3; API/agent đọc đúng release đang hoạt động, không còn nơi đọc CSV nơi đọc database | Bạn | `src/db/`, `src/api/`, `alembic/` |
| `C2-DAT-02` | **Đối chiếu thật** 7.403 thực phẩm và 2.747 món trên Supabase với release R2 vừa ký — phân loại dòng nào giữ (đang được lịch sử tham chiếu), dòng nào đánh dấu ngừng dùng cho generation, dòng nào bỏ hẳn. Trình R2 duyệt trước khi chạy trên production | R3 | `scripts/` |
| `C2-AGT-01` | Shadow mode cho rule chưa verify: rule chạy và ghi log nhưng **không tác động** kết quả | R1 | `src/agents/**` |
| `C2-FE-01` | Nhãn phân biệt rule đã xác minh và rule đang shadow trên màn hình duyệt | Bạn | `app/dietitian/**` |

**CP2 — bằng chứng:** R2 đã ký hai release · generator chỉ đọc dữ liệu thuộc release đang hoạt động · R3 chứng minh bằng số liệu cụ thể là dữ liệu chưa duyệt **không** lọt được vào luồng bệnh nhân · rule chưa chắc chắn đã bị vô hiệu hoá chứ không để `to_verify` mà vẫn chạy.

---

### Chặng 3 → CP3 và CP4 · Sinh thực đơn Việt Nam và duyệt có phiên bản

Ước tính một đến hai tuần. Ít việc dữ liệu mới; R3 dùng thời gian này chuẩn bị nền cho pipeline RAG sẽ xây ở Chặng 4.

| Mã | Việc | Người | Tệp |
|---|---|:-:|---|
| `C3-AGT-01` | CP-SAT sinh **tối đa ba phương án hợp lệ**; LLM chỉ được xếp hạng hoặc diễn đạt các phương án đã qua kiểm tra | R1 | `src/agents/**` |
| `C3-AGT-02` | Vai trò món: tinh bột, đạm, rau, canh, bữa phụ. Bữa sáng cấu trúc nhanh gọn; trưa và tối dùng mâm cơm | R1 | `src/agents/**` |
| `C3-BE-01` | Schema `plan_approvals` — lưu artifact đã duyệt, gắn hash, không sửa lại. Thêm cột `plan_id` vào `clinical_notes` cho F1 | Bạn | `src/db/`, `alembic/` |
| `C3-BE-02` | API trả nhiều phương án; mỗi lần sinh lại hoặc chỉnh món tạo **phiên bản mới**, gắn hash — món/gram đổi thì hash đổi và duyệt cũ hết hiệu lực | Bạn | `src/api/routes/meal_plans.py` |
| `C3-BE-03` | **F1 — API yêu cầu bổ sung thông tin.** Trạng thái `awaiting_patient_input`, ghi vào `clinical_notes` | Bạn | `src/api/routes/reviews.py` |
| `C3-FE-01` | Giao diện so sánh ba phương án cạnh nhau | Bạn | `app/dietitian/**` |
| `C3-FE-02` | Dinh dưỡng hiển thị ba tầng: theo món, theo bữa, theo ngày | Bạn | `app/dietitian/**` |
| `C3-FE-03` | **What-if trước khi đổi món** — backend đã có `targets/{id}/what-if` | Bạn | `app/dietitian/**` |
| `C3-FE-04` | **F1 — giao diện chuyên gia:** nút thứ ba cạnh Duyệt và Từ chối, form soạn câu hỏi | Bạn | `app/dietitian/reviews/**` |
| `C3-FS-01` | **F1 — phía bệnh nhân:** banner thông báo và form trả lời | Bạn | `app/patient/**` |
| `C3-FS-02` | Xử lý `409` khi đã có plan cùng ngày | Bạn | `app/patient/**` |
| `C3-CLN-01` | Kiểm tra ba phương án sinh ra có hợp lý lâm sàng không, không chỉ hợp lệ về số | R2 | `eval/` |
| `C3-DAT-01` | **Khảo sát nguồn hướng dẫn lâm sàng** để chuẩn bị ingest vào `guideline_chunks` — ADA, KDIGO... bản nào có sẵn, định dạng gì, cấp phép dùng lại thế nào. Đầu ra là danh sách nguồn đã duyệt được với R2 | R3 | `docs/` |

**CP3 (giữa chặng):** CP-SAT ra được ba phương án hợp lệ cho một hồ sơ thật · backend tính lại dinh dưỡng đủ cả ba · R2 xác nhận ba phương án đều dùng được trên lâm sàng.

**CP4 (cuối chặng):**

```bash
curl -X POST localhost:8000/api/v1/reviews/<plan_id>/request-info \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"question":"Xác nhận còn dị ứng hải sản không?"}'
# → status đổi sang awaiting_patient_input
```

Kịch bản đầu-cuối: chuyên gia mở hàng chờ → thấy mức P0/P1/P2 → bấm "Cần bổ sung thông tin" → bệnh nhân thấy thông báo, trả lời → hồ sơ quay lại đầu hàng chờ với nhãn đã phản hồi → duyệt được. Sửa gram sau khi duyệt thì hash đổi và quyết định duyệt cũ mất hiệu lực.

---

### Chặng 4 → CP5 và CP6 · Tái sử dụng hai tầng, nhật ký, trợ lý có trích dẫn thật

Ước tính hai tuần. Chặng nặng nhất cho cả bạn lẫn R3 — đây là nơi pipeline RAG được xây, đúng lúc trợ lý (F3a) cần trích dẫn nguồn thật thay vì chỉ diễn giải suông.

| Mã | Việc | Người | Tệp |
|---|---|:-:|---|
| `C4-BE-01` | Schema `plan_assignments` — ngày cụ thể nào dùng thực đơn nào (bản gốc hay bản biến thể vừa auto-release) | Bạn | `src/db/`, `alembic/` |
| `C4-BE-02` | **F2 tầng 1 — logic dùng `plan_assignments`.** Reuse chỉ tiếp tục đúng artifact đã duyệt, không tự duyệt bản mới | Bạn | `src/api/` |
| `C4-BE-03` | Điều kiện dừng tái sử dụng khi thuốc, dị ứng, bệnh lý, mục tiêu hoặc rule thay đổi | Bạn | `src/api/` |
| `C4-BE-04` | **F2 tầng 2 — popup 3 preset lúc duyệt.** API nhận preset (Ổn định/Linh hoạt/Linh hoạt cao), map sang `tolerance`/`max_auto_releases`/`expires_in_days`, gọi `POST /substitution-scopes` **đã có sẵn**. Đặt ngay sau bước duyệt, không đặt lúc bấm sinh | Bạn | `src/api/`, `app/dietitian/reviews/**` |
| `C4-BE-05` | **Job hằng đêm cho F2 tầng 2.** Gọi `POST /meal-plans/{id}/equivalent` mỗi đêm cho hồ sơ có scope còn hiệu lực — bộ giải **đã có sẵn**, chỉ thiếu cái gọi nó | Bạn | `src/api/`, worker |
| `C4-AGT-04` | **Vá lỗ hổng vùng miền.** `optimizer.py` và `equivalent.py` chưa lọc `region` khi chọn ứng viên — chỉ lọc dị ứng/sở thích | R1 | `src/agents/optimizer.py`, `src/agents/equivalent.py` |
| `C4-DAT-01` | **Xây pipeline ingest cho `guideline_chunks`** — bảng đã có, hoàn toàn chưa có `ingest.py`/`chunker.py`. Nạp các nguồn R3 đã khảo sát ở Chặng 3, chia đoạn, sinh embedding, lưu vào pgvector | R3 | `src/rag/` (mới) |
| `C4-DAT-02` | **Truy hồi cho trợ lý (F3a):** hàm tìm đoạn hướng dẫn liên quan tới câu hỏi bệnh nhân, trả về kèm `source`/trang — nối vào node trợ lý của R1, không tự trả lời thay | R3 | `src/rag/` (mới) |
| `C4-DAT-03` | Kiểm tra chất lượng dữ liệu food log: tỉ lệ món map được / chưa map được / khẩu phần chưa quy đổi, báo cáo hằng tuần | R3 | `scripts/` |
| `C4-BE-06` | Dựng object storage cho ảnh nhật ký, gắn `food_log_id` | Bạn | `src/api/`, hạ tầng |
| `C4-BE-07` | **F4 — mở quyền:** `POST /patients/{id}/observations` đang khoá `require_role("dietitian","admin")`, nới để bệnh nhân tự ghi được, giữ `_get_owned_profile` | Bạn | `src/api/routes/patient_workspace.py` |
| `C4-AGT-01` | **F3a — trợ lý trả lời** câu hỏi an toàn, diễn giải thực đơn đã duyệt **và trích dẫn thật từ `guideline_chunks`** khi R3 xong `C4-DAT-02` | R1 | `src/agents/**` |
| `C4-AGT-02` | **F3b — leo thang.** Guardrail phát hiện vượt ranh giới thì tạo luồng `clinical_notes`, đẩy cho đúng chuyên gia | R1 | `src/agents/**` |
| `C4-AGT-03` | Worker tính báo cáo tuần; LLM nếu dùng thì chỉ chuyển số đã tính thành lời | R1 | `src/agents/**` |
| `C4-CLN-01` | Định nghĩa care status: `insufficient_data`, `stable`, `watch`, `review_required`, `red_flag` | R2 | `src/clinical/**` |
| `C4-FE-01` | Dashboard care status — **hai hệ badge tách bạch** với P0/P1/P2 | Bạn | `app/dietitian/**` |
| `C4-FE-02` | Mục "Câu hỏi cần vấn đáp", **tách khỏi** hàng chờ duyệt thực đơn | Bạn | `app/dietitian/**` |
| `C4-FE-03` | Biểu đồ cân nặng và BMI trong hồ sơ bệnh nhân phía chuyên gia | Bạn | `app/dietitian/patients/**` |
| `C4-FS-01` | **F5 — thời khoá biểu bữa ăn:** desktop lưới 4×7, mobile một ngày một cột | Bạn | `app/patient/weekly/**` |
| `C4-FS-02` | **F5 — đính kèm ảnh**, nhãn "chưa được hệ thống xác minh nội dung" | Bạn | `app/patient/**` |
| `C4-FS-03` | **F4 — giao diện bệnh nhân** tự ghi cân nặng và xem biểu đồ | Bạn | `app/patient/**` |
| `C4-FS-04` | Thẻ "Thực đơn đang áp dụng" hiện hạn hiệu lực và badge tự động | Bạn | `app/patient/**` |

**CP5 (giữa chặng):** tái sử dụng tầng 1 chạy được cho một hồ sơ ổn định bảy ngày mà **không phát sinh lượt duyệt mới** · tầng 2 sinh được ít nhất một biến thể hợp lệ qua job hằng đêm, khác món nhưng cùng đúng vùng miền — **R1 xác nhận** vì đây là fix trong `src/agents/**` · đổi một loại thuốc thì hệ thống dừng cả hai tầng.

**CP6 (cuối chặng):**
- **F3a và F3b phát hành cùng lúc.** R1 tự hỏi trợ lý một câu vượt ranh giới, xác nhận nó chuyển cho chuyên gia thay vì tự trả lời
- **Trợ lý trích dẫn được nguồn thật** từ `guideline_chunks`, không chỉ diễn giải suông — **R3 xác nhận** pipeline RAG trả đúng đoạn liên quan, **R2 xác nhận** nội dung trích dẫn không sai lệch
- Thời khoá biểu hiện đúng lưới 4×7 trên desktop, một ngày một cột trên điện thoại
- Bệnh nhân tự ghi được cân nặng; biểu đồ **không nội suy** ngày trống
- Báo cáo tuần trả `insufficient_data` khi dữ liệu ít, **không** trả `stable`
- Popup 3 preset xuất hiện sau khi duyệt, không xuất hiện lúc sinh

> **F6 (chuỗi ngày) và F7 (huy hiệu) chỉ bắt đầu sau CP6**, khi F5 đã chạy ổn định và có dữ liệu thật.

---

### Chặng 5 → CP7 · Tổ chức B2B và độ bền hệ thống

Ước tính một đến hai tuần. Chặng chủ yếu của bạn; R3 tiếp tục vận hành pipeline dữ liệu đã xây.

| Mã | Việc | Người | Tệp |
|---|---|:-:|---|
| `C5-BE-01` | Schema `organizations`, `organization_members`, phân công care team | Bạn | `src/db/`, `alembic/` |
| `C5-BE-02` | Rà lại **toàn bộ** endpoint bảo đảm không truy cập chéo tổ chức | Bạn | `src/api/**` |
| `C5-BE-03` | Chuyển generation và weekly summary sang **worker bền vững** | Bạn | worker, hạ tầng |
| `C5-BE-04` | CI mở rộng: lint, type check, pytest, data validation, Next.js build, Playwright smoke | Bạn | `.github/**` |
| `C5-BE-05` | Dựng theo dõi lỗi, metrics, cảnh báo | Bạn | hạ tầng |
| `C5-FE-01` | Giao diện quản lý tổ chức, thành viên, phân công care team | Bạn | `app/dietitian/**` |
| `C5-FE-02` | Trạng thái job rõ hơn: `queued`, `đang thử lại lần 2/3`, `timeout` | Bạn | `app/dietitian/**` |
| `C5-AGT-01` | Bảo đảm graph chạy được trong worker, không phụ thuộc vòng đời request | R1 | `src/agents/**` |
| `C5-DAT-01` | Gắn `organization_id` vào pipeline đối chiếu/versioning dữ liệu đã xây ở Chặng 2 — dữ liệu dùng chung giữa các tổ chức (`food_items`, `clinical_rules`) không đổi, dữ liệu riêng (`guideline_chunks` nếu tổ chức tự thêm hướng dẫn nội bộ) phải cô lập | R3 | `src/rag/`, `scripts/` |
| `C5-DAT-02` | Mở rộng data release: thêm món/thực phẩm theo phản hồi từ Chặng 2–4, giữ đúng quy trình R2 duyệt | R3 | `data/seeds/**` (R2 duyệt) |

**CP7 — bằng chứng:** chuyên gia phòng khám A **không thấy bệnh nhân của phòng khám B tồn tại**, kiểm bằng test tự động · tắt worker giữa lúc chạy job rồi bật lại, job hoàn thành tiếp hoặc kết thúc với lỗi rõ ràng · R3 xác nhận dữ liệu dùng chung (food/rule) không bị nhân bản sai giữa các tổ chức.

---

### Chặng 6 → CP8 và CP9 · Shadow mode

**Tối thiểu hai tuần, không rút ngắn được.** Đây là chặng R3 chuyển hẳn sang phân tích dữ liệu thật.

| Việc | Người |
|---|:-:|
| Vận hành shadow mode, thu thập số liệu hằng ngày | Bạn |
| Đánh giá lâm sàng: hệ thống có bỏ sót ca nguy hiểm không, có cảnh báo thừa không | **R2** |
| Đo thời gian generation, điểm timeout, số lần gọi LLM và lỗi | R1 |
| **Xây bảng phân tích cho sáu câu hỏi ở CP9** — tổng hợp dữ liệu thật thành số liệu R2/R1 có thể đọc và ra quyết định, không phải cảm tính | **R3** |
| **Theo dõi chất lượng pipeline RAG khi dùng thật** — trợ lý có trích đúng nguồn không, có đoạn nào bị truy hồi sai ngữ cảnh không | **R3** |

**CP8 (bắt đầu):** shadow mode chạy được, không tác động tới bệnh nhân thật, R3 có bảng số liệu cập nhật hằng ngày.

**CP9 (đủ bằng chứng)** — trả lời được sáu câu, **R3 chuẩn bị số liệu, R2 và R1 kết luận**:
1. Hệ thống có bỏ sót trường hợp nguy hiểm không?
2. Có tạo quá nhiều cảnh báo không?
3. Trường hợp nào thường bị chuyên gia override?
4. Báo cáo có giúp giảm thời gian đọc từng bữa không?
5. Generation mất bao lâu, timeout ở đâu?
6. Bệnh nhân có ghi đủ dữ liệu không?

> **Dừng pilot ngay** nếu phát hiện bỏ sót P0, lộ dữ liệu giữa hai tổ chức, mất quyết định duyệt, mất job, hoặc không giải thích được vì sao một bệnh nhân xuất hiện trong hàng chờ.

---

### Chặng 7 → CP10 · Go/No-Go

Thứ tự deploy: schema tương thích trước, rồi backend và worker, rồi frontend. Reuse, cảnh báo tuần và LLM mỗi thứ có **feature flag riêng**.

**CP10 — năm câu hỏi lớn, theo `PRODUCTION_READINESS_MASTER_PLAN.md` mục 8:**

| Câu hỏi | Người trả lời | Bằng chứng |
|---|:-:|---|
| Có dựng lại được hệ thống không? | Bạn | Người mới clone repo dựng được từ đầu; backup đã khôi phục thử |
| Có giải thích được mọi quyết định không? | R1 | Từ một thực đơn truy ngược được hồ sơ, rule, nguồn, generator, người duyệt |
| Có giữ được ranh giới an toàn không? | R2 | LLM không tính số, rule đã ký, thiếu dữ liệu không gọi là ổn định, trợ lý không tự đổi thực đơn, ảnh không vào pipeline nhận diện |
| Hệ thống có chịu được lỗi không? | Bạn | Restart không mất job, LLM timeout không treo, backup khôi phục được |
| Pilot có chứng minh giá trị không? | R2 + R3 | Số liệu từ CP9 |

Cần đủ chữ ký R1, R2, R3 và business owner. Thiếu một phần thì phần đó **tắt bằng feature flag**, không mở nửa vời.

---

## 5. Bảng tổng hợp checkpoint

| CP | Tên | Người xác nhận | Quyền dừng cả đội |
|:-:|---|:-:|:-:|
| CP1 | Nền móng dựng lại được | Bạn | ✅ |
| CP2 | Rule và dữ liệu đã ký, đối chiếu xong | R2 (nội dung) + R3 (đối chiếu) | ✅ |
| CP3 | Sinh được nhiều phương án | R1 + R2 | |
| CP4 | Duyệt có phiên bản + F1 | Bạn | |
| CP5 | Tái sử dụng hai tầng chạy được | Bạn + R1 (vùng miền) | |
| CP6 | Nhật ký, trợ lý có trích dẫn thật, chỉ số | Bạn + R1 + R3 (RAG) | |
| CP7 | Tổ chức + worker bền | Bạn + R3 (dữ liệu dùng chung) | |
| CP8 | Shadow mode bắt đầu | Bạn + R3 | |
| CP9 | Shadow mode đủ bằng chứng | R2 + R3 | ✅ |
| CP10 | Go/No-Go | Cả bốn + business | ✅ |

---

## 6. Rủi ro đã thấy trước

| Rủi ro | Dấu hiệu sớm | Làm gì |
|---|---|---|
| Alembic khó hơn dự tính, revision không tìm lại được | Hết ngày 2 của Chặng 1 chưa có một head | Cả đội dừng việc chạm schema, R1 vào cùng bạn |
| **Bạn thành nút cổ chai** — ôm cả backend, cả hai giao diện, cả DevOps, cả deliverables | Một chặng bất kỳ mà việc dở dang cuối chặng nhiều hơn đầu chặng | R1 nhận bớt phần giao diện đơn giản khi cần; R3 có thể nhận API thuần liên quan dữ liệu (VD endpoint đọc `guideline_chunks`) nếu rảnh tay |
| **Không ai kiểm tra độc lập nữa** — mọi checkpoint đều do người làm ra nó tự xác nhận | Một checkpoint "đạt" nhưng sau đó phát hiện lỗi rõ ràng lẽ ra phải thấy trước | Trước mỗi checkpoint có quyền dừng cả đội (CP1/CP2/CP9), người xác nhận trình bằng chứng cụ thể (lệnh chạy được, ảnh chụp, số liệu) trong standup — cả đội cùng nhìn, không chỉ một người tự nói "xong" |
| Ép làm F2 tầng 2 hoặc F5 sớm hơn thứ tự | Có người tự mở nhánh thứ hai | Từ chối. Thứ tự ưu tiên đã chốt ở `PATIENT_EXPERIENCE_MASTER_PLAN.md` mục 1 |
| **Phát hành F3a mà F3b chưa xong** | Có PR mở chat cho người dùng thật ở Chặng 3 | Chặn merge. Đây là rủi ro an toàn, không phải tính năng nửa vời vô hại |
| **Quên vá vùng miền** | CP5 đạt nhưng không ai hỏi "bản biến thể có đúng vùng không" | R1 xác nhận vùng miền bằng dữ liệu thật, không suy đoán, trước khi CP5 được tính là đạt |
| **RAG ingest sai nguồn hoặc thiếu giấy phép sử dụng lại** | Pipeline chạy được nhưng nội dung trích dẫn không rõ nguồn gốc pháp lý | `C3-DAT-01` bắt buộc R3 và R2 cùng duyệt danh sách nguồn **trước khi** viết pipeline ingest ở `C4-DAT-01`, không ingest rồi mới hỏi |
| R2 quá tải ở Chặng 2 | Hết tuần đầu chưa verify xong nhóm rule rủi ro cao | Cả đội cùng nhập dữ liệu, như đã từng làm với `DAT-02` |

---

## 7. Những phát hiện đã kiểm chứng từ code

Ghi lại để không ai phải khảo sát lại, và để ước lượng công sức cho đúng.

| Phát hiện | Ảnh hưởng |
|---|---|
| `MealPlanOut` **đã trả sẵn trường `highest_risk`** | Badge P0/P1/P2 là việc **thuần frontend** |
| `GET /patients/{id}/observations` đã cho bệnh nhân đọc của mình, nhưng `POST` khoá bằng `require_role("dietitian","admin")` | F4 chỉ cần nới đúng một chỗ, không phải viết API mới |
| Bảng `clinical_notes` và `patient_observations` **đã tồn tại** trong `models.py` | F1 và F4 rẻ hơn dự tính; `clinical_notes` còn thiếu `plan_id` |
| **`substitution_scopes` không chỉ là schema — `src/api/routes/equivalent.py` và `src/agents/equivalent.py` đã là API hoàn chỉnh**, gồm tạo/thu hồi scope, bộ giải CP-SAT tìm tổ hợp món tương đương, tính lại nutrition trên server, và auto-release có 4 điều kiện an toàn kèm audit log riêng | F2 tầng 2 rẻ hơn nhiều so với ước tính ban đầu — chỉ còn thiếu job hằng đêm, UI, và bảng `plan_assignments` |
| **`optimizer.py` và `equivalent.py` không lọc theo `region`** — vùng miền chỉ là gợi ý văn bản mềm cho Gemini trong `gemini_dish_selector.py`, không có tác dụng ở đường CP-SAT thuần | Bản tự sinh biến thể mỗi đêm (F2 tầng 2) có thể lệch vùng miền so với thực đơn gốc mà không ai biết — cần vá trước khi coi CP5 là đạt |
| **`guideline_chunks` chỉ là schema trống — không có `src/rag/`, `ingest.py`, `chunker.py` nào trong repo, không có pipeline truy hồi nào** | Đây là lý do R3 có một mảng việc thật để xây (Chặng 3–4), không phải việc bịa ra cho có |
| Alembic local báo một đầu `c41a7d92e610`; merge `1778fd77cbec` đã nối `c95f302a587e` | Chặng 1 **có thể đã xong phần lớn** — cần xác minh trên production trước khi lo lắng |
| Nút nổi bị cắt nửa ngoài mép phải ở **mọi trang**, cả 1280px và 1440px | Lỗi thật, đã chụp màn hình, phải sửa trước khi làm khung chat |
| Ngày `2031-03-03` lệch 5 năm trong dữ liệu seed | Lỗi dữ liệu, hiện ra cả dashboard lẫn hàng chờ duyệt |
| Danh sách hồ sơ: 2021 hồ sơ, 102 trang, chỉ có nút trang trước sau | Không dùng được ở quy mô thật |
