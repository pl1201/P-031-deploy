"""P2/AGT-12: khai báo nguyên liệu có sẵn trong tủ lạnh — đầu vào cho thực đơn
tương đương (`src/agents/equivalent.py`).

LLM: NO.

⚠️ Nhập tự do (`free_text_vi`) CHỜ `FoodMatcher` (BE-07, chưa merge vào
`main`) — route này CHỈ nhận `food_id` khớp DB thật, không có cơ chế tự khớp
tên gõ tay sang food_id (RULE-2: không đoán).
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.api.security import CurrentUser, get_current_user
from src.db.base import get_db
from src.db.models import FoodItem as DbFoodItem
from src.db.models import PantryItem
from src.db.models import PatientProfile as DbPatientProfile

router = APIRouter(prefix="/pantry", tags=["pantry"])


class PantryItemIn(BaseModel):
    food_id: int
    qty: float = Field(gt=0)
    unit: str = Field(min_length=1, max_length=20)


class PantryItemOut(BaseModel):
    id: str
    food_id: int | None
    name_vi: str | None
    qty: float
    unit: str
    created_at: datetime

    @classmethod
    def from_model(cls, item: PantryItem) -> PantryItemOut:
        return cls(
            id=item.id,
            food_id=item.food_id,
            name_vi=item.food.name_vi if item.food is not None else None,
            qty=item.qty,
            unit=item.unit,
            created_at=item.created_at,
        )


def _get_owned_profile(db: Session, patient_id: str, user: CurrentUser) -> DbPatientProfile:
    profile = db.get(DbPatientProfile, patient_id)
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hồ sơ bệnh nhân")
    if user.role == "patient" and profile.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hồ sơ bệnh nhân")
    return profile


@router.post("/{patient_id}", response_model=PantryItemOut, status_code=status.HTTP_201_CREATED)
def add_pantry_item(
    patient_id: str,
    payload: PantryItemIn,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> PantryItemOut:
    _get_owned_profile(db, patient_id, user)
    food = db.get(DbFoodItem, payload.food_id)
    if food is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "food_id không có trong CSDL")

    item = PantryItem(profile_id=patient_id, food_id=payload.food_id, qty=payload.qty, unit=payload.unit)
    db.add(item)
    db.commit()
    db.refresh(item)
    return PantryItemOut.from_model(item)


@router.get("/{patient_id}", response_model=list[PantryItemOut])
def list_pantry_items(
    patient_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[PantryItemOut]:
    _get_owned_profile(db, patient_id, user)
    items = (
        db.query(PantryItem).filter(PantryItem.profile_id == patient_id).order_by(PantryItem.created_at.desc()).all()
    )
    return [PantryItemOut.from_model(i) for i in items]


@router.delete("/{patient_id}/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pantry_item(
    patient_id: str,
    item_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> None:
    _get_owned_profile(db, patient_id, user)
    item = db.query(PantryItem).filter(PantryItem.id == item_id, PantryItem.profile_id == patient_id).first()
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy nguyên liệu trong tủ lạnh")
    db.delete(item)
    db.commit()
