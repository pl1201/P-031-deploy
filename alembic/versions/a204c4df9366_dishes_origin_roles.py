"""dishes: thêm cột `origin` + `roles` (vai trò trong cấu trúc bữa).

Revision ID: a204c4df9366
Revises: 5bbf9aaefecc

`origin` (`vn`/`foreign`) biến ranh giới "món Việt curated vs khối tham chiếu
USDA FNDDS" từ quy ước TIỀN TỐ dish_id (`FNDDS-`) thành dữ liệu tra vấn được
bằng SQL. Tầng C trong `src/clinical/tiers.py` vẫn giữ nguyên làm lưới an toàn
cho dòng cũ — cột này bổ sung, không thay thế.

`roles` là danh sách vai trò phân tách bằng `|` (từ vựng ở
`src/clinical/dish_roles.py`): `staple`, `protein`, `vegetable`, `soup`,
`beverage`, `dessert`, `one_dish`, `condiment`. RỖNG = món không đủ điều kiện
làm một mục độc lập trong bữa (fail closed) — đúng cho cả 2632 dòng
`origin=foreign` và cho nguyên liệu bị nhập lẫn thành "món" (bánh đa nem).

Cả hai cột đều `nullable=True`: dữ liệu cũ trong DB production chưa có giá
trị, và rỗng đã có nghĩa an toàn sẵn (fail closed) nên không cần backfill
bắt buộc để schema hợp lệ.

LƯU Ý VẬN HÀNH (giống 5bbf9aaefecc): `alembic_version` trên DB Supabase dùng
chung đang stamp ở `f85d0e3b2c41`, revision không có trong `alembic/versions/`
của nhánh này — lịch sử migration cục bộ và DB thật đã lệch TỪ TRƯỚC. Vì vậy
2 cột này được thêm bằng ALTER TABLE trực tiếp (2026-08-12), KHÔNG qua
`alembic upgrade`. File này để DB tạo mới từ đầu có đúng schema và làm tài
liệu cho lần stamp lại. Linh (owner E3/DB) cần đối chiếu trước khi chạy
`alembic stamp`/`upgrade` thật trên DB chung.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a204c4df9366"
down_revision: str | Sequence[str] | None = "5bbf9aaefecc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("dishes", sa.Column("origin", sa.String(length=10), nullable=True))
    op.add_column("dishes", sa.Column("roles", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("dishes", "roles")
    op.drop_column("dishes", "origin")
