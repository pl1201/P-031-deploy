"""Trung tâm thông báo — một chiều hệ thống → người dùng.

LLM: NO. Chỉ đọc/ghi các bản ghi `Notification` đã được các route khác (reviews,
meal_plans) tạo sẵn — không tự sinh nội dung, không tính lại giá trị lâm sàng nào.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.security import CurrentUser, get_current_user
from src.db.base import get_db
from src.db.models import Notification

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationOut(BaseModel):
    id: str
    type: str
    severity: str
    title: str
    body: str
    related_meal_plan_id: str | None
    read_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UnreadCountOut(BaseModel):
    unread: int


@router.get("", response_model=list[NotificationOut])
def list_notifications(
    limit: int = Query(default=50, ge=1, le=200),
    unread_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[Notification]:
    query = db.query(Notification).filter(Notification.user_id == user.id)
    if unread_only:
        query = query.filter(Notification.read_at.is_(None))
    return query.order_by(Notification.created_at.desc()).limit(limit).all()


@router.get("/unread-count", response_model=UnreadCountOut)
def unread_count(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> UnreadCountOut:
    count = db.query(Notification).filter(Notification.user_id == user.id, Notification.read_at.is_(None)).count()
    return UnreadCountOut(unread=count)


def _get_owned_notification(db: Session, notification_id: str, user: CurrentUser) -> Notification:
    notification = (
        db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == user.id).first()
    )
    if notification is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy thông báo")
    return notification


@router.patch("/{notification_id}/read", response_model=NotificationOut)
def mark_notification_read(
    notification_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Notification:
    notification = _get_owned_notification(db, notification_id, user)
    if notification.read_at is None:
        notification.read_at = datetime.utcnow()
        db.commit()
        db.refresh(notification)
    return notification


@router.patch("/read-all", response_model=UnreadCountOut)
def mark_all_read(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> UnreadCountOut:
    now = datetime.utcnow()
    db.query(Notification).filter(Notification.user_id == user.id, Notification.read_at.is_(None)).update(
        {"read_at": now}
    )
    db.commit()
    return UnreadCountOut(unread=0)
