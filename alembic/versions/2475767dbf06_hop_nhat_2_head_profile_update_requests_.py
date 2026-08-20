"""Hợp nhất 2 head: profile_update_requests (đội) + verified_by sang Text.

Hai nhánh phát sinh song song và cùng nối vào `1778fd77cbec`:

* `c41a7d92e610` — bảng `profile_update_requests` (bệnh nhân xin sửa hồ sơ,
  chuyên gia duyệt), do đồng đội làm trên repo dự án.
* `a2f7c4e91d63` — nới `verified_by` từ varchar(100) sang Text để không cắt
  mất chữ ký duyệt dài.

Không có DDL nào ở đây — merge point thuần, chỉ để chuỗi migration về lại một
head duy nhất.

⚠️ Ghi chú vận hành (từ `docs/DATABASE_AUDIT_2026-08-15.md`): revision
`c41a7d92e610` đã được chạy lên Supabase dùng chung TRƯỚC khi về repo này —
lúc rà soát ngày 15/08, `alembic_version` trên DB là `c41a7d92e610` trong khi
mã đó không tồn tại trong `alembic/versions/`. Nay nó đã về, nên phần "revision
lạ" của báo cáo coi như đã giải thích xong. Vẫn còn phần chưa xử lý: DB thiếu
`clinical_rules.risk_level`/`.evidence_level` và 3 index của Đợt A.

Revision ID: 2475767dbf06
Revises: a2f7c4e91d63, c41a7d92e610
"""

from collections.abc import Sequence

revision: str = "2475767dbf06"
down_revision: str | Sequence[str] | None = ("a2f7c4e91d63", "c41a7d92e610")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Merge point — không có thay đổi schema."""


def downgrade() -> None:
    """Merge point — không có thay đổi schema."""
