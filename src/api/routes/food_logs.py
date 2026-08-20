"""BE-07: nhật ký ăn uống + hàng chờ giải quyết món chưa tra được (OOV).

LLM: NO. Route này chỉ dùng matcher tất định (`src/clinical/matching.py`);
Làn B (LLM mapper) là việc riêng, chưa nối vào đây.

Hai điều bất biến của module này
--------------------------------
1. **Không bao giờ bịa số.** Món chưa tra được thì `food_id=NULL`, `grams=NULL`,
   và nó KHÔNG được cộng vào tổng ngày. Tổng ngày trả về kèm `coverage` và
   `verdict` từng chất để client không thể vô tình hiển thị "đạt ngưỡng" khi dữ
   liệu còn khuyết (xem `src/clinical/diary.py`).
2. **Không tin số client gửi.** Khi chuyên gia giải quyết một dòng OOV, gram và
   food_id do họ chọn được dùng để tính LẠI trên server bằng `compute_nutrition`
   — đúng khuôn `approve_review` ở `src/api/routes/reviews.py`.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.api.clinical_bridge import to_clinical_profile
from src.api.security import CurrentUser, get_current_user, guard_free_text, require_role
from src.clinical.diary import LoggedFood, summarize_day
from src.clinical.matching import FoodMatcher
from src.clinical.models import MealSlot
from src.clinical.rules import compute_targets, load_rules
from src.clinical.seeds import load_food_repository
from src.db.base import get_db
from src.db.models import AuditLog, FoodLog
from src.db.models import PatientProfile as DbPatientProfile

router = APIRouter(prefix="/food-logs", tags=["food-logs"])

# Trạng thái khớp — xem docstring cột `match_status` trong src/db/models.py.
MATCH_UNMATCHED = "unmatched"
MATCH_AUTO = "auto"
MATCH_PATIENT_CONFIRMED = "patient_confirmed"
MATCH_EXPERT = "expert"
MATCH_NO_DATA = "no_data"


# --------------------------------------------------------------------------
# Nạp một lần cho cả tiến trình — đọc CSV mỗi request thì mỗi lần ghi nhật ký
# phải parse lại 7.745 dòng.
# --------------------------------------------------------------------------
_repo = None
_matcher: FoodMatcher | None = None


def _get_repo():
    global _repo
    if _repo is None:
        _repo = load_food_repository()
    return _repo


def _get_matcher() -> FoodMatcher:
    global _matcher
    if _matcher is None:
        from src.agents.nodes.core import _la_khoi_usda_bulk

        # Cùng tập ứng viên với sinh thực đơn: bệnh nhân không nên ghi được món
        # mà hệ thống lại không bao giờ kê cho họ.
        _matcher = FoodMatcher([f for f in _get_repo().all() if not _la_khoi_usda_bulk(f)])
    return _matcher


# --------------------------------------------------------------------------
# Schema
# --------------------------------------------------------------------------
class FoodLogCreate(BaseModel):
    profile_id: str
    free_text_vi: str = Field(min_length=1, max_length=255)
    food_id: int | None = None
    grams: float | None = Field(default=None, gt=0, le=5000)
    slot: MealSlot = MealSlot.LUNCH
    logged_at: datetime | None = None
    note_vi: str | None = None


class MatchSuggestion(BaseModel):
    food_id: int
    name_vi: str
    score: float
    matched_on: str


class MatchSuggestionList(BaseModel):
    query: str
    suggestions: list[MatchSuggestion]


class FoodLogOut(BaseModel):
    id: str
    profile_id: str
    logged_at: datetime
    free_text_vi: str | None
    food_id: int | None
    food_name_vi: str | None
    grams: float | None
    slot: str | None
    match_status: str
    match_confidence: float | None
    note_vi: str | None
    # Chỉ có khi chưa khớp chắc — để client hiện danh sách cho người chọn.
    suggestions: list[MatchSuggestion] = Field(default_factory=list)

    @classmethod
    def from_model(cls, log: FoodLog, *, suggestions: list[MatchSuggestion] | None = None) -> FoodLogOut:
        repo = _get_repo()
        food = repo.get(log.food_id) if log.food_id is not None else None
        return cls(
            id=log.id,
            profile_id=log.profile_id,
            logged_at=log.logged_at,
            free_text_vi=log.free_text_vi,
            food_id=log.food_id,
            food_name_vi=food.name_vi if food else None,
            grams=log.grams,
            slot=log.slot,
            match_status=log.match_status,
            match_confidence=log.match_confidence,
            note_vi=log.note_vi,
            suggestions=suggestions or [],
        )


class NutrientVerdictOut(BaseModel):
    nutrient: str
    label_vi: str
    verdict: str
    counted: float | None
    min_value: float | None
    max_value: float | None
    unit: str | None


class ViolationOut(BaseModel):
    nutrient: str
    kind: str
    severity: str
    message_vi: str
    suggestion: str | None = None
    actual: float | None = None
    limit: float | None = None
    unit: str | None = None
    source_ref: str | None = None
    evidence: str | None = None
    food_log_id: str | None = None


class DaySummaryOut(BaseModel):
    """Tổng hợp một ngày.

    `coverage < 1.0` nghĩa là còn món chưa tra được ⇒ mọi con số dưới đây là
    **mức tối thiểu**, và các chất chưa vượt trần mang verdict
    `insufficient_data` chứ KHÔNG phải "đạt".
    """

    profile_id: str
    day: date
    matched_count: int
    unmatched_count: int
    coverage: float
    is_complete: bool
    verdicts: list[NutrientVerdictOut]
    violations: list[ViolationOut]


class ResolveRequest(BaseModel):
    """Chuyên gia giải quyết một dòng OOV.

    `action`:
      * `map_to_existing` — cần `food_id` (+ `grams` nếu dòng chưa có)
      * `mark_no_data`    — thừa nhận không đủ dữ liệu; đây là lựa chọn HỢP LỆ
                            và được khuyến khích, đúng DEC-008
    """

    action: str = Field(pattern="^(map_to_existing|mark_no_data)$")
    food_id: int | None = None
    grams: float | None = Field(default=None, gt=0, le=5000)
    note_vi: str | None = None


# --------------------------------------------------------------------------
# Quyền
# --------------------------------------------------------------------------
def _profile_or_404(db: Session, profile_id: str, user: CurrentUser) -> DbPatientProfile:
    """404 (không phải 403) khi bệnh nhân đụng hồ sơ người khác.

    Trả 403 sẽ xác nhận hồ sơ đó tồn tại — rò rỉ thông tin. Theo đúng cách
    `targets.py` đang làm.
    """
    profile = db.get(DbPatientProfile, profile_id)
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hồ sơ bệnh nhân")
    if user.role == "patient" and profile.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hồ sơ bệnh nhân")
    return profile


# --------------------------------------------------------------------------
# Ghi nhật ký
# --------------------------------------------------------------------------
@router.get("/suggestions", response_model=MatchSuggestionList)
def suggest_foods(
    q: str = Query(min_length=2, max_length=255),
    limit: int = Query(default=5, ge=1, le=10),
    _user: CurrentUser = Depends(get_current_user),
) -> MatchSuggestionList:
    """Return deterministic candidates before a diary row is created."""
    suggestions = [
        MatchSuggestion(food_id=c.food_id, name_vi=c.name_vi, score=c.score, matched_on=c.matched_on)
        for c in _get_matcher().match(q)[:limit]
    ]
    return MatchSuggestionList(query=q.strip(), suggestions=suggestions)


@router.post("", response_model=FoodLogOut, status_code=status.HTTP_201_CREATED)
def create_food_log(
    payload: FoodLogCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
    _: None = Depends(guard_free_text("free_text_vi")),
) -> FoodLogOut:
    """Ghi một món đã ăn.

    Cố tình KHÔNG bắt buộc `food_id`: bệnh nhân chỉ gõ tên món. Hệ thống tự thử
    khớp; khớp không chắc thì lưu nguyên chữ họ gõ và đẩy sang hàng chờ của
    chuyên gia — không đoán bừa, cũng không bắt bệnh nhân tự tra CSDL.
    """
    _profile_or_404(db, payload.profile_id, user)

    matcher = _get_matcher()
    best = matcher.best(payload.free_text_vi)
    suggestions = [
        MatchSuggestion(food_id=c.food_id, name_vi=c.name_vi, score=c.score, matched_on=c.matched_on)
        for c in matcher.match(payload.free_text_vi)
    ]

    confirmed_food = _get_repo().get(payload.food_id) if payload.food_id is not None else None
    if payload.food_id is not None and confirmed_food is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Món đã chọn không còn trong cơ sở dữ liệu")

    if confirmed_food is not None and payload.grams is not None:
        food_id, match_status, confidence = confirmed_food.id, MATCH_PATIENT_CONFIRMED, 1.0
        grams = payload.grams
    elif best is not None and payload.grams is not None:
        food_id, match_status, confidence = best.food_id, MATCH_AUTO, best.score
        grams = payload.grams
    else:
        # Thiếu MỘT trong hai (không khớp được món, hoặc không rõ khẩu phần) là
        # đủ để coi dòng này chưa dùng được: biết ăn gì mà không biết bao nhiêu
        # thì vẫn không cộng được vào tổng (PRD FR-11).
        food_id, match_status, confidence = None, MATCH_UNMATCHED, None
        grams = None

    log = FoodLog(
        profile_id=payload.profile_id,
        logged_at=payload.logged_at or datetime.now(UTC),
        food_id=food_id,
        free_text_vi=payload.free_text_vi.strip(),
        grams=grams,
        slot=payload.slot.value,
        match_status=match_status,
        match_confidence=confidence,
        portion_qty=payload.grams,
        portion_unit="g" if payload.grams is not None else None,
        note_vi=payload.note_vi,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return FoodLogOut.from_model(log, suggestions=[] if food_id else suggestions)


@router.get("", response_model=list[FoodLogOut])
def list_food_logs(
    profile_id: str,
    day: date | None = Query(default=None),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[FoodLogOut]:
    _profile_or_404(db, profile_id, user)
    q = db.query(FoodLog).filter(FoodLog.profile_id == profile_id)
    if day is not None:
        q = q.filter(FoodLog.logged_at >= datetime.combine(day, datetime.min.time()))
        q = q.filter(FoodLog.logged_at < datetime.combine(day, datetime.max.time()))
    return [FoodLogOut.from_model(x) for x in q.order_by(FoodLog.logged_at).all()]


@router.get("/summary", response_model=DaySummaryOut)
def day_summary(
    profile_id: str,
    day: date | None = Query(default=None),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> DaySummaryOut:
    """Tổng hợp ngày + kết luận có kiểm soát.

    Con số ở đây chỉ cộng phần ĐÃ tra được. Client PHẢI đọc `coverage` và
    `verdict` — không được tự kết luận "đạt" từ mỗi con số.
    """
    profile = _profile_or_404(db, profile_id, user)
    target_day = day or datetime.now(UTC).date()

    rows = (
        db.query(FoodLog)
        .filter(FoodLog.profile_id == profile_id)
        .filter(FoodLog.logged_at >= datetime.combine(target_day, datetime.min.time()))
        .filter(FoodLog.logged_at < datetime.combine(target_day, datetime.max.time()))
        .all()
    )

    logs = [
        LoggedFood(
            log_id=r.id,
            # Dòng chuyên gia đã đánh dấu "không đủ dữ liệu" thì cố ý loại khỏi
            # phép cộng, dù nó có food_id hay không.
            food_id=None if r.match_status == MATCH_NO_DATA else r.food_id,
            grams=None if r.match_status == MATCH_NO_DATA else r.grams,
            free_text_vi=r.free_text_vi,
            slot=MealSlot(r.slot) if r.slot else MealSlot.LUNCH,
        )
        for r in rows
    ]

    targets = compute_targets(to_clinical_profile(profile), load_rules())
    summary = summarize_day(logs, targets, _get_repo(), load_rules())

    return DaySummaryOut(
        profile_id=profile_id,
        day=target_day,
        matched_count=summary.matched_count,
        unmatched_count=summary.unmatched_count,
        coverage=round(summary.coverage, 3),
        is_complete=summary.is_complete,
        verdicts=[
            NutrientVerdictOut(
                nutrient=v.nutrient,
                label_vi=v.label_vi,
                verdict=v.verdict.value,
                counted=v.counted,
                min_value=v.min_value,
                max_value=v.max_value,
                unit=v.unit,
            )
            for v in summary.verdicts
        ],
        violations=[ViolationOut(**v.model_dump(mode="json")) for v in summary.violations],
    )


# --------------------------------------------------------------------------
# Hàng chờ giải quyết của chuyên gia
# --------------------------------------------------------------------------
@router.get("/unresolved", response_model=list[FoodLogOut])
def list_unresolved(
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(require_role("dietitian", "admin")),
) -> list[FoodLogOut]:
    """Các dòng nhật ký chưa tra được, kèm gợi ý để chuyên gia bấm một phát là xong."""
    rows = db.query(FoodLog).filter(FoodLog.match_status == MATCH_UNMATCHED).order_by(FoodLog.logged_at.desc()).all()
    matcher = _get_matcher()
    out: list[FoodLogOut] = []
    for r in rows:
        suggestions = [
            MatchSuggestion(food_id=c.food_id, name_vi=c.name_vi, score=c.score, matched_on=c.matched_on)
            for c in matcher.match(r.free_text_vi or "")
        ]
        out.append(FoodLogOut.from_model(r, suggestions=suggestions))
    return out


@router.post("/{log_id}/resolve", response_model=FoodLogOut)
def resolve_food_log(
    log_id: str,
    payload: ResolveRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_role("dietitian", "admin")),
) -> FoodLogOut:
    """Chuyên gia gán món hoặc xác nhận không đủ dữ liệu."""
    log = db.get(FoodLog, log_id)
    if log is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dòng nhật ký")

    before = {
        "food_id": log.food_id,
        "grams": log.grams,
        "match_status": log.match_status,
    }

    if payload.action == "mark_no_data":
        log.match_status = MATCH_NO_DATA
        log.match_confidence = None
    else:
        if payload.food_id is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Thiếu food_id để gán món")
        # Không tin id client gửi: phải tồn tại thật trong bảng thành phần.
        if _get_repo().get(payload.food_id) is None:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"food_id={payload.food_id} không có trong cơ sở dữ liệu thực phẩm",
            )
        grams = payload.grams if payload.grams is not None else log.grams
        if grams is None:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Thiếu khẩu phần (gram) — không có số thì không tính vào tổng được",
            )
        log.food_id = payload.food_id
        log.grams = grams
        log.match_status = MATCH_EXPERT
        log.match_confidence = 1.0

    if payload.note_vi:
        log.note_vi = payload.note_vi

    after = {"food_id": log.food_id, "grams": log.grams, "match_status": log.match_status}
    db.add(
        AuditLog(
            at=datetime.now(UTC),
            actor_id=user.id,
            action="resolve_food_log",
            before=before,
            after=after,
        )
    )
    db.commit()
    db.refresh(log)
    return FoodLogOut.from_model(log)
