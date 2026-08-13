"""Merge 2 head: workspace-timeline chain và safety+pantry chain.

Revision ID: c95f302a587e
Revises: 8546da42031c, f85d0e3b2c41

Bối cảnh (sửa `main` đỏ, 2026-08-12)
------------------------------------
`main` có 2 nhánh migration song song chưa bao giờ được hợp nhất:

- `8546da42031c` — chain safety/pantry (`b7c214e93a08` food_logs OOV,
  `f3a1c9d2b7e4` pantry_items+substitution_scopes, các merge trung gian).
- `f85d0e3b2c41` — chain workspace timeline (`f74c9d2a1b30` patient
  workspace/observations, rồi vô hiệu hoá plan còn dùng `MENU-*`).

Hai head cùng tồn tại nên `alembic upgrade head` không chạy được (alembic từ
chối khi có nhiều head). Migration này chỉ hợp nhất đồ thị, KHÔNG đổi schema.

Kèm theo: file `aedef0ff7743_merge_heads_pgvector_meal_plan_items.py` bị MẤT
khỏi `main` (còn tồn tại ở nhánh cũ) trong khi 3 migration
(`b7c214e93a08`, `c41f6a2d9e10`, `f3a1c9d2b7e4`) vẫn khai
`down_revision = "aedef0ff7743"`. Thiếu file đó làm mọi lệnh alembic vỡ ngay
khi dựng revision map (`KeyError: 'aedef0ff7743'`) — kể cả `alembic current`.
File đã được phục hồi trong cùng PR này.

⚠️ CẢNH BÁO VẬN HÀNH cho DB Supabase dùng chung — ĐỌC TRƯỚC KHI CHẠY
--------------------------------------------------------------------
`alembic_version` của DB dùng chung đang ở `f85d0e3b2c41`, tức nhánh
safety/pantry CHƯA từng được alembic áp. NHƯNG các bảng/cột của nhánh đó
(`pantry_items`, `substitution_scopes`, cột OOV của `food_logs`) ĐÃ tồn tại
thật trong DB — vì `scripts/seed_db.py` gọi `Base.metadata.create_all(engine)`,
tạo bảng NGOÀI alembic.

Hệ quả: chạy `alembic upgrade head` trên DB đó sẽ **lỗi** ("already exists")
chứ không phải nâng cấp êm. Đường an toàn là đối chiếu schema thật rồi
`alembic stamp` tới head này, KHÔNG `upgrade`. Việc này thuộc quyền Linh
(owner E3/DB) — xem báo cáo đối chiếu trong PR.
"""

from collections.abc import Sequence

revision: str = "c95f302a587e"
down_revision: str | Sequence[str] | None = ("8546da42031c", "f85d0e3b2c41")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Chỉ hợp nhất đồ thị revision — không có thao tác schema nào."""


def downgrade() -> None:
    """Tách lại thành 2 head — không có thao tác schema nào."""
