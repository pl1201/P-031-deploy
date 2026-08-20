"""Index cho truy vấn nóng của Web/App (Đợt A — docs/DB_UPGRADE_PLAN_FOR_WEB.md).

Revision ID: c4e82b16d0f3
Revises: b3d71a05c9e2

Bối cảnh
--------
Rà truy vấn thật của API cho kế hoạch nâng cấp DB phát hiện hai chỗ lọc bằng cột
KHÔNG có index:

- `meal_plans.status` — hàng chờ chuyên gia (`src/api/routes/reviews.py`) lọc
  đúng bằng cột này, và danh sách phân trang sắp theo `created_at`.
- `meal_plans (profile_id, plan_date)` — kiểm tra trùng thực đơn cùng ngày, chạy
  ở MỌI lần tạo plan (`src/api/routes/meal_plans.py`).
- `food_logs (profile_id, logged_at)` — nhật ký theo ngày và biểu đồ tuân thủ 7
  ngày. Hai index rời sẵn có không phục vụ truy vấn ghép này tốt bằng index ghép.

Trước đó `dishes`/`food_items` chỉ có index trên `name_vi`, tức đang tối ưu cho
tìm-theo-tên trong khi truy vấn thật của sản phẩm là lọc theo trạng thái và
khoảng thời gian.

⚠️ Trung thực về mức lợi: ở quy mô dữ liệu hiện tại (hơn 100 món, vài trăm
meal_plan) các index này CHƯA tạo khác biệt đo được. Chúng được thêm vì rẻ, không
đổi dữ liệu, không đổi contract API, và vì chi phí thêm index sau khi bảng đã lớn
cao hơn nhiều. Đừng trích migration này như một cải thiện hiệu năng đã đo.

KHÔNG thêm index cho `dishes` ở đợt này: truy vấn món thay thế lọc theo `region`
trên một bảng ~108 dòng, index không giúp gì. Vấn đề thật của truy vấn đó là
THIẾU BỘ LỌC AN TOÀN, đã sửa riêng ở cùng PR.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "c4e82b16d0f3"
down_revision: str | Sequence[str] | None = "b3d71a05c9e2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_meal_plans_status_created", "meal_plans", ["status", "created_at"])
    op.create_index("ix_meal_plans_profile_plan_date", "meal_plans", ["profile_id", "plan_date"])
    op.create_index("ix_food_logs_profile_logged", "food_logs", ["profile_id", "logged_at"])


def downgrade() -> None:
    op.drop_index("ix_food_logs_profile_logged", table_name="food_logs")
    op.drop_index("ix_meal_plans_profile_plan_date", table_name="meal_plans")
    op.drop_index("ix_meal_plans_status_created", table_name="meal_plans")
