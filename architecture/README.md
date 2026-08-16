# Architecture — NutriCare Agent

> Sơ đồ Mermaid, render trực tiếp trên GitHub — không cần mở file ảnh. Nguồn đối chiếu trực tiếp với code tại thời điểm viết (16/08/2026): `src/agents/graph.py`, `src/agents/nodes/core.py`, `src/api/routes/`, `src/api/security.py`, `src/services/llm.py`, `src/db/models.py`.
>
> Bản đầy đủ hơn (ERD 15 bảng, sequence chi tiết, guardrail 4 tầng): [`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md). File này là bản tóm tắt tập trung đúng khung đánh giá: Frontend / Backend / Agent / Vector DB / API ngoài + luồng dữ liệu.

## Mục lục

1. [System Context](#1-system-context)
2. [Container & Component View](#2-container--component-view)
3. [Data Flow](#3-data-flow)
4. [AI Agent & Safety Pipeline](#4-ai-agent--safety-pipeline)
5. [Authentication & Authorization](#5-authentication--authorization)
6. [UI Flow](#6-ui-flow)
7. [Deployment Topology](#7-deployment-topology)

---

## 1. System Context

Ai dùng hệ thống và hệ thống nói chuyện với dịch vụ ngoài nào. Không tác nhân nào tự động nhận thực đơn — mọi mũi tên tới "Bệnh nhân" chỉ mang dữ liệu đã `status=approved`.

```mermaid
graph LR
    Patient["👤 Bệnh nhân<br/>mãn tính (ĐTĐ2…)"]
    Dietitian["🩺 Chuyên gia dinh dưỡng<br/>chốt chặn duyệt (RULE-3)"]

    subgraph SYS["NutriCare Agent"]
        System["FastAPI + LangGraph<br/>+ PostgreSQL/pgvector"]
    end

    Gemini["Gemini / OpenAI<br/>chọn food_id + gram (RULE-1)"]
    USDA["USDA FoodData Central<br/>tra cứu khi thiếu dữ liệu"]
    LangSmith["LangSmith<br/>trace debug (tuỳ chọn)"]

    Patient -->|xem thực đơn approved,<br/>ghi nhật ký ăn uống| System
    Dietitian -->|duyệt / sửa / từ chối| System
    System -->|structured output| Gemini
    System -.->|tra cứu bổ sung| USDA
    System -.->|trace| LangSmith
```

## 2. Container & Component View

Chi tiết dễ bỏ sót: **Agent và Clinical Core không phải service riêng** — chạy trong cùng tiến trình Python với FastAPI, gọi qua `BackgroundTasks` (threadpool), không phải RPC qua mạng. Vector DB (pgvector) đã có schema nhưng pipeline ingest/retrieval **chưa nối dây** (xem ghi chú trong sơ đồ 3).

```mermaid
graph TB
    subgraph FE["FRONTEND — web-next/ (Vercel, Next.js App Router)"]
        PW["Patient App<br/>app/patient/*"]
        DW["Dietitian App<br/>app/dietitian/*"]
    end

    subgraph PROC["BACKEND — Render Web Service (1 container, 1 process)"]
        API["FastAPI — src/api/routes<br/>auth · patients · targets<br/>meal_plans · reviews · food_logs<br/>JWT + RBAC ở mọi route"]
        AGENT["AGENT — src/agents<br/>graph.py (LangGraph, 15 node)<br/>hybrid.py / equivalent.py (CP-SAT)<br/>⭐ 1 node duy nhất gọi LLM"]
        CORE["CLINICAL CORE — src/clinical<br/>energy · targets · rules_engine<br/>allergy · drug_food · validator<br/>cấm import LLM client (test chặn)"]
    end

    DB[("PostgreSQL 16 + pgvector<br/>Neon/Supabase<br/>food_items · clinical_rules<br/>meal_plans · audit_log<br/>guideline_chunks (schema — chưa dùng)")]

    Gemini["Gemini API (ngoài)"]

    PW -->|HTTPS /api/v1| API
    DW -->|HTTPS /api/v1| API
    API -->|BackgroundTasks| AGENT
    AGENT --> CORE
    AGENT -.->|generate_menu| Gemini
    CORE --> DB
    API --> DB
    AGENT --> DB

    style AGENT fill:#e3f2fd,stroke:#1565c0
    style CORE fill:#e8f5e9,stroke:#2e7d32
    style Gemini fill:#fff3e0,stroke:#ef6c00
```

## 3. Data Flow

Dữ liệu **thật sự** di chuyển qua đâu trong một lượt sinh thực đơn — không phải sơ đồ component, mà là hành trình của con số dinh dưỡng, từ hồ sơ bệnh nhân tới màn hình bệnh nhân, đi qua đúng ranh giới RULE-1 (LLM chỉ chọn món) và RULE-3 (chỉ `approved` mới ra ngoài).

```mermaid
flowchart LR
    A["PatientProfile<br/>(DB)"] --> B["compute_targets()<br/>SQL/Python — ngưỡng theo bệnh lý"]
    B --> C["candidate shortlisting<br/>src/agents/nodes/core.py<br/>lọc dị ứng/thích, chọn top-k tất định"]
    C --> D["generate_menu<br/>LLM — CHỈ trả food_id + gram"]
    D --> E["compute_nutrition()<br/>SQL — sum kcal/Na/K/P từ food_items"]
    E --> F["safety_validate()<br/>so khớp thực đơn ↔ ngưỡng"]
    F --> G{"risk_triage<br/>P0/P1/P2"}
    G -->|P0| D
    G -->|P1/P2/không P0| H["review packet<br/>+ nguồn NIN/USDA"]
    H --> I[("meal_plans<br/>status=pending_review")]
    I --> J["Chuyên gia duyệt<br/>POST /reviews/approve"]
    J --> K[("meal_plans<br/>status=approved")]
    K --> L["Patient App<br/>GET /meal-plans<br/>chỉ đọc approved"]

    RAG["guideline_chunks + pgvector<br/>❌ pipeline ingest/retrieval chưa triển khai"]
    C -.->|dự kiến, chưa nối| RAG

    style D fill:#e3f2fd,stroke:#1565c0
    style E fill:#e8f5e9,stroke:#2e7d32
    style F fill:#e8f5e9,stroke:#2e7d32
    style B fill:#e8f5e9,stroke:#2e7d32
    style J fill:#fff3e0,stroke:#ef6c00
    style RAG fill:#f5f5f5,stroke:#9e9e9e,stroke-dasharray: 5 5
```

**Điểm mấu chốt:** node xanh dương (`generate_menu`) là nơi duy nhất LLM chạm vào dữ liệu — và nó chỉ trả về `food_id`+gram. Mọi ô xanh lá là tính toán tất định bằng SQL/Python. Nhánh RAG (xám, nét đứt) được vẽ để trung thực về hiện trạng: bảng đã có, chưa được nối vào luồng chọn món.

## 4. AI Agent & Safety Pipeline

`src/agents/graph.py` — 15 node. Hai điểm rẽ nhánh: xung đột mục tiêu lâm sàng đi thẳng sang duyệt thủ công; rủi ro **P0** vòng lại sinh thực đơn tối đa 3 lần rồi mới dùng mẫu dự phòng. **P1/P2** không chặn — đi tiếp kèm cảnh báo tới bàn duyệt (fail-closed có kiểm soát, không fail-silent).

```mermaid
flowchart TD
    START(["START"]) --> LP["load_profile"]
    LP --> CT["compute_targets"]
    CT --> TG{"target_gate<br/>min > max?"}
    TG -->|xung đột| MR["prepare_manual_review"]
    TG -->|an toàn| RC["retrieve_context_bundle"]
    RC --> SC["build_safety_constraints"]
    SC --> GM["generate_menu<br/>🤖 LLM"]
    GM --> CN["compute_nutrition<br/>SQL"]
    CN --> SV["safety_validate"]
    SV --> RT{"risk_triage<br/>P0 / P1 / P2"}
    RT -->|"P0, thử < 3"| BF["build_feedback"]
    BF --> GM
    RT -->|"P0, thử ≥ 3"| FB["fallback_template"]
    FB --> CN
    RT -->|"không P0"| EX["explain_with_citations<br/>🤖 LLM, trích NIN/USDA"]
    MR --> EX
    EX --> RP["prepare_review_packet"]
    RP --> TR["to_review<br/>⏸ interrupt_before — chờ duyệt"]

    style GM fill:#e3f2fd,stroke:#1565c0
    style EX fill:#e3f2fd,stroke:#1565c0
    style CT fill:#e8f5e9,stroke:#2e7d32
    style CN fill:#e8f5e9,stroke:#2e7d32
    style SV fill:#e8f5e9,stroke:#2e7d32
    style TR fill:#fff3e0,stroke:#ef6c00,stroke-width:3px
    style MR fill:#fff3e0,stroke:#ef6c00
```

### Phân cấp cảnh báo (`risk_triage`)

| Tầng | Ý nghĩa | Hành vi |
|---|---|---|
| **P0** | Nguy hiểm (vượt ngưỡng cứng, tương tác thuốc nặng...) | Chặn phát hành, `build_feedback` → sinh lại tối đa 3 lần → `fallback_template` |
| **P1** | Cảnh báo | Đi tiếp, gắn `warning` vào review packet cho chuyên gia |
| **P2** | Thông tin | Ghi chú tham khảo, không chặn |

## 5. Authentication & Authorization

Hai lớp tách biệt: **role check** (thô, ở tầng dependency `require_role`) và **row-level ownership filter** (mịn, ở tầng query) — thiếu lớp thứ hai là lỗ hổng IDOR kinh điển, dự án có cả hai.

```mermaid
sequenceDiagram
    participant U as Client
    participant API as FastAPI
    participant Auth as security.py
    participant Q as Query layer

    U->>API: POST /auth/login {email, password}
    API->>Auth: verify_password (argon2id)
    Auth-->>API: OK
    API-->>U: access_token (15p) + refresh_token (7n), HS256

    U->>API: GET /meal-plans (Bearer token)
    API->>Auth: get_current_user() — decode + kiểm type=access
    Auth-->>API: CurrentUser(id, role)
    API->>Auth: require_role("patient") — LỚP 1, thô
    Auth-->>API: 403 nếu sai role

    API->>Q: LỚP 2 — filter theo query<br/>.filter(user_id == current_user.id, status == "approved")
    Q-->>API: chỉ dữ liệu của chính chủ
    API-->>U: 200 OK
```

## 6. UI Flow

Hai luồng màn hình tách biệt theo vai trò — bệnh nhân không bao giờ có đường vào hàng chờ duyệt; chuyên gia là cổng bắt buộc trước khi bệnh nhân thấy bất kỳ thực đơn nào.

```mermaid
flowchart TD
    Login["/login"] -->|role=patient| PDash["/patient — Dashboard"]
    Login -->|role=dietitian| DDash["/dietitian — Dashboard"]

    subgraph PATIENT["Luồng Bệnh nhân"]
        PDash --> PProfile["/patient/profile<br/>cập nhật hồ sơ"]
        PDash --> PRequest["Yêu cầu thực đơn<br/>POST /meal-plans"]
        PRequest -.->|202, chạy nền| PWait["chờ — chưa thấy nội dung"]
        PDash --> PWeekly["/patient/weekly<br/>xem thực đơn approved"]
        PDash --> PDiary["/patient/diary<br/>ghi nhật ký ăn uống"]
    end

    subgraph DIETITIAN["Luồng Chuyên gia"]
        DDash --> DReviews["/dietitian/reviews<br/>hàng chờ duyệt (pending_review)"]
        DReviews --> DDetail["Xem chi tiết plan<br/>nguồn + cảnh báo P0/P1/P2"]
        DDetail --> DReplace["Thay thế món<br/>replacement-candidates"]
        DDetail -->|Approve| DApprove["status → approved"]
        DDetail -->|Reject + lý do| DReject["status → rejected"]
        DDash --> DPatients["/dietitian/patients<br/>danh sách bệnh nhân"]
        DDash --> DAnalytics["/dietitian/analytics<br/>dashboard tổng hợp"]
    end

    DApprove -.->|thực đơn mới xuất hiện| PWeekly

    style DApprove fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    style PWait fill:#f5f5f5,stroke:#9e9e9e,stroke-dasharray: 5 5
```

## 7. Deployment Topology

Một service Render duy nhất phục vụ cả API lẫn Agent (không có worker service riêng — khớp với mục 2). Cold start free tier ~50s, cần "warm up" trước demo.

```mermaid
graph TB
    GH["GitHub Actions<br/>ruff · mypy · pytest · docker build"] -->|push main| Render
    GH -->|push main| Vercel

    subgraph Render["Render — Web Service (1 container)"]
        R1["FastAPI + Uvicorn<br/>+ LangGraph agent (in-process)"]
    end
    subgraph Vercel["Vercel"]
        V1["web-next (Next.js)"]
    end

    DB[("Neon / Supabase<br/>Postgres + pgvector<br/>Supabase: chỉ Postgres thuần, không RLS/Auth (ADR-008)")]
    LS["LangSmith (tuỳ chọn)"]

    V1 -->|NEXT_PUBLIC_API_URL| R1
    R1 --> DB
    R1 -.-> LS
```
