"""Gộp toàn bộ router theo resource thành 1 `router` duy nhất để `main.py` include."""

from __future__ import annotations

from fastapi import APIRouter

from src.api.routes import auth, meal_plans, misc, patient_workspace, patients, reviews, targets

router = APIRouter()
router.include_router(misc.router)
router.include_router(auth.router)
router.include_router(patients.router)
router.include_router(patient_workspace.router)
router.include_router(targets.router)
router.include_router(meal_plans.router)
router.include_router(reviews.router)
