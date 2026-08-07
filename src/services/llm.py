"""Cổng gọi LLM (Gemini) để CHỌN món — không bao giờ để LLM tính số.

Ticket: AGT-04. Đây là bản cài đặt thật của Protocol `MenuGenerator`.

⚠️ RULE-1: LLM chỉ trả `slot + food_id + grams`. Mọi giá trị dinh dưỡng được tính
ở tầng deterministic (compute_nutrition). Schema `_LLMSelection` CỐ Ý không có bất
kỳ trường dinh dưỡng nào — nếu ai thêm vào là vi phạm kiến trúc.
"""

from __future__ import annotations

import logging
from typing import Literal

from google import genai
from google.genai import errors, types
from pydantic import BaseModel

from src.clinical.models import (
    ClinicalTargets,
    FoodItem,
    MealSlot,
    MenuDraft,
    MenuItem,
    PatientProfile,
)
from src.config import Settings, get_settings

logger = logging.getLogger(__name__)


# --- Schema LLM: CHỈ lựa chọn món, KHÔNG con số dinh dưỡng (RULE-1) ---
class _LLMItem(BaseModel):
    # KHÔNG ràng buộc ở đây: Gemini schema chỉ nhận JSON-schema tối giản. Bounds
    # (gt=0, le=2000) do MenuItem áp khi _to_menu_draft chuyển đổi.
    slot: Literal["breakfast", "lunch", "dinner", "snack"]
    food_id: int
    grams: float


class _LLMSelection(BaseModel):
    items: list[_LLMItem]


def _targets_text(targets: ClinicalTargets) -> str:
    lines = [f"- Năng lượng: {targets.bmr_kcal:.0f}-{targets.tdee_kcal:.0f} kcal/ngày (tham khảo)"]
    for name, t in targets.targets.items():
        bound = []
        if t.min_value is not None:
            bound.append(f"tối thiểu {t.min_value:.0f}")
        if t.max_value is not None:
            bound.append(f"tối đa {t.max_value:.0f}")
        if bound:
            lines.append(f"- {name}: {', '.join(bound)} {t.unit}")
    return "\n".join(lines)


def _candidates_text(candidates: list[FoodItem]) -> str:
    rows = ["id | tên | kcal/100g | carb | natri(mg) | GI"]
    for f in candidates:
        gi = f.gi_index if f.gi_index is not None else "-"
        rows.append(f"{f.id} | {f.name_vi} | {f.kcal_100g:.0f} | {f.carb_g:.0f} | {f.na_mg:.0f} | {gi}")
    return "\n".join(rows)


def _build_prompt(
    profile: PatientProfile,
    targets: ClinicalTargets,
    candidates: list[FoodItem],
    feedback: str | None,
) -> str:
    conditions = ", ".join(f"{c.code.value}{'/' + c.stage if c.stage else ''}" for c in profile.conditions)
    parts = [
        "Bạn là chuyên gia dinh dưỡng lâm sàng. Hãy CHỌN món cho thực đơn 1 ngày.",
        f"\nBệnh nhân: {profile.age} tuổi, {profile.sex.value}, bệnh: {conditions or 'không'}.",
        f"\nĐịnh mức cần tôn trọng:\n{_targets_text(targets)}",
        f"\nDanh sách món ỨNG VIÊN (chỉ được chọn từ đây):\n{_candidates_text(candidates)}",
    ]
    if feedback:
        parts.append(f"\nBản trước KHÔNG đạt, sửa đúng các điểm sau:\n{feedback}")
    parts.append(
        "\nQUY TẮC BẮT BUỘC:\n"
        "1. Chỉ trả về food_id (từ danh sách) + số gram + bữa (slot).\n"
        "2. TUYỆT ĐỐI KHÔNG tự tính hay ghi kcal/natri/đạm - hệ thống sẽ tự tính.\n"
        "3. Ưu tiên đủ năng lượng, hạn chế natri, phù hợp bệnh lý."
    )
    return "\n".join(parts)


def _to_menu_draft(selection: _LLMSelection) -> MenuDraft:
    items: dict[MealSlot, list[MenuItem]] = {}
    for item in selection.items:
        slot = MealSlot(item.slot)
        items.setdefault(slot, []).append(MenuItem(food_id=item.food_id, grams=item.grams))
    return MenuDraft(items=items)


class GeminiMenuGenerator:
    """Bản cài đặt `MenuGenerator` bằng Gemini structured output + xoay vòng key."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._keys = self._settings.gemini_keys()
        if not self._keys:
            raise ValueError("Chưa cấu hình GEMINI_API_KEY nào trong .env")
        self._model = self._settings.gemini_model

    def generate(
        self,
        profile: PatientProfile,
        targets: ClinicalTargets,
        candidates: list[FoodItem],
        feedback: str | None,
    ) -> MenuDraft:
        prompt = _build_prompt(profile, targets, candidates, feedback)
        config = types.GenerateContentConfig(
            temperature=self._settings.llm_temperature,
            response_mime_type="application/json",
            response_schema=_LLMSelection,
        )
        return _to_menu_draft(self._call_with_rotation(prompt, config))

    def _call_with_rotation(self, prompt: str, config: types.GenerateContentConfig) -> _LLMSelection:
        """Gọi Gemini; hết quota (429) thì đổi sang key kế tiếp."""
        last_error: errors.APIError | None = None
        for i, key in enumerate(self._keys):
            client = genai.Client(api_key=key)
            try:
                resp = client.models.generate_content(model=self._model, contents=prompt, config=config)
            except errors.ClientError as exc:
                if exc.code == 429 and i < len(self._keys) - 1:
                    logger.warning("Gemini key #%d het quota (429), doi key ke tiep.", i + 1)
                    last_error = exc
                    continue
                raise
            parsed = resp.parsed
            if isinstance(parsed, _LLMSelection):
                return parsed
            return _LLMSelection.model_validate_json(resp.text or "{}")
        raise RuntimeError("Tất cả key Gemini đều hết quota") from last_error
