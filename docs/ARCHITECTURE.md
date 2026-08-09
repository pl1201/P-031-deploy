# ARCHITECTURE — NutriCare Agent

> Deliverable #3 · Phiên bản 1.0 · 26/07/2026
> Nguyên tắc bất biến: **LLM chọn món — Python tính số.**
> Kiến trúc trong file này trung lập về bệnh lý (schema, luồng graph, nguyên tắc). Phạm vi bệnh lý nghiệm thu MVP xem `docs/PRD.md` v2.1 (trọng tâm ĐTĐ2).

---

## 1. Nguyên tắc thiết kế

| # | Nguyên tắc | Diễn giải |
|---|---|---|
| P1 | **Determinism over eloquence** | Bất kỳ thứ gì đo được bằng công thức thì tính bằng code, không hỏi LLM |
| P2 | **No number without source** | Mọi giá trị dinh dưỡng đi kèm `food_id` + `source` + `source_url`; không có nguồn thì không hiển thị |
| P3 | **Human is the last gate** | Không có đường nào từ LLM đến bệnh nhân mà không qua bàn duyệt của chuyên gia |
| P4 | **Fail closed** | Validator nghi ngờ → chặn, không phát hành. Thà không có thực đơn còn hơn có thực đơn sai |
| P5 | **Everything is auditable** | Mọi lần sinh, sửa, duyệt đều ghi log bất biến kèm actor và timestamp |
| P6 | **One database** | Postgres + pgvector. Không thêm hệ quản trị dữ liệu nào nữa |

---

## 2. Sơ đồ tổng thể hệ thống

```mermaid
graph TB
    subgraph Client["Client Layer"]
        PW[Next.js — Patient Portal]
        DW[Next.js — Dietitian Dashboard]
    end

    subgraph API["FastAPI Backend"]
        AUTH[Auth / RBAC — JWT]
        PROF[Profile Service]
        PLAN[Meal Plan Service]
        LOG[Food Log Service]
        REV[HITL Review Service]
        AUD[Audit Logger]
    end

    subgraph CORE["Deterministic Clinical Core — Python thuần"]
        CALC[Nutrition Calculator<br/>BMR / TDEE / định mức]
        RULES[Rules Engine<br/>bounds checker]
        ALG[Allergy + Drug-Food Checker]
        OOV[OOV Estimator]
    end

    subgraph AGENT["LangGraph Agent"]
        GRAPH[StateGraph — 8 nodes]
        CKPT[(Postgres Checkpointer)]
    end

    subgraph DATA["Data Layer — PostgreSQL 16"]
        FOOD[(food_items<br/>dishes / recipes)]
        CLIN[(clinical_rules<br/>drug_food_interactions)]
        USER[(users / profiles<br/>meal_plans / food_logs)]
        VEC[(pgvector — guideline chunks)]
        AUDT[(audit_log — append only)]
    end

    subgraph EXT["External"]
        LLM[LLM API<br/>GPT-4o-mini / Claude Haiku]
        LS[LangSmith Tracing]
    end

    PW --> AUTH
    DW --> AUTH
    AUTH --> PROF & PLAN & LOG & REV
    PLAN --> GRAPH
    REV --> GRAPH
    GRAPH --> CKPT
    GRAPH --> CALC & RULES & ALG & OOV
    GRAPH --> LLM
    GRAPH --> LS
    CALC --> FOOD
    RULES --> CLIN
    ALG --> CLIN
    GRAPH --> VEC
    PROF & PLAN & LOG & REV --> USER
    PROF & PLAN & REV --> AUD --> AUDT

    style CORE fill:#e8f5e9,stroke:#2e7d32
    style AGENT fill:#e3f2fd,stroke:#1565c0
    style EXT fill:#fff3e0,stroke:#ef6c00
```

**Đọc sơ đồ:** khối xanh lá (Clinical Core) là nơi mọi con số được sinh ra — nó **không gọi LLM**. Khối xanh dương (Agent) gọi LLM nhưng chỉ để *chọn* và *diễn đạt*.

---

## 3. Luồng LangGraph Agent

> **Cập nhật 2026-08-09:** mục này trước đây mô tả graph 8-node ban đầu (thiết kế lúc lập kiến trúc). Graph thật trong `src/agents/graph.py` hiện có **15 node** (an toàn hơn: fail-closed có kiểm soát, gate ngưỡng lâm sàng tách riêng, phân loại rủi ro P0/P1/P2, audit đầy đủ). Đặc tả chi tiết từng lớp thay đổi + lý do: `docs/LANGGRAPH_ARCHITECTURE_COMPARISON.md`. Bản Mermaid dưới đây đồng bộ lại cho khớp `main`.

```mermaid
flowchart TD
    S([START]) --> LP[1. load_profile]
    LP -->|failed| E([END])
    LP -->|continue| CT[2. compute_targets<br/>DETERMINISTIC]

    CT --> TG{3. target_gate<br/>DETERMINISTIC}
    TG -->|conflict / unverified| MR[12. prepare_manual_review]
    TG -->|safe| RC[4. retrieve_context_bundle<br/>hybrid RAG + food candidates SQL]

    RC --> SC[5. build_safety_constraints]
    SC --> GM[6. generate_menu<br/>CP-SAT / Gemini hybrid]
    GM --> CN[7. compute_nutrition<br/>DETERMINISTIC · SQL sum]
    CN --> SV[8. safety_validate<br/>bounds + dị ứng + tương tác thuốc]
    SV --> RT{9. risk_triage<br/>P0/P1/P2}

    RT -->|không P0| EX[13. explain_with_citations<br/>LLM · diễn giải kèm citation]
    RT -->|P0 và retry lt 3| BF[10. build_feedback<br/>lỗi cụ thể vào prompt]
    BF --> GM
    RT -->|P0 và retry gte 3| FB[11. fallback_template<br/>gắn cờ needs_attention]
    FB --> CN

    MR --> EX
    EX --> RP[14. prepare_review_packet]
    RP --> HITL[[15. to_review — interrupt HITL QUEUE]]
    HITL -->|Chuyên gia APPROVE| PUB([Phát hành cho bệnh nhân])
    HITL -->|Chuyên gia EDIT| CN
    HITL -->|Chuyên gia REJECT + lý do| BF

    style CT fill:#c8e6c9
    style CN fill:#c8e6c9
    style SV fill:#c8e6c9
    style GM fill:#bbdefb
    style EX fill:#bbdefb
    style HITL fill:#ffe0b2,stroke:#e65100,stroke-width:3px
```

### `generate_menu` — CP-SAT/hybrid (đã triển khai, không phải chỉ LLM)

`src/agents/hybrid.py::HybridMenuGenerator` là generator thật đang dùng trong `generate_menu` (wired qua `AGT-10`) — ưu tiên giải bằng OR-Tools **CP-SAT chế độ feasibility-only** (đo được nhanh hơn nhiều so với chế độ tối đa hoá hàm mục tiêu: ~0,1s OPTIMAL so với ~105s rồi UNKNOWN), Gemini chỉ được gọi khi CP-SAT không tìm được nghiệm khả thi hoặc để chọn giữa các nghiệm hợp lệ (structured output, chỉ `food_id`+gram — RULE-1 vẫn giữ nguyên qua lớp này). Khi bài toán vô nghiệm vì tủ lạnh/nguyên liệu sẵn có không đủ, `src/agents/equivalent.py` (thực đơn tương đương, P2/AGT-12) tái dùng CP-SAT với tập ứng viên và dải ràng buộc thu hẹp quanh thực đơn gốc — "tương đương" được định nghĩa bằng ràng buộc toán học, không phải LLM phán đoán ngữ nghĩa.

### Vì sao node 7 (`compute_nutrition`) tách khỏi node 6 (`generate_menu`)

LLM/CP-SAT ở node 6 chỉ trả về JSON dạng:

```json
{"meals": [{"slot": "breakfast", "items": [{"food_id": 1042, "grams": 180}]}]}
```

Node 7 tự truy vấn SQL và tính tổng. **LLM không bao giờ nhìn thấy hay sinh ra con số kcal.** Đây là cơ chế chống bịa số ở tầng kiến trúc, không phải ở tầng prompt — mạnh hơn nhiều so với việc dặn LLM "đừng bịa".

### Explainer & Coaching cho bệnh nhân — dịch vụ ngoài graph (đang xây, chưa merge)

Khác với `explain_with_citations` (node 13, giải thích cho chuyên gia TRƯỚC khi duyệt), tính năng "Menu Explainer & Coaching" đang phát triển (PR #77 — B1 deterministic, `AGT-13` — B2 LLM+route) giải thích **thực đơn đã `approved`** cho bệnh nhân bằng ngôn ngữ tự nhiên. Đây là **endpoint gọi theo yêu cầu (`GET /meal-plans/{id}/explain`), KHÔNG phải node trong graph** — vì mọi node hiện tại chạy trước khi duyệt, còn việc duyệt (`POST /reviews/{planId}/approve`) chỉ đổi `status` trên DB, không resume graph. `src/clinical/menu_explainer.py` (assembler tất định) + `src/services/menu_explanation_guard.py` (chặn bịa số) + `src/services/menu_coach.py` (LLM văn phong hoá, B2) theo đúng mẫu đã dùng cho `target_assistant.py` (P1).

### State schema

> Cập nhật 2026-08-09: state thật trong `src/agents/graph.py` đã mở rộng nhiều so với bản thiết kế ban đầu bên dưới — thêm version/hash để audit, `target_gate`/`risk_triage`/`review_packet` cho luồng 15-node. Xem đặc tả nhóm trường đầy đủ + lý do mở rộng: `docs/LANGGRAPH_ARCHITECTURE_COMPARISON.md` §6 ("State hiện tại"). Khối dưới đây giữ lại làm ví dụ khái niệm ban đầu, không phải state thật hiện tại.

```python
class NutriState(TypedDict):
    # Input
    patient_id: str
    request_type: Literal["daily", "weekly", "family_meal"]
    date_range: tuple[date, date]

    # Deterministic outputs
    profile: PatientProfile
    targets: ClinicalTargets        # kcal, protein_g, na_mg, k_mg, p_mg, purine_mg, fiber_g
    applied_rule_ids: list[str]

    # RAG
    guideline_chunks: list[Chunk]
    candidate_foods: list[FoodItem]

    # Agent loop
    draft_menu: MenuDraft | None
    computed_nutrition: NutritionSummary | None
    violations: list[Violation]
    retry_count: int                # max 3
    feedback: str | None

    # HITL
    status: Literal["drafting","pending_review","approved","rejected","published"]
    reviewer_id: str | None
    reviewer_notes: str | None

    # Audit
    trace_id: str
    sources: list[SourceRef]        # bắt buộc không rỗng khi status=approved
```

---

## 4. Luồng HITL (sequence)

```mermaid
sequenceDiagram
    actor D as Chuyên gia dinh dưỡng
    actor P as Bệnh nhân
    participant FE as Next.js
    participant BE as FastAPI
    participant AG as LangGraph
    participant DB as Postgres

    P->>FE: Yêu cầu thực đơn tuần
    FE->>BE: POST /meal-plans
    BE->>AG: invoke(state)
    AG->>AG: targets → retrieve → generate → validate
    AG->>DB: lưu draft, status=pending_review
    AG-->>BE: interrupt(thread_id)
    BE-->>FE: 202 Accepted — "Đang chờ chuyên gia duyệt"
    Note over P,FE: Bệnh nhân KHÔNG thấy nội dung thực đơn ở bước này

    D->>FE: Mở Review Queue
    FE->>BE: GET /reviews/pending
    BE->>DB: SELECT ... status=pending_review
    BE-->>FE: danh sách + cảnh báo + nguồn
    D->>FE: Sửa 120g → 90g cơm, Approve
    FE->>BE: POST /reviews/{id}/approve
    BE->>AG: Command(resume={"action":"approve","edits":[...]})
    AG->>AG: compute_nutrition lại với gram đã sửa
    AG->>DB: status=approved + audit_log
    BE-->>FE: 200 OK
    FE-->>P: Thông báo — thực đơn đã sẵn sàng
```

---

## 5. Mô hình dữ liệu

> ⚠️ **2026-08-05 (BE-01):** ERD dưới đây build ra thẳng từ `src/db/models.py`
> (SQLAlchemy, nguồn sự thật cho DDL) — 2 bản mô tả cùng 1 schema, sửa bên
> này phải sửa bên kia. So với bản vẽ ban đầu ở S1 (trước khi có dữ liệu
> thật), đã bổ sung 6 bảng: `dishes`, `dish_ingredients`, `serving_sizes`,
> `patient_medications`, `patient_allergies`, `food_logs`, `guideline_chunks`
> — những bảng này đã tồn tại thật trong `data/seeds/`/ticket DAT-04/DAT-06/
> CLN-05/CLN-06/BE-07 nhưng ERD cũ chưa vẽ ra. Đã build + chạy thật
> `alembic upgrade head` / `downgrade base` trên SQLite trắng — xem `alembic/`.

```mermaid
erDiagram
    users ||--o| patient_profiles : has
    users ||--o{ meal_plans : "reviewed_by"
    patient_profiles ||--o{ meal_plans : for
    patient_profiles ||--o{ food_logs : logs
    patient_profiles ||--o{ patient_medications : takes
    patient_profiles ||--o{ patient_allergies : has
    meal_plans ||--|{ meal_plan_items : contains
    meal_plan_items }o--|| food_items : references
    food_logs }o--o| food_items : "references (null nếu OOV)"
    dishes ||--|{ dish_ingredients : "made of"
    dish_ingredients }o--|| food_items : uses
    meal_plans ||--o{ audit_log : generates

    users {
        string id PK "UUID"
        string email UK
        string password_hash
        string role "patient|dietitian|admin"
    }
    patient_profiles {
        string id PK "UUID"
        string user_id FK
        int age
        string sex
        float height_cm
        float weight_kg
        json conditions "ICD10 + stage"
        json lab_values "eGFR, HbA1c, K, uric"
        string activity_level
        string region "north|central|south"
    }
    patient_medications {
        string id PK "UUID"
        string profile_id FK
        string drug_name
        string dosage
        date started_at
    }
    patient_allergies {
        string id PK "UUID"
        string profile_id FK
        string allergen "VD hải sản, đậu phộng"
    }
    food_items {
        int id PK
        string name_vi
        json aliases "OOV synonyms"
        string category
        float kcal_100g
        float protein_g
        float carb_g
        float fat_g
        float fiber_g
        float sugar_g
        float na_mg
        float k_mg
        float p_mg
        float purine_mg
        string purine_source_ref
        float gi_index
        string gi_source
        string gi_source_ref
        json contains_allergens
        string source "NIN|USDA|curated|estimated"
        string source_ref
        bool is_estimated
    }
    dishes {
        string dish_id PK
        string name_vi
        string region "north|central|south"
        float serving_g
        string verified_by
        string note
    }
    dish_ingredients {
        int id PK
        string dish_id FK
        int food_id FK
        float grams
        string note
    }
    serving_sizes {
        int id PK
        string category
        float serving_g
        string note
        string source
    }
    clinical_rules {
        string rule_id PK
        string condition_code
        string stages
        string nutrient
        string bound "min|max"
        float value
        string unit
        string basis "absolute|per_kg|pct_energy|per_1000kcal"
        string severity "hard|soft"
        string guideline_ref
        string guideline_grade
        string verify_status
        string overridden_by
    }
    drug_food_interactions {
        int id PK
        string drug_name
        string drug_class
        string food_or_nutrient
        string severity "high|moderate|low"
        string mechanism_vi
        string recommendation_vi
        string source_ref
        string verify_status
    }
    food_food_interactions {
        int id PK
        string substance_a
        string substance_b
        string food_examples_vi
        string mechanism_vi
        string direction "increases|decreases"
        string effect_size_vi
        string clinical_significance "high|moderate|low"
        string applies_to_condition "T2DM|HTN|CKD|GOUT|null"
        string recommendation_vi
        string source_ref
        string pmid
        string verify_status
    }
    drug_meal_timing {
        int id PK
        string drug_name
        string drug_class
        string timing_rule "before|with|after|avoid_with"
        int offset_minutes
        string relative_to "VD bữa ăn, cà phê"
        string rationale_pk_vi
        string condition "T2DM|HTN|CKD|GOUT|null"
        string source_ref
        string page_ref
        string verify_status
    }
    guideline_chunks {
        string id PK "UUID"
        string source "VD ADA 2025, KDIGO 2024"
        string title
        int page
        string condition_code
        string content
        json embedding "pgvector.Vector khi có Postgres thật, JSON tạm trên SQLite"
    }
    meal_plans {
        string id PK "UUID"
        string profile_id FK
        date plan_date
        string status
        json targets
        json computed_nutrition
        json violations
        int retry_count
        string reviewer_id FK
        string reviewer_notes
        string trace_id
    }
    meal_plan_items {
        string id PK "UUID"
        string plan_id FK
        string slot "breakfast|lunch|dinner|snack"
        int food_id FK
        float grams
    }
    food_logs {
        string id PK "UUID"
        string profile_id FK
        datetime logged_at
        int food_id FK "null nếu gõ tự do (OOV)"
        string free_text_vi "tên gõ tay khi chưa có trong DB"
        float grams
        bool is_estimated "true nếu qua OOV Estimator (CLN-07)"
    }
    audit_log {
        int id PK
        datetime at
        string actor_id
        string action
        json before
        json after
    }
```

### Bảng bắt buộc có cột `source`

`food_items`, `dishes`, `clinical_rules`, `drug_food_interactions`, `food_food_interactions`, `drug_meal_timing`, `guideline_chunks`.
**CI có test chặn: không dòng nào được có `source IS NULL`.**

### Vì sao `dish_ingredients`/`meal_plan_items`/`food_logs` không tự tính dinh dưỡng

Đúng RULE-1: các bảng này chỉ lưu `food_id` + `grams` (+ `slot` cho thực đơn).
Không cột nào lưu sẵn kcal/Na/protein của dòng — mọi tổng dinh dưỡng tính lại
bằng SQL từ `food_items` tại thời điểm đọc, không bao giờ cache giá trị đã
tính (tránh lệch khi `food_items` được sửa lại sau).

---

## 6. Hợp đồng API (v1)

| Method | Endpoint | Role | Mô tả |
|---|---|---|---|
| POST | `/api/v1/auth/login` | public | JWT |
| GET | `/api/v1/health` | public | Health check |
| POST | `/api/v1/profiles` | patient, dietitian | Tạo/cập nhật hồ sơ |
| GET | `/api/v1/profiles/me` | patient | Hồ sơ của mình |
| POST | `/api/v1/targets/compute` | dietitian | Tính định mức lâm sàng (không cần LLM) |
| POST | `/api/v1/meal-plans` | patient, dietitian | Sinh thực đơn → trạng thái `pending_review` |
| GET | `/api/v1/meal-plans` | patient | Chỉ trả về `status=approved` |
| GET | `/api/v1/meal-plans/{id}` | owner, dietitian | Chi tiết + nguồn + cảnh báo |
| GET | `/api/v1/reviews/pending` | **dietitian** | Hàng chờ duyệt |
| POST | `/api/v1/reviews/{id}/approve` | **dietitian** | Duyệt (kèm edits tuỳ chọn) |
| POST | `/api/v1/reviews/{id}/reject` | **dietitian** | Từ chối + lý do (bắt buộc) |
| POST | `/api/v1/food-logs` | patient | Ghi nhật ký |
| GET | `/api/v1/food-logs/summary` | patient, dietitian | Tổng hợp ngày/tuần + cảnh báo ngưỡng |
| POST | `/api/v1/family-meal/decompose` | patient | Phân rã mâm cơm |
| GET | `/api/v1/shopping-list/{plan_id}` | patient | Danh sách đi chợ |
| POST | `/api/v1/chat` | patient, dietitian | Hội thoại (có guardrail chặn chỉ định y khoa) |

**Response envelope chuẩn** — mọi response chứa dữ liệu dinh dưỡng phải có:

```json
{
  "data": { "...": "..." },
  "sources": [
    {"food_id": 1042, "name": "Gạo tẻ máy", "source": "NIN", "ref": "Bảng TPTP VN 2007, tr.42"}
  ],
  "warnings": [
    {"type": "drug_food", "severity": "high", "message": "Bưởi tương tác với Atorvastatin"}
  ],
  "disclaimer": "Thông tin mang tính tham khảo, không thay thế chỉ định của bác sĩ. Đã được duyệt bởi CN. Nguyễn Văn X lúc 20/08/2026 14:32."
}
```

---

## 7. Kiến trúc Guardrails — 4 tầng

```mermaid
graph LR
    IN[Input] --> L1[Tầng 1: Input Guard<br/>chặn câu hỏi chỉ định/chẩn đoán<br/>regex + LLM classifier]
    L1 --> L2[Tầng 2: Structured Output<br/>Pydantic schema · LLM chỉ trả food_id + gram]
    L2 --> L3[Tầng 3: Deterministic Validator<br/>bounds · dị ứng · tương tác thuốc<br/>fail closed]
    L3 --> L4[Tầng 4: Human Review<br/>HITL bắt buộc]
    L4 --> OUT[Output tới bệnh nhân]

    style L3 fill:#c8e6c9
    style L4 fill:#ffe0b2
```

| Tầng | Chặn được gì | Không chặn được gì |
|---|---|---|
| 1. Input Guard | "Tôi bị bệnh gì?", "Giảm liều insulin được không?" | Câu hỏi ẩn ý |
| 2. Structured Output | LLM bịa số kcal, bịa tên thực phẩm | LLM chọn món không phù hợp |
| 3. Validator | Vượt ngưỡng Na/K/P/kcal, dị ứng, tương tác thuốc | Sai sót lâm sàng tinh vi |
| 4. HITL | Phần còn lại | — (đây là chốt chặn cuối) |

**Câu trả lời chuẩn khi Tầng 1 kích hoạt:**
> "Mình không thể đưa ra chẩn đoán hay điều chỉnh thuốc — việc đó thuộc thẩm quyền của bác sĩ điều trị. Mình có thể giúp bạn về khẩu phần ăn trong khuôn khổ chỉ định sẵn có. Bạn muốn mình chuyển câu hỏi này tới chuyên gia dinh dưỡng đang phụ trách bạn không?"

---

## 8. Bảo mật & Quyền riêng tư

| Khía cạnh | Thiết kế v1 |
|---|---|
| Xác thực | JWT (access 30 phút + refresh), argon2id cho mật khẩu |
| Phân quyền | RBAC ở tầng dependency của FastAPI, **kiểm tra ở cả API lẫn query** (bệnh nhân chỉ đọc `patient_id = current_user.profile_id`) |
| PHI trong prompt | **Không gửi tên, email, CCCD, địa chỉ vào LLM.** Chỉ gửi: tuổi, giới, cân nặng, chiều cao, mã bệnh, chỉ số xét nghiệm, danh sách thuốc |
| Mã hoá | TLS trên đường truyền; cột nhạy cảm dùng `pgcrypto` hoặc mã hoá tầng ứng dụng |
| Logging | Logger có filter tự động che PII; **cấm `print()`** |
| Audit | `audit_log` append-only, không có endpoint DELETE |
| Dữ liệu | NHANES 2021–2023 public-use, de-identified được phép cho dev/test; benchmark eval vẫn là synthetic; cấm SEQN/PII trong prompt và log |
| Tuân thủ | Tham chiếu Nghị định 13/2023/NĐ-CP. **Không tuyên bố "HIPAA compliant"** — chỉ nói "thiết kế theo nguyên tắc tối thiểu hoá dữ liệu" |

---

## 9. Deployment

```mermaid
graph TB
    subgraph GH[GitHub]
        REPO[Repository] --> CI[Actions: ruff + mypy + pytest + docker build]
    end
    CI -->|push develop| STG
    CI -->|push main| PRD

    subgraph STG[Staging]
        S1[Render — API]
        S2[Vercel Preview — Web]
    end
    subgraph PRD[Production]
        P1[Render — FastAPI + Uvicorn]
        P2[Vercel — Next.js]
        P3[(Neon/Supabase — Postgres + pgvector)]
        P4[LangSmith]
    end
    P2 --> P1 --> P3
    P1 --> P4
```

- **Backend:** Render Web Service, Docker multi-stage, health check `/api/v1/health`
- **Frontend:** Vercel, biến `NEXT_PUBLIC_API_URL`
- **DB:** Neon free tier (có pgvector) hoặc Supabase — nếu chọn Supabase, chỉ dùng làm Postgres hosted thuần, xem ràng buộc ở ADR-008
- **Secrets:** chỉ qua env vars của platform, **không bao giờ trong repo**
- **Cold start Render free tier ~50s** → trước demo phải "warm up" bằng cách gọi health check

---

## 10. Cấu trúc thư mục (mở rộng từ template AI20K)

```
├── src/
│   ├── agents/
│   │   ├── graph.py               # StateGraph, edges, checkpointer
│   │   ├── state.py               # NutriState
│   │   ├── nodes/
│   │   │   ├── load_profile.py
│   │   │   ├── compute_targets.py     # KHÔNG gọi LLM
│   │   │   ├── retrieve_context.py
│   │   │   ├── generate_menu.py       # gọi LLM
│   │   │   ├── compute_nutrition.py   # KHÔNG gọi LLM
│   │   │   ├── validate.py            # KHÔNG gọi LLM
│   │   │   └── explain.py             # gọi LLM
│   │   └── tools/
│   │       ├── food_search.py
│   │       ├── nutrition_calculator.py
│   │       ├── meal_planner.py
│   │       └── interaction_checker.py
│   ├── clinical/                  # ⭐ Deterministic core — trái tim dự án
│   │   ├── energy.py              # BMR, TDEE
│   │   ├── targets.py             # định mức theo bệnh lý
│   │   ├── rules_engine.py        # bounds checker
│   │   ├── allergy.py
│   │   ├── drug_food.py
│   │   └── oov_estimator.py
│   ├── rag/
│   │   ├── ingest.py
│   │   ├── chunker.py
│   │   └── hybrid_search.py       # BM25 + pgvector
│   ├── api/routes/
│   │   ├── auth.py · profiles.py · meal_plans.py
│   │   ├── reviews.py · food_logs.py · chat.py
│   ├── models/                    # Pydantic schemas
│   ├── db/                        # SQLAlchemy models, Alembic
│   ├── core/                      # config, logging, security
│   └── main.py
├── web/                           # Next.js (nếu tách repo thì bỏ)
├── data/
│   ├── seeds/food_items.csv       # có cột source
│   ├── seeds/clinical_rules.csv
│   ├── seeds/drug_food.csv
│   └── guidelines/                # PDF/MD để ingest RAG
├── eval/
│   ├── datasets/cases_60.jsonl
│   ├── scripts/run_eval.py
│   └── results/report.md          # Deliverable #10
├── tests/{unit,integration,eval}
├── docs/                          # tài liệu này
├── DEVLOG.md                      # Deliverable #8 + #9
└── CLAUDE.md                      # rules cho AI coding agent
```

---

## 11. Architecture Decision Records (rút gọn)

| ADR | Quyết định | Lựa chọn thay thế đã cân nhắc | Lý do chọn |
|---|---|---|---|
| ADR-001 | Postgres + pgvector, không dùng Qdrant | Qdrant, Milvus, Chroma | Dưới 5.000 chunk; giảm 1 service; 1 connection string |
| ADR-002 | LLM chỉ trả `food_id` + gram | Cho LLM trả cả giá trị dinh dưỡng | Nghiên cứu chứng minh LLM lệch định lượng hệ thống; đây là chống bịa ở tầng kiến trúc |
| ADR-003 | 1 graph (nay 15 node, mở rộng từ thiết kế ban đầu 8 node — xem `docs/LANGGRAPH_ARCHITECTURE_COMPARISON.md`), không 5 agent rời | Multi-agent CrewAI | Debug được, latency thấp, vẫn thể hiện được agentic loop |
| ADR-004 | HITL bằng LangGraph `interrupt` + checkpointer | Bảng status thuần | Đúng chuẩn LangGraph, resume được state; **có fallback nếu quá phức tạp** |
| ADR-005 | Drug-food curated 80 cặp thay vì DDID 23.950 | Import DDID | License chưa rõ; 80 cặp đủ bao phủ 4 nhóm bệnh của đề bài |
| ADR-006 | Render + Vercel, không K8s | AWS EKS, GCP GKE | 6 tuần, free tier, không được thêm điểm nếu dùng K8s |
| ADR-007 | Fail closed | Cảnh báo rồi vẫn hiển thị | Bối cảnh y tế; sai sót có hậu quả thật |
| ADR-008 | Supabase = hosted Postgres+pgvector thuần (nếu chọn thay Neon), KHÔNG dùng RLS/Auth/CLI migration của Supabase | Dùng full stack Supabase (Auth + RLS + Supabase CLI migrations) | Auth (JWT+argon2id) và authorization (chặn ở tầng query FastAPI, VD `_get_owned_profile`) đã tự xây — thêm RLS tạo 2 tầng phân quyền phải đồng bộ tay, dễ lệch. Alembic đã là nguồn chân lý schema duy nhất — dùng song song Supabase CLI migrations tạo 2 nguồn cạnh tranh. Free tier Supabase tự pause sau 1 tuần không hoạt động — cần lưu ý trước demo. Xem research 2026-08-07 trong `DEVLOG.md` |

---

## 12. Những gì hệ thống KHÔNG làm (nói rõ trong demo)

- ❌ Không chẩn đoán bệnh
- ❌ Không kê đơn, không điều chỉnh liều thuốc
- ❌ Không thay thế bác sĩ hay chuyên gia dinh dưỡng
- ❌ Không xử lý dữ liệu định danh hoặc dữ liệu bệnh nhân Việt Nam thật; NHANES public-use chỉ dùng trong phạm vi nghiên cứu/dev/test đã công bố
- ❌ Không tự động phát hành thực đơn khi chưa có người duyệt

> Liệt kê rõ ràng những gì mình *không* làm là dấu hiệu của một đội hiểu bài toán y tế. Đưa slide này vào pitch deck.
