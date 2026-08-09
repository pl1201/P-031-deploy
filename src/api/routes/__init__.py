"""Gộp toàn bộ router theo resource thành 1 `router` duy nhất để `main.py` include."""

from __future__ import annotations

from fastapi import APIRouter

from src.api.routes import auth, equivalent, food_logs, meal_plans, misc, pantry, patients, reviews, targets

router = APIRouter()
router.include_router(misc.router)
router.include_router(auth.router)
router.include_router(patients.router)
router.include_router(targets.router)
router.include_router(meal_plans.router)
router.include_router(reviews.router)
router.include_router(food_logs.router)
router.include_router(pantry.router)
router.include_router(equivalent.router)
