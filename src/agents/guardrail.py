"""AGT-07: Guardrail chặn chỉ định y khoa.

LLM: Tầng 2 (Gemini classifier) - chỉ dùng khi regex tầng 1 không chắc.
Tầng 1: regex tiếng Việt (nhanh, không tốn API).
Tầng 2: Gemini zero-shot classifier (khi cần ≥95% accuracy).

AC:
- ≥95% chặn đúng trên 20 câu red-team (test_guardrail.py)
- Không chặn nhầm câu hỏi dinh dưỡng bình thường (FP < 10%)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tầng 1: Regex patterns tiếng Việt
# ---------------------------------------------------------------------------

_MEDICAL_PATTERNS: list[str] = [
    # Liều thuốc / chỉ số
    r"(?i)(liều|mg|mcg|ml|đơn vị|unit|IU)\s*(thuốc|insulin|metformin|gliclazide|glibenclamide|acarbose|sitagliptin|empagliflozin|dapagliflozin|warfarin|statin|atorvastatin|simvastatin|amlodipine|captopril|enalapril|losartan)",
    r"(?i)uống\s*(?:bao nhiêu|mấy|bao lâu|khi nào)\s*(thuốc|viên|mg)",
    r"(?i)(nên|có nên|có thể|được không)\s*(uống|dùng|ngừng|dừng|bỏ|đổi|thay|tăng|giảm)\s*(thuốc|insulin|liều)",
    r"(?i)(ngừng|dừng|bỏ|đổi|thay|tăng|giảm)\s*(thuốc|insulin|liều|metformin|gliclazide)",
    # Chẩn đoán / xét nghiệm
    r"(?i)(bị bệnh gì|mắc bệnh gì|chẩn đoán|kết quả xét nghiệm|HbA1c của tôi|đường huyết của tôi|tôi có bị)",
    r"(?i)(tôi có bị|có phải tôi|tôi có mắc)\s*(đái tháo đường|tiểu đường|tăng huyết áp|bệnh thận|gout|ung thư|tim mạch)",
    r"(?i)(xét nghiệm|kết quả|chỉ số)\s*(bình thường|cao|thấp|nguy hiểm|ổn)",
    # Kê đơn / biến chứng
    r"(?i)(kê|kê đơn|cần|phải)\s*(thuốc|đơn thuốc|toa thuốc)",
    r"(?i)(biến chứng|cắt cụt|mù|thận hư|suy thận|đột quỵ|nhồi máu)",
    r"(?i)(tiêm insulin|chích insulin|kim tiêm)",
    # Câu hỏi y tế trực tiếp
    r"(?i)(bác sĩ|bác sỹ|chuyên gia|y tá)\s*(nói|khuyên|dặn|tư vấn)\s*(gì|rằng|là)",
    r"(?i)thuốc\s*(này|đó|tôi đang uống)\s*(có hại|nguy hiểm|an toàn|được không|tốt không)",
    r"(?i)(huyết áp|đường huyết|HbA1c)\s*(cao|thấp|nguy hiểm|bình thường|của tôi)\s*(là|có|nên|phải)",
    # Kết quả xét nghiệm / chỉ số y tế nguy hiểm
    r"(?i)(kết quả|chỉ số)\s*(HbA1c|đường huyết|huyết áp|eGFR|creatinine)\s*[\d.,]+\s*(có nguy hiểm|nguy hiểm|bình thường|cao|thấp|ổn)",
    r"(?i)(HbA1c|đường huyết|huyết áp)\s*[\d.,]+\s*(của tôi|tôi có|có nguy)",
    # Tương tác thuốc-thuốc (không phải thuốc-thực phẩm)
    r"(?i)thuốc\s*(tôi đang uống|này|đó)\s*(có tương tác|tương tác)\s*(với thuốc|thuốc khác)",
    r"(?i)(tương tác|kết hợp|dùng chung)\s*(giữa|với)\s*(hai loại thuốc|thuốc [a-zàáâãèéêìíòóôõùúăđơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ]+\s+và thuốc)",
    # Đổi/chuyển loại thuốc
    r"(?i)(đổi|chuyển|thay)\s*(từ|sang)\s*[a-zàáâãèéêìíòóôõùúăđơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ]+\s*(sang|thành)\s*[a-zàáâãèéêìíòóôõùúăđơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ]+",
    r"(?i)(nên|có nên|có thể)\s*(đổi|chuyển|thay)\s*(thuốc|từ|glibenclamide|metformin|insulin|gliclazide)",
    r"(?i)(phải|nên|được)\s*(tiêm|truyền|phẫu thuật|mổ|nội soi)",
]

_COMPILED = [re.compile(p) for p in _MEDICAL_PATTERNS]

# Patterns an toàn - không chặn dù match tên thuốc (dinh dưỡng liên quan thuốc)
_SAFE_PATTERNS: list[str] = [
    r"(?i)(thực phẩm|rau|quả|món ăn|ăn gì|không ăn|nên ăn|tránh ăn|kiêng)\s.{0,30}(warfarin|statin|metformin|ACE|thuốc)",
    r"(?i)(tương tác|ảnh hưởng)\s*(thực phẩm|dinh dưỡng|ăn uống)",
    r"(?i)(vitamin K|grapefruit|rượu|cồn|caffeine)\s.{0,20}(thuốc|warfarin|statin)",
    r"(?i)ăn gì\s*(tốt|tốt nhất|tốt cho|phù hợp|khi|lúc|để)",
    r"(?i)(thực đơn|khẩu phần|bữa ăn|dinh dưỡng|calo|carb|protein|chất béo|chất xơ)",
    r"(?i)(GI|glycemic|đường huyết sau ăn|kiểm soát đường)\s*(của thực phẩm|thấp|cao|index)",
]

_SAFE_COMPILED = [re.compile(p) for p in _SAFE_PATTERNS]

# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class GuardrailResult:
    blocked: bool
    confidence: float  # 0.0–1.0
    reason: str = ""
    safe_response: str = field(default_factory=lambda: _SAFE_RESPONSE)
    method: str = "regex"  # "regex" | "llm" | "safe_pattern"

_SAFE_RESPONSE = (
    "Tôi là công cụ hỗ trợ tư vấn dinh dưỡng, không có chức năng tư vấn "
    "y khoa, kê đơn hoặc điều chỉnh thuốc. Vui lòng trao đổi trực tiếp với "
    "bác sĩ hoặc chuyên gia y tế của bạn về câu hỏi này. 🏥"
)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def check_guardrail(message: str) -> GuardrailResult:
    """Kiểm tra message có phải câu hỏi y tế cần chặn không.

    Tầng 1: Regex nhanh.
    Tầng 2: LLM classifier (nếu regex không chắc).

    Returns:
        GuardrailResult với blocked=True nếu cần chặn.
    """
    if not message or not message.strip():
        return GuardrailResult(blocked=False, confidence=1.0, reason="empty")

    # Kiểm tra safe patterns trước (tránh false positive)
    for pat in _SAFE_COMPILED:
        if pat.search(message):
            return GuardrailResult(
                blocked=False,
                confidence=0.9,
                reason="safe_pattern_match",
                method="safe_pattern",
            )

    # Tầng 1: Regex
    matches = [pat.pattern for pat in _COMPILED if pat.search(message)]
    if matches:
        logger.debug("Guardrail tầng 1 chặn message. Patterns: %s", matches[:2])
        return GuardrailResult(
            blocked=True,
            confidence=0.95,
            reason=f"regex_match:{matches[0][:40]}",
            method="regex",
        )

    # Tầng 2: LLM (nếu có API key) — chỉ gọi khi cần
    try:
        return _classify_with_llm(message)
    except Exception as exc:
        logger.debug("LLM classifier lỗi, mặc định không chặn: %s", exc)
        return GuardrailResult(blocked=False, confidence=0.6, reason="llm_error_passthrough", method="llm")


def _classify_with_llm(message: str) -> GuardrailResult:
    """Tầng 2: Gemini zero-shot classifier."""
    try:
        from src.config import get_settings  # lazy import
        settings = get_settings()
        if not settings.gemini_api_key:
            raise ValueError("Không có GEMINI_API_KEY")

        import google.generativeai as genai  # type: ignore
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        prompt = (
            "Phân loại câu hỏi sau: có phải yêu cầu tư vấn y khoa "
            "(chẩn đoán, kê đơn, điều chỉnh thuốc, xét nghiệm) không?\n\n"
            f"Câu hỏi: {message[:400]}\n\n"
            "Trả lời JSON: {\"is_medical\": true/false, \"confidence\": 0.0-1.0, \"reason\": \"...\"}"
        )
        response = model.generate_content(prompt)
        import json
        text = response.text.strip()
        # Extract JSON
        start = text.find("{")
        end = text.rfind("}") + 1
        data = json.loads(text[start:end])

        is_medical: bool = data.get("is_medical", False)
        confidence: float = float(data.get("confidence", 0.5))
        reason: str = data.get("reason", "")

        return GuardrailResult(
            blocked=is_medical and confidence >= 0.75,
            confidence=confidence,
            reason=reason,
            method="llm",
        )
    except ImportError:
        raise ValueError("google-generativeai không được cài")
