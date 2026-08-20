"""Merge 2 head: dishes origin/roles (CLN-11) và workspace-timeline+safety/pantry (main).

Revision ID: 1778fd77cbec
Revises: a204c4df9366, c95f302a587e

Bối cảnh (rà soát DB, 2026-08-13)
---------------------------------
`feature/CLN-11-DAT-21-clinical-data` tách nhánh migration riêng trước khi
`c95f302a587e` (merge workspace-timeline + safety/pantry) được tạo trên
`main`:

- `a204c4df9366` (`dishes_origin_roles`) ← `5bbf9aaefecc`
  (`widen_clinical_rules_flag_columns`) ← `8546da42031c` — chain riêng của
  nhánh này, thêm cột `dishes.origin`/`dishes.roles` và nới độ dài cột
  `clinical_rules.overridden_by`/`disabled_by_flag`/`requires_flag` (50→255
  ký tự).
- `c95f302a587e` — head hiện tại của `main`.

Hai head cùng tồn tại khi merge PR này vào `main` (`alembic heads` trả về 2
kết quả) — CI `tests/test_alembic_graph.py` (thêm sau sự cố `aedef0ff7743`
biến mất nhiều lần) bắt đúng lỗi này trước khi nó lặp lại. Migration này chỉ
hợp nhất đồ thị, KHÔNG đổi schema.

⚠️ Đã đối chiếu Supabase dùng chung (read-only, 2026-08-13): cả 2 thay đổi
schema của nhánh `a204c4df9366` đã tồn tại thật trên DB (`dishes.origin`/
`dishes.roles` có sẵn; `clinical_rules.overridden_by/disabled_by_flag/
requires_flag` đã là `varchar(255)`) — tương tự tình huống `c95f302a587e` mô
tả cho `pantry_items`/`substitution_scopes`. `alembic upgrade head` từ
migration này an toàn (không thao tác schema), nhưng nếu DB đang stamp ở
`c95f302a587e`, `alembic stamp` thẳng lên revision này (không `upgrade`) là
đường phù hợp hơn — theo đúng khuyến nghị đã ghi trong `c95f302a587e`.
"""

from __future__ import annotations

from collections.abc import Sequence

revision: str = "1778fd77cbec"
down_revision: str | Sequence[str] | None = ("a204c4df9366", "c95f302a587e")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Chỉ hợp nhất đồ thị revision — không có thao tác schema nào."""


def downgrade() -> None:
    """Tách lại thành 2 head — không có thao tác schema nào."""
