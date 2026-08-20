"""Merge ui-main (notifications/preferences/onboarding) with the unmerged
feature/CLN-rule-risk-level-qd5481 chain that was already applied to the
shared Supabase dev database (organizations/plan_approvals/thai_bo_pct...).

Điểm rẽ nhánh chung là `c41a7d92e610`. Không có va chạm tên bảng/cột giữa 2
nhánh (đã kiểm tra trước khi tạo file này) — file này chỉ nối lịch sử, không
đổi schema. `src/db/models.py` của `ui-main` không định nghĩa các bảng riêng
của nhánh kia (organizations, plan_approvals...) — chúng tồn tại vật lý trên
DB chung nhưng ORM ở nhánh này không đụng tới, không gây lỗi.

Revision ID: 5f1ccfaeb53b
Revises: 53f37213ed57, c8f31d75a204
"""

from collections.abc import Sequence

revision: str = "5f1ccfaeb53b"
down_revision: str | Sequence[str] | None = ("53f37213ed57", "c8f31d75a204")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
