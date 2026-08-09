"""Trợ lý ngưỡng cho chuyên gia (P1) — lớp LLM: diễn đạt + parse tham số.

Ticket: P1 (trả lời câu hỏi Q3 của Hưng). Đây là bản cài đặt Gemini, theo đúng
khuôn `src/services/llm.py` (structured output + xoay vòng key).

⚠️ Ranh giới bắt buộc: LLM ở đây **không bao giờ** sinh ra một con số ngưỡng.
- `explain_naturally()` chỉ văn phong hoá dữ kiện ĐÃ CÓ từ
  `src/clinical/target_explainer.py` (tất định) — nếu ai thêm field số vào
  input thì cứ đưa vào, nhưng bản thân hàm này không được PHÉP tự bịa số nào
  không có trong `NutrientExplanation`.
- `parse_what_if()` chỉ trả về `ProfileDelta` — enum bệnh lý (`ConditionCode`),
  chuỗi giai đoạn, danh sách cờ. KHÔNG CÓ field số nào trong schema — Pydantic
  tự chặn LLM trả field lạ, không cần code phòng thủ thêm.

Mọi con số ngưỡng thật luôn đến từ `compute_targets()` gọi LẠI trên
`ProfileDelta` đã áp vào bản sao hồ sơ — xem `apply_delta()`.
"""

from __future__ import annotations

import logging
from typing import Literal, TypeVar

from google import genai
from google.genai import errors, types
from pydantic import BaseModel, Field

from src.clinical.models import Condition, ConditionCode, PatientProfile
from src.clinical.target_explainer import NutrientExplanation
from src.config import Settings, get_settings

logger = logging.getLogger(__name__)

_CLINICAL_FLAGS = Literal["frailty_sarcopenia", "metabolically_unstable", "sodium_wasting"]


class ProfileDelta(BaseModel):
    """Thay đổi hồ sơ do chuyên gia mô tả bằng lời — KHÔNG có field số nào.

    `condition_code=None` nghĩa là câu hỏi không đề cập đổi bệnh lý (VD chỉ hỏi
    thêm cờ frailty). Muốn XOÁ một bệnh lý không nằm trong phạm vi what-if này
    — chỉ hỗ trợ thêm mới/đổi giai đoạn/thêm cờ, đúng nhu cầu thật "nếu nặng
    hơn thì sao" chứ không phải sửa hồ sơ tuỳ ý.
    """

    condition_code: ConditionCode | None = None
    stage: str | None = None
    flags: list[_CLINICAL_FLAGS] = Field(default_factory=list)


def apply_delta(profile: PatientProfile, delta: ProfileDelta) -> PatientProfile:
    """Áp delta lên một BẢN SAO hồ sơ — không bao giờ sửa profile gốc.

    Đây là hàm thuần Python (LLM: NO nếu tách riêng, nhưng ở chung file cho
    tiện vì luôn đi cùng `parse_what_if`) — mọi field vào/ra đều đã được
    Pydantic validate cứng qua `ProfileDelta`, không có chỗ nào nhận input tự
    do trực tiếp.
    """
    conditions = list(profile.conditions)
    if delta.condition_code is not None:
        conditions = [c for c in conditions if c.code != delta.condition_code]
        conditions.append(Condition(code=delta.condition_code, stage=delta.stage))

    updates: dict = {"conditions": conditions}
    for flag in delta.flags:
        updates[flag] = True

    return profile.model_copy(update=updates)


# ---------------------------------------------------------------------------
# Diễn đạt tự nhiên — chỉ văn phong hoá, không thêm dữ kiện
# ---------------------------------------------------------------------------
class _ExplainOutput(BaseModel):
    text_vi: str


_EXPLAIN_SYSTEM_PROMPT = """Bạn là trợ lý VIẾT LẠI cho chuyên gia dinh dưỡng lâm sàng Việt Nam.

PHẠM VI DUY NHẤT: diễn đạt lại danh sách dữ kiện đã cho thành đoạn văn tiếng Việt
mạch lạc, ngắn gọn, đúng giọng văn chuyên môn.

BẠN KHÔNG BAO GIỜ:
- Thêm bất kỳ con số nào KHÔNG có trong dữ kiện được cung cấp.
- Suy đoán thêm rule, guideline, hay lý do nào ngoài dữ kiện đã cho.
- Đưa ra khuyến nghị lâm sàng của riêng bạn.
- Nói rằng đây là chẩn đoán hay chỉ định điều trị.

Nếu một chất không có dữ kiện gì đáng chú ý (không rule loại, không xung đột),
chỉ cần nêu ngắn gọn ngưỡng và rule áp dụng, không cần bịa thêm diễn giải."""


def _explanation_facts_text(explanations: list[NutrientExplanation]) -> str:
    lines: list[str] = []
    for e in explanations:
        rng = f"{e.min_value if e.min_value is not None else '—'}-{e.max_value if e.max_value is not None else '—'} {e.unit or ''}"
        lines.append(f"- {e.label_vi} ({e.nutrient}): {rng}")
        for a in e.applied:
            lines.append(f"    + Áp dụng {a.rule_id} ({a.guideline_ref}): {a.bound}={a.resolved_value} {a.unit}")
        for x in e.excluded:
            lines.append(f"    - Không áp {x.rule_id} ({x.guideline_ref}): {x.reason}")
        for note in e.conflict_notes:
            lines.append(f"    ! Xung đột: {note}")
    return "\n".join(lines)


def explain_naturally(explanations: list[NutrientExplanation], *, settings: Settings | None = None) -> str:
    """Văn phong hoá danh sách `NutrientExplanation` thành đoạn văn tiếng Việt.

    Đây là tiện ích hiển thị, KHÔNG phải nguồn sự thật — UI vẫn phải hiện được
    `explanations` gốc (structured) làm chỗ dựa an toàn nếu đoạn văn diễn đạt
    sai hoặc lược bớt điều gì đó quan trọng.
    """
    if not explanations:
        return "Chưa có ngưỡng nào để giải thích."
    facts = _explanation_facts_text(explanations)
    prompt = f"Dữ kiện (đã tính sẵn, không được thêm số nào ngoài đây):\n{facts}\n\nHãy viết lại thành đoạn văn."
    result = _call_gemini(prompt, _EXPLAIN_SYSTEM_PROMPT, _ExplainOutput, settings)
    return result.text_vi


# ---------------------------------------------------------------------------
# Parse what-if — chỉ trả tham số, không trả số
# ---------------------------------------------------------------------------
_WHAT_IF_SYSTEM_PROMPT = """Bạn là bộ phân tích câu hỏi "nếu...thì sao" của chuyên gia dinh dưỡng.

PHẠM VI DUY NHẤT: đọc câu hỏi tiếng Việt và trả về ĐÚNG bệnh lý/giai đoạn/cờ
lâm sàng được nhắc tới — không trả bất kỳ trường nào khác.

Mã bệnh lý hợp lệ: T2DM (đái tháo đường týp 2), HTN (tăng huyết áp), CKD (bệnh
thận mạn), GOUT (gout). Giai đoạn CKD dùng ký hiệu G1..G5 (có thể có hậu tố
như G3a/G3b). Cờ lâm sàng hợp lệ: frailty_sarcopenia (suy yếu/thiểu cơ),
metabolically_unstable (chuyển hoá không ổn định), sodium_wasting (bệnh thận
mất muối).

Câu hỏi không nhắc tới bệnh lý mới thì để condition_code = null, chỉ điền cờ
nếu có nhắc tới. KHÔNG được tự suy đoán ra thông tin không có trong câu hỏi."""


def parse_what_if(question_vi: str, *, settings: Settings | None = None) -> ProfileDelta:
    return _call_gemini(question_vi, _WHAT_IF_SYSTEM_PROMPT, ProfileDelta, settings)


# ---------------------------------------------------------------------------
# Gọi Gemini — xoay vòng key, giống khuôn src/services/llm.py
# ---------------------------------------------------------------------------
_SchemaT = TypeVar("_SchemaT", bound=BaseModel)


def _call_gemini(
    prompt: str,
    system_prompt: str,
    schema: type[_SchemaT],
    settings: Settings | None,
) -> _SchemaT:
    settings = settings or get_settings()
    keys = settings.gemini_keys()
    if not keys:
        raise ValueError("Chưa cấu hình GEMINI_API_KEY nào trong .env")

    config = types.GenerateContentConfig(
        temperature=settings.llm_temperature,
        response_mime_type="application/json",
        response_schema=schema,
        system_instruction=system_prompt,
    )

    last_error: errors.APIError | None = None
    for i, key in enumerate(keys):
        client = genai.Client(api_key=key)
        try:
            resp = client.models.generate_content(model=settings.gemini_model, contents=prompt, config=config)
        except errors.ClientError as exc:
            if exc.code == 429 and i < len(keys) - 1:
                logger.warning("Gemini key #%d het quota (429), doi key ke tiep.", i + 1)
                last_error = exc
                continue
            raise
        parsed = resp.parsed
        if isinstance(parsed, schema):
            return parsed
        return schema.model_validate_json(resp.text or "{}")
    raise RuntimeError("Tất cả key Gemini đều hết quota") from last_error
