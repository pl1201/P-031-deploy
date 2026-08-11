#!/usr/bin/env python3
"""Nạp 4 dataset bệnh nhân tổng hợp `data/patients/*.csv` vào DB thật (BE-10 nối dài).

LLM: NO — thuần ETL.

⚠️ DEC-019 (2026-08-09, xem `DEVLOG.md` §3): Hưng (R2) xác nhận trực tiếp cho
phép nạp cả 4 dataset dù license/de-identification của set2/set3/set4 CHƯA
xác minh xong (`manifest.yaml` vẫn ghi `status=quarantined`, chỉ đổi
`enabled=true`). Không tự ý mở rộng quyết định này sang việc khác.

Mỗi hồ sơ tạo kèm 1 `User` giả: email `synthetic+<patient_id>@vnutricare.local`,
password ngẫu nhiên KHÔNG dùng để đăng nhập — lọc được rõ khỏi user thật bằng
prefix `synthetic+`. Idempotent theo email (không seed trùng khi chạy lại).

Mapping cố ý (không suy đoán số mới, chỉ chuyển đổi có kiểm soát):
- activity_level: CSV dùng nhãn tần suất vận động NHANES (sedentary/
  lightly_active/moderately_active) — schema DB dùng "loại lao động" cho hệ
  số PAL (light/moderate/heavy/very_heavy). Map tuyến tính theo DEC-019
  (không dùng very_heavy — CSV không có nhãn tương ứng).
- set4 (`t2dm_vn_adapted_set4_108patients.csv`): schema nghiên cứu Thái Lan
  riêng, glucose/A1c ở mmol/L (khác mg_dl của set1/3) — quy đổi glucose
  ×18.0182 sang mg/dL, A1c giữ nguyên (đã là %). Lọc CHỈ `type.diabetes ==
  "type 2"` (103/108 dòng) — 5 dòng type 1 không thuộc phạm vi dự án.
- `medications` của set2/set4 là NHÃN NHÓM THUỐC (oral_antidiabetic, insulin),
  KHÔNG phải tên thuốc cụ thể — lưu nguyên trạng, không tự suy diễn tên thuốc
  thật (RULE-2/DEC-008). Sẽ KHÔNG khớp được với `drug_food_interactions.csv`.
- `dislikes`/`weight_goal` trong CSV không có cột DB tương ứng — bỏ qua.

Chạy: python scripts/load_patient_datasets.py [--database-url sqlite:///scratch_patients.db]
"""

from __future__ import annotations

import argparse
import csv
import secrets
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from src.api.security import hash_password  # noqa: E402
from src.db.base import Base  # noqa: E402
from src.db.models import PatientMedication, PatientProfile, User  # noqa: E402

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "patients"

MMOL_L_TO_MG_DL_GLUCOSE = 18.0182

# DEC-019: 2 khái niệm khác nhau (tần suất vận động NHANES vs loại lao động
# PAL của dự án) — map tuyến tính theo thứ tự tăng dần, KHÔNG có very_heavy.
_ACTIVITY_MAP: dict[str, str] = {
    "sedentary": "light",
    "lightly_active": "moderate",
    "moderately_active": "heavy",
}


def _synthetic_email(patient_id: str) -> str:
    return f"synthetic+{patient_id}@vnutricare.local"


def _medications_list(raw: str | None) -> list[str]:
    return [s.strip() for s in (raw or "").split(";") if s.strip()]


def _opt_float(raw: str | None) -> float | None:
    raw = (raw or "").strip()
    try:
        return float(raw) if raw else None
    except ValueError:
        return None


# argon2 cố ý chậm (~100-300ms/lần) — với ~2000 hồ sơ, hash riêng từng user sẽ
# tốn nhiều phút và làm transaction bị Supabase Session Pooler đóng kết nối
# giữa chừng (đã gặp bug tương tự ở seed_db.py). Các tài khoản này KHÔNG BAO
# GIỜ được dùng để đăng nhập (chỉ tồn tại vì patient_profiles bắt buộc có
# user_id) — dùng CHUNG một password ngẫu nhiên đã hash 1 lần là an toàn,
# vì plaintext không được lưu lại/tiết lộ ở đâu.
_SYNTHETIC_PASSWORD_HASH = hash_password(secrets.token_urlsafe(32))


def _upsert_patient(
    session: Session,
    *,
    patient_id: str,
    existing_users: dict[str, User],
    existing_profiles: dict[str, PatientProfile],
    age: int,
    sex: str,
    height_cm: float,
    weight_kg: float,
    activity_level: str,
    region: str | None,
    conditions: list[dict],
    lab_values: dict[str, float | None],
    medications: list[str],
) -> None:
    email = _synthetic_email(patient_id)
    user = existing_users.get(email)
    if user is None:
        user = User(email=email, password_hash=_SYNTHETIC_PASSWORD_HASH, role="patient")
        session.add(user)
        session.flush()
        existing_users[email] = user

    profile = existing_profiles.get(user.id)
    is_new_profile = profile is None
    if profile is None:
        profile = PatientProfile(user_id=user.id)
        session.add(profile)

    profile.age = age
    profile.sex = sex
    profile.height_cm = height_cm
    profile.weight_kg = weight_kg
    profile.activity_level = activity_level
    profile.region = region
    profile.conditions = conditions
    profile.lab_values = {k: v for k, v in lab_values.items() if v is not None}

    if is_new_profile:
        session.flush()  # cần profile.id (sinh phía server khi INSERT) trước khi ghi PatientMedication
        existing_profiles[user.id] = profile

    session.query(PatientMedication).filter(PatientMedication.profile_id == profile.id).delete()
    for drug_name in medications:
        session.add(PatientMedication(profile_id=profile.id, drug_name=drug_name))


def _load_existing_users(session: Session) -> dict[str, User]:
    """Nạp trước toàn bộ user `synthetic+*` vào bộ nhớ — tránh 1 SELECT/dòng
    qua mạng (nguồn nghẽn thật trên Supabase Session Pooler, cùng loại bug đã
    gặp ở `seed_db.py`)."""
    return {u.email: u for u in session.query(User).filter(User.email.like("synthetic+%")).all()}


def _load_existing_profiles(session: Session, existing_users: dict[str, User]) -> dict[str, PatientProfile]:
    user_ids = [u.id for u in existing_users.values()]
    if not user_ids:
        return {}
    rows = session.query(PatientProfile).filter(PatientProfile.user_id.in_(user_ids)).all()
    return {p.user_id: p for p in rows}


def load_set123(
    session: Session,
    filename: str,
    glucose_key: str | None,
    existing_users: dict[str, User],
    existing_profiles: dict[str, PatientProfile],
    commit_every: int = 200,
) -> int:
    """set1/set2/set3 — schema chuẩn hoá giống nhau (T2DM-only, region đã khớp enum)."""
    n = 0
    with open(DATA_DIR / filename, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            lab_values = {
                "hba1c_pct": _opt_float(row.get("hba1c_pct")),
                "sbp_mmhg": _opt_float(row.get("sbp_mmhg")),
                "dbp_mmhg": _opt_float(row.get("dbp_mmhg")),
                "dm_duration_years": _opt_float(row.get("dm_duration_years")),
            }
            if glucose_key:
                lab_values["glucose_fasting_mg_dl"] = _opt_float(row.get(glucose_key))

            _upsert_patient(
                session,
                patient_id=row["patient_id"],
                existing_users=existing_users,
                existing_profiles=existing_profiles,
                age=int(row["age"]),
                sex=row["sex"],
                height_cm=float(row["height_cm"]),
                weight_kg=float(row["weight_kg"]),
                activity_level=_ACTIVITY_MAP[row["activity_level"]],
                region=row.get("region") or None,
                conditions=[{"code": "T2DM"}],
                lab_values=lab_values,
                medications=_medications_list(row.get("medications")),
            )
            n += 1
            if n % commit_every == 0:
                session.commit()
                print(f"  ... {n} dòng")
    return n


def load_set4(
    session: Session,
    existing_users: dict[str, User],
    existing_profiles: dict[str, PatientProfile],
    commit_every: int = 200,
) -> int:
    """set4 — schema nghiên cứu Thái Lan riêng. Lọc type 2, quy đổi mmol/L→mg/dL."""
    n = 0
    with open(DATA_DIR / "t2dm_vn_adapted_set4_108patients.csv", newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row.get("type.diabetes", "").strip() != "type 2":
                continue

            conditions = [{"code": "T2DM"}]
            if (row.get("hypertension") or "").strip().lower() == "yes":
                conditions.append({"code": "HTN"})

            glucose_mmol = _opt_float(row.get("fastingglucose"))
            lab_values = {
                "hba1c_pct": _opt_float(row.get("A1c")),
                "sbp_mmhg": _opt_float(row.get("Systolic.blood.pressure")),
                "dbp_mmhg": _opt_float(row.get("diastolic.blood.pressure")),
                "glucose_fasting_mg_dl": (glucose_mmol * MMOL_L_TO_MG_DL_GLUCOSE if glucose_mmol is not None else None),
                "total_cholesterol_mmol_l": _opt_float(row.get("total.Cholesterol")),
            }

            medications = _medications_list(row.get("current.treatment.medication"))
            _upsert_patient(
                session,
                patient_id=f"set4_{row['ordernumber']}",
                existing_users=existing_users,
                existing_profiles=existing_profiles,
                age=int(row["age"]),
                sex=row["sex"],
                height_cm=float(row["heigh"]),
                weight_kg=float(row["weight"]),
                activity_level="light",  # DEC-019: cột nguồn là bool "đủ vận động", không đủ chi tiết để map 4 mức
                region=None,  # set4 không có cột region
                conditions=conditions,
                lab_values=lab_values,
                medications=medications,
            )
            n += 1
            if n % commit_every == 0:
                session.commit()
    return n


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", default="sqlite:///scratch_patients.db")
    args = parser.parse_args()

    engine = create_engine(args.database_url, pool_pre_ping=True)
    Base.metadata.create_all(engine)

    with Session(engine, expire_on_commit=False) as session:
        existing_users = _load_existing_users(session)
        existing_profiles = _load_existing_profiles(session, existing_users)

        n1 = load_set123(
            session, "t2dm_vn_adapted_set1_840patients.csv", "glucose_fasting_mg_dl", existing_users, existing_profiles
        )
        session.commit()
        print(f"set1: {n1} hồ sơ")

        n2 = load_set123(session, "t2dm_vn_adapted_set2_700patients.csv", None, existing_users, existing_profiles)
        session.commit()
        print(f"set2: {n2} hồ sơ")

        n3 = load_set123(
            session, "t2dm_vn_adapted_set3_372patients.csv", "glucose_fasting_mg_dl", existing_users, existing_profiles
        )
        session.commit()
        print(f"set3: {n3} hồ sơ")

        n4 = load_set4(session, existing_users, existing_profiles)
        session.commit()
        print(f"set4: {n4} hồ sơ (đã lọc type 2, loại 5 dòng type 1)")

        print(f"Tổng: {n1 + n2 + n3 + n4} hồ sơ")


if __name__ == "__main__":
    main()
