"""Đợt C: organizations, organization_members, plan_assignments, plan_approvals, care_status.

Sáu quyết định kiến trúc ở `PRODUCTION_READINESS_MASTER_PLAN.md` §5 đã được R2
chốt "theo các mục đã đề xuất" — điều kiện mà `docs/DB_UPGRADE_PLAN_FOR_WEB.md`
đặt ra trước khi được thêm nhóm bảng này.

Toàn bộ là THÊM MỚI, không đụng bảng cũ. `patient_profiles.organization_id`
nullable vì 2.021 hồ sơ đã có trên DB dùng chung trước khi có bảng
`organizations` — gán bừa tổ chức cho chúng là bịa dữ liệu.

Revision ID: 5103d1c0e654
Revises: 9441cd2da1b1
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "5103d1c0e654"
down_revision: str | Sequence[str] | None = "9441cd2da1b1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_organizations_code", "organizations", ["code"], unique=True)

    op.create_table(
        "organization_members",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        # Một người một vai trò trong một tổ chức — không thì hai dòng mâu thuẫn
        # cùng tồn tại và "người này được làm gì" không có câu trả lời xác định.
        sa.UniqueConstraint("organization_id", "user_id", name="uq_org_member"),
    )
    op.create_index("ix_org_members_user", "organization_members", ["user_id"])

    op.create_table(
        "plan_assignments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("profile_id", sa.String(length=36), nullable=False),
        sa.Column("dietitian_id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=True),
        sa.Column("assigned_by", sa.String(length=36), nullable=True),
        sa.Column("assigned_at", sa.DateTime(), nullable=False),
        # `revoked_at` thay vì xoá dòng: ai TỪNG phụ trách hồ sơ là thông tin
        # cần cho truy vết.
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["profile_id"], ["patient_profiles.id"]),
        sa.ForeignKeyConstraint(["dietitian_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["assigned_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_plan_assignments_profile", "plan_assignments", ["profile_id", "revoked_at"])
    op.create_index("ix_plan_assignments_dietitian", "plan_assignments", ["dietitian_id", "revoked_at"])

    op.create_table(
        "plan_approvals",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("meal_plan_id", sa.String(length=36), nullable=False),
        sa.Column("profile_id", sa.String(length=36), nullable=False),
        sa.Column("approved_by", sa.String(length=36), nullable=False),
        sa.Column("approved_at", sa.DateTime(), nullable=False),
        sa.Column("menu_version", sa.Integer(), nullable=False),
        sa.Column("menu_hash", sa.String(length=64), nullable=True),
        sa.Column("nutrition_hash", sa.String(length=64), nullable=True),
        sa.Column("solver_seed", sa.Integer(), nullable=True),
        # Bản đóng băng nội dung đã ký. Cố ý KHÔNG trỏ sang `meal_plan_items`:
        # món có thể bị sửa sau đó, mà artifact trỏ sang dữ liệu đổi được thì
        # không còn là artifact.
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["meal_plan_id"], ["meal_plans.id"]),
        sa.ForeignKeyConstraint(["profile_id"], ["patient_profiles.id"]),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        # Mỗi phiên bản thực đơn chỉ được ký MỘT lần — ký lại cùng version nghĩa
        # là có hai artifact cùng nhận là bản đã duyệt.
        sa.UniqueConstraint("meal_plan_id", "menu_version", name="uq_plan_approval_version"),
    )
    op.create_index("ix_plan_approvals_plan", "plan_approvals", ["meal_plan_id", "approved_at"])

    op.create_table(
        "care_status",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("profile_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("changed_by", sa.String(length=36), nullable=True),
        sa.Column("changed_at", sa.DateTime(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["profile_id"], ["patient_profiles.id"]),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_care_status_profile_changed", "care_status", ["profile_id", "changed_at"])

    with op.batch_alter_table("patient_profiles") as batch:
        batch.add_column(sa.Column("organization_id", sa.String(length=36), nullable=True))
        batch.create_foreign_key(
            "fk_patient_profiles_organization", "organizations", ["organization_id"], ["id"]
        )


def downgrade() -> None:
    with op.batch_alter_table("patient_profiles") as batch:
        batch.drop_constraint("fk_patient_profiles_organization", type_="foreignkey")
        batch.drop_column("organization_id")

    op.drop_index("ix_care_status_profile_changed", table_name="care_status")
    op.drop_table("care_status")
    op.drop_index("ix_plan_approvals_plan", table_name="plan_approvals")
    op.drop_table("plan_approvals")
    op.drop_index("ix_plan_assignments_dietitian", table_name="plan_assignments")
    op.drop_index("ix_plan_assignments_profile", table_name="plan_assignments")
    op.drop_table("plan_assignments")
    op.drop_index("ix_org_members_user", table_name="organization_members")
    op.drop_table("organization_members")
    op.drop_index("ix_organizations_code", table_name="organizations")
    op.drop_table("organizations")
