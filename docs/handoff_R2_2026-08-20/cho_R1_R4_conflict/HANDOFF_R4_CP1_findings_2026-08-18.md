# Bàn giao R4 — 2 phát hiện + fix đã kiểm chứng (CP1), tối 18/08

> Tìm ra khi R2 audit CP1 bằng Playwright thật. Đã sửa xong, đã test/build/xác nhận UI thật — nhưng đây là file thuộc `src/api/**`/`web-next/src/**` (phạm vi R4), nên **hoàn tác lại**, chỉ để lại ghi chú này. R4 tự quyết định áp dụng lại theo cách nào.

---

## 1. `C1-BE-01` — Lỗ hổng đăng ký công khai thành `dietitian`

**File:** `src/api/routes/auth.py:35`

**Vấn đề:** `RegisterRequest.role = Field(pattern="^(patient|dietitian)$")` — bất kỳ ai gọi `POST /auth/register` cũng tự tạo được tài khoản `dietitian`, vi phạm RULE-3.

**Fix đã kiểm chứng an toàn:**
```python
role: str = Field(pattern="^patient$")
```

**Đã xác nhận trước khi sửa:**
- `scripts/seed_demo_users.py` tạo tài khoản dietitian demo **thẳng qua DB** (không qua endpoint này) — không phụ thuộc.
- Không có route "mời chuyên gia" nào khác đang dùng endpoint này.
- Không test nào đăng ký `dietitian` qua endpoint public (trước khi sửa).

**Test đã thêm** (`tests/test_api_auth.py`):
```python
def test_dang_ky_cong_khai_voi_role_dietitian_bi_tu_choi(client):
    """CP1: đăng ký công khai chỉ tạo được patient — dietitian phải qua cơ chế mời/admin cấp (C1-BE-01)."""
    r = _register(client, role="dietitian")
    assert r.status_code == 422
```
11/11 test `test_api_auth.py` pass sau khi sửa.

**⚠️ Hệ quả dây chuyền phải xử lý cùng lúc:** helper `_register_and_login(client, email, role)` bị lặp lại gần giống hệt nhau ở **10 file test** (`test_api_reviews.py`, `test_api_meal_plans.py`, `test_api_food_logs.py`, `test_api_pantry_equivalent.py`, `test_api_menu_explainer.py`, `test_api_patients.py`, `test_api_patient_workspace.py`, `test_api_target_assistant.py`, `test_api_targets.py`, `test_api_chat_auth.py`) — tất cả gọi `_register_and_login(client, ..., "dietitian")` qua endpoint public, sẽ vỡ ngay khi khoá lỗ hổng này.

Cách sửa đã thử và chạy được (không đổi signature fixture nào, không cần thread `db_session` qua nhiều lớp) — thêm vào `tests/conftest.py`:

```python
def _create_user_directly(client, email: str, role: str, password: str = "matkhau123") -> str:
    """Tạo user thẳng qua DB session của `client` — dùng cho role khác `patient`.
    /auth/register công khai chỉ còn nhận role=patient (C1-BE-01)."""
    from src.api.security import hash_password
    from src.db.base import get_db
    from src.db.models import User

    db = next(client.app.dependency_overrides[get_db]())
    user = User(email=email, password_hash=hash_password(password), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user.id
```

Rồi ở mỗi file, import `from conftest import _create_user_directly` và sửa `_register_and_login` thành nhánh `if role == "patient": ... else: user_id = _create_user_directly(...)`. Đã áp dụng thử và chạy xanh trên `test_api_reviews.py` (15 passed) trước khi hoàn tác.

---

## 2. Badge P0/P1/P2 chưa hiện trên hàng chờ duyệt

**File:** `web-next/src/app/dietitian/reviews/page.tsx`

**Vấn đề xác nhận bằng code + Playwright:** `plan.highest_risk` (backend đã trả sẵn trong `MealPlanOut`) chỉ được dùng để **lọc/sắp xếp nội bộ** (dòng 62-69, criterion `'blocking'`), **không có JSX nào render nó thành badge** ở danh sách hàng chờ. Trang chi tiết (`reviews/[id]/page.tsx`) đã hiển thị đầy đủ — chỉ thiếu ở trang danh sách.

**Fix đã kiểm chứng bằng Playwright thật** (tạo 1 kế hoạch `pending_review` thật, chụp màn hình, thấy badge `P1` hiện đúng cạnh badge trạng thái, không có console error):

Trong `reviews/page.tsx`, thêm:
```tsx
const RISK_LABEL: Record<string, string> = { P0: 'Chặn phát hành', P1: 'Cần chuyên gia xác nhận', P2: 'Thông tin tham khảo', none: 'Không có ngoại lệ' }
```

Trong vòng lặp render mỗi dòng (sau khi có `const status = ...`):
```tsx
// Luôn render 1 span (kể cả rỗng khi 'none') — .audit-row là CSS grid cột cố định,
// trả về null sẽ làm các cột sau bị lệch hàng so với dòng khác.
const hasRisk = plan.highest_risk !== 'none'
const risk = <span className={hasRisk ? `badge ${plan.highest_risk === 'P0' ? 'badge-hard' : 'badge-soft'}` : ''} title={hasRisk ? RISK_LABEL[plan.highest_risk] : undefined}>{hasRisk ? plan.highest_risk : ''}</span>
```
Rồi chèn `{risk}` vào ngay sau `{status}` ở cả 2 nhánh render (`filter === 'pending'` và nhánh còn lại).

**CSS cần sửa cùng lúc** (`web-next/src/app/globals.css`), vì `.audit-row` là CSS grid cột cố định (thêm 1 cột `44px` cho badge mới):
```css
.audit-row { display:grid; grid-template-columns:110px 44px minmax(180px,1fr) minmax(150px,.8fr) 120px auto; ... }
.audit-row-selectable { grid-template-columns:28px 110px 44px minmax(180px,1fr) minmax(150px,.8fr) 120px auto; }
```
Và trong media query `@media(max-width:1050px)`, `.audit-row-selectable .audit-check` đổi `grid-row:1/6` → `grid-row:1/7` (6 phần tử xếp dọc thay vì 5, vì thêm 1 dòng risk badge).

**Đã build sạch:** `npx tsc --noEmit` không lỗi trước khi hoàn tác.

---

## 3. Nút nổi trợ lý — KHÔNG có bug, đã xác nhận bằng Playwright

Không cần sửa gì. Đo bounding box thật ở landing/login/dietitian, 1280px và 1440px: nút luôn nằm gọn trong viewport (`right_edge` khớp chính xác viewport width). CP1 có thể tick mục này là đạt mà không cần code nào thay đổi.

---

## Trạng thái sau khi R2 hoàn tác tối 18/08

Toàn bộ 10 file trên (`auth.py`, `test_api_auth.py`, `reviews/page.tsx`, `globals.css`, `conftest.py` + 5 file test đã sửa dở) đã `git restore` về đúng HEAD, không còn thay đổi nào trong working tree. R4 tự quyết định áp dụng lại fix theo cách này hay cách khác.
