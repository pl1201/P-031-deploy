#!/usr/bin/env python3
"""BE-05: seed 2 chuyên gia (dietitian) + 6 bệnh nhân mô phỏng vào DB thật.

LLM: NO. Toàn bộ nhân trắc/bệnh lý là số liệu mô phỏng tự đặt để demo luồng
API — KHÔNG phải bệnh nhân thật (đúng RULE an toàn dữ liệu của CLAUDE.md §3).

Idempotent: kiểm tra `User.email` đã tồn tại trước khi tạo — chạy lại nhiều
lần không tạo trùng tài khoản.

Chạy: python scripts/seed_demo_users.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy.orm import Session

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # cho phép chạy trực tiếp `python scripts/seed_demo_users.py`

from src.api.security import hash_password  # noqa: E402
from src.db.base import Base, get_engine, get_session_factory  # noqa: E402
from src.db.models import PatientAllergy, PatientMedication, PatientProfile, User  # noqa: E402

DEMO_PASSWORD = "Demo1234"  # tài khoản demo, ghi rõ trong README — không dùng cho tài khoản thật

DIETITIANS = [
    {"email": "dietitian1@nutricare.demo", "full_name": "BS. Trần Thị Mai (demo)"},
    {"email": "dietitian2@nutricare.demo", "full_name": "BS. Nguyễn Văn Hải (demo)"},
]

# Mỗi bệnh lý mục tiêu (T2DM/HTN/CKD/Gout) có ít nhất 1 người, kèm 1 ca đa bệnh
# lý (BN-06) để demo được cơ chế hoà giải xung đột DEC-007.
PATIENTS = [
    {
        "email": "patient1@nutricare.demo",
        "age": 58,
        "sex": "male",
        "height_cm": 165,
        "weight_kg": 68,
        "activity_level": "light",
        "conditions": [{"code": "T2DM", "stage": None}],
        "lab_values": {"HbA1c": 7.8},
        "allergies": [],
        "medications": ["metformin"],
        "region": "north",
    },
    {
        "email": "patient2@nutricare.demo",
        "age": 63,
        "sex": "female",
        "height_cm": 155,
        "weight_kg": 60,
        "activity_level": "light",
        "conditions": [{"code": "HTN", "stage": None}],
        "lab_values": {},
        "allergies": ["hải sản"],
        "medications": ["amlodipine"],
        "region": "central",
    },
    {
        "email": "patient3@nutricare.demo",
        "age": 70,
        "sex": "male",
        "height_cm": 168,
        "weight_kg": 62,
        "activity_level": "light",
        "conditions": [{"code": "CKD", "stage": "G3b"}],
        "lab_values": {"eGFR": 38},
        "allergies": [],
        "medications": ["furosemide"],
        "region": "south",
    },
    {
        "email": "patient4@nutricare.demo",
        "age": 45,
        "sex": "male",
        "height_cm": 172,
        "weight_kg": 80,
        "activity_level": "moderate",
        "conditions": [{"code": "GOUT", "stage": None}],
        "lab_values": {"uric_acid": 8.2},
        "allergies": [],
        "medications": ["allopurinol"],
        "region": "north",
    },
    {
        "email": "patient5@nutricare.demo",
        "age": 52,
        "sex": "female",
        "height_cm": 160,
        "weight_kg": 65,
        "activity_level": "light",
        "conditions": [{"code": "T2DM", "stage": None}, {"code": "HTN", "stage": None}],
        "lab_values": {"HbA1c": 8.1},
        "allergies": ["đậu nành"],
        "medications": ["metformin", "losartan"],
        "region": "central",
    },
    {
        # Ca đa bệnh lý ĐTĐ2+CKD — đúng ví dụ DEC-007/DEC-014 (chỉ needs_expert_review
        # khi rule thật sự xung đột, không phải mọi ca đồng mắc).
        "email": "patient6@nutricare.demo",
        "age": 58,
        "sex": "male",
        "height_cm": 165,
        "weight_kg": 65,
        "activity_level": "light",
        "conditions": [{"code": "T2DM", "stage": None}, {"code": "CKD", "stage": "G3b"}],
        "lab_values": {"HbA1c": 7.5, "eGFR": 40},
        "allergies": [],
        "medications": ["metformin"],
        "region": "north",
    },
]


def seed_dietitians(session: Session) -> int:
    count = 0
    for d in DIETITIANS:
        existing = session.query(User).filter(User.email == d["email"]).first()
        if existing is not None:
            continue
        session.add(User(email=d["email"], password_hash=hash_password(DEMO_PASSWORD), role="dietitian"))
        count += 1
    return count


def seed_patients(session: Session) -> int:
    count = 0
    for p in PATIENTS:
        user = session.query(User).filter(User.email == p["email"]).first()
        if user is None:
            user = User(email=p["email"], password_hash=hash_password(DEMO_PASSWORD), role="patient")
            session.add(user)
            session.flush()  # cần user.id trước khi tạo profile
        if user.profile is not None:
            continue  # đã có hồ sơ — idempotent, không tạo trùng

        profile = PatientProfile(
            user_id=user.id,
            age=p["age"],
            sex=p["sex"],
            height_cm=p["height_cm"],
            weight_kg=p["weight_kg"],
            activity_level=p["activity_level"],
            conditions=p["conditions"],
            lab_values=p["lab_values"],
            region=p["region"],
        )
        session.add(profile)
        session.flush()
        for allergen in p["allergies"]:
            session.add(PatientAllergy(profile_id=profile.id, allergen=allergen))
        for drug_name in p["medications"]:
            session.add(PatientMedication(profile_id=profile.id, drug_name=drug_name))
        count += 1
    return count


def main() -> int:
    Base.metadata.create_all(get_engine())
    session = get_session_factory()()
    try:
        n_dietitians = seed_dietitians(session)
        n_patients = seed_patients(session)
        session.commit()
    finally:
        session.close()

    print(f"Đã tạo {n_dietitians} chuyên gia mới, {n_patients} bệnh nhân mới (đã có thì bỏ qua).")
    print(f"Mật khẩu demo cho toàn bộ tài khoản: {DEMO_PASSWORD}")
    print("Danh sách:")
    for d in DIETITIANS:
        print(f"  dietitian | {d['email']}")
    for p in PATIENTS:
        codes = "+".join(c["code"] for c in p["conditions"])
        print(f"  patient   | {p['email']} | {codes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
