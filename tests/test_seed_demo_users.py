"""BE-05: seed 2 chuyên gia + 6 bệnh nhân mô phỏng — idempotent, SQLite tạm."""

from __future__ import annotations

import importlib

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.db.base import Base
from src.db.models import PatientAllergy, PatientMedication, PatientProfile, User


def _seed_module():
    return importlib.import_module("scripts.seed_demo_users")


def _fresh_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def test_seed_dung_2_chuyen_gia_va_6_benh_nhan():
    seed = _seed_module()
    session = _fresh_session()

    n_dietitians = seed.seed_dietitians(session)
    n_patients = seed.seed_patients(session)
    session.commit()

    assert n_dietitians == 2
    assert n_patients == 6
    assert session.query(User).filter(User.role == "dietitian").count() == 2
    assert session.query(User).filter(User.role == "patient").count() == 6
    assert session.query(PatientProfile).count() == 6


def test_seed_moi_benh_ly_muc_tieu_co_it_nhat_1_benh_nhan():
    """T2DM/HTN/CKD/Gout đều xuất hiện — đúng AC BE-05 'mỗi bệnh lý 1-2 người'."""
    seed = _seed_module()
    session = _fresh_session()
    seed.seed_dietitians(session)
    seed.seed_patients(session)
    session.commit()

    all_codes = {c["code"] for p in session.query(PatientProfile).all() for c in p.conditions}
    assert all_codes == {"T2DM", "HTN", "CKD", "GOUT"}


def test_seed_chay_lai_khong_tao_trung_idempotent():
    seed = _seed_module()
    session = _fresh_session()
    seed.seed_dietitians(session)
    seed.seed_patients(session)
    session.commit()

    n_dietitians_2 = seed.seed_dietitians(session)
    n_patients_2 = seed.seed_patients(session)
    session.commit()

    assert n_dietitians_2 == 0
    assert n_patients_2 == 0
    assert session.query(User).count() == 8
    assert session.query(PatientProfile).count() == 6


def test_moi_benh_nhan_dang_nhap_duoc_bang_mat_khau_demo(client, db_session):
    """Chạy qua đúng route /auth/login thật (không gọi thẳng verify_password)."""
    seed = _seed_module()
    seed.seed_dietitians(db_session)
    seed.seed_patients(db_session)
    db_session.commit()

    for p in seed.PATIENTS:
        r = client.post("/api/v1/auth/login", json={"email": p["email"], "password": seed.DEMO_PASSWORD})
        assert r.status_code == 200, f"{p['email']}: {r.text}"


def test_ho_so_co_du_di_ung_va_thuoc_dung_dinh_dang():
    seed = _seed_module()
    session = _fresh_session()
    seed.seed_dietitians(session)
    seed.seed_patients(session)
    session.commit()

    profile5 = session.query(PatientProfile).join(User).filter(User.email == "patient5@nutricare.demo").first()
    assert profile5 is not None
    allergies = session.query(PatientAllergy).filter(PatientAllergy.profile_id == profile5.id).all()
    medications = session.query(PatientMedication).filter(PatientMedication.profile_id == profile5.id).all()
    assert {a.allergen for a in allergies} == {"đậu nành"}
    assert {m.drug_name for m in medications} == {"metformin", "losartan"}
