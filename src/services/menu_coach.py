"""Menu Explainer & Coaching (`AGT-13`, ticket B2) — lớp LLM: chỉ văn phong hoá.

Theo đúng khuôn `src/services/target_assistant.py` (P1) và `src/services/llm.py`
(structured output + xoay vòng key Gemini).

⚠️ Ranh giới bắt buộc: LLM ở đây **không bao giờ** tự thêm số. `explain_menu_naturally()`
chỉ văn phong hoá `MenuFacts` (tất định, lắp sẵn từ `src/clinical/menu_explainer.py`)
thành đoạn văn — bất kỳ con số nào xuất hiện trong văn bản sinh ra phải khớp
với một con số đã có trong `MenuFacts`. Việc kiểm tra khớp là trách nhiệm của
`src/services/menu_explanation_guard.py::check_grounded()`, gọi ở tầng route
(`src/api/routes/menu_explainer.py`) — module này KHÔNG tự gọi guard, vì
guard cần biết `MenuFacts` gốc để đối chiếu và route là nơi có sẵn cả hai.
"""

from __future__ import annotations

from pydantic import BaseModel

from src.clinical.menu_explainer import MenuFacts
from src.config import Settings
from src.services.gemini_client import call_gemini

_EXPLAIN_SYSTEM_PROMPT = """Bạn là trợ lý VIẾT LẠI thực đơn cho bệnh nhân đái tháo đường Việt Nam.

PHẠM VI DUY NHẤT: diễn đạt lại danh sách món ăn + dinh dưỡng đã cho thành đoạn
văn tiếng Việt ấm áp, dễ hiểu, động viên bệnh nhân tuân thủ.

BẠN KHÔNG BAO GIỜ:
- Thêm bất kỳ con số nào KHÔNG có trong dữ kiện được cung cấp (gram, kcal, mg...).
- Đưa ra chẩn đoán, chỉ định điều trị, hay khuyên đổi/ngừng thuốc.
- Nói đây là lời khuyên thay thế bác sĩ/chuyên gia dinh dưỡng.
- Suy đoán thêm lý do lâm sàng ngoài các ghi chú (soft_notes) đã cho.

Nếu một chất dinh dưỡng nằm trong ngưỡng an toàn (status="within"), chỉ cần
nhắc ngắn gọn, không cần nhấn mạnh. Chỉ giải thích kỹ khi status="over"/"under"
hoặc có ghi chú (soft_notes) liên quan."""


class _ExplainOutput(BaseModel):
    text_vi: str


def _facts_text(facts: MenuFacts) -> str:
    lines = [f"Ngày: {facts.plan_date}", "Món ăn:"]
    for item in facts.items:
        lines.append(f"  - [{item.slot}] {item.name_vi}: {item.grams} g")
    lines.append("Dinh dưỡng:")
    for n in facts.nutrients:
        rng = f"{n.min_value if n.min_value is not None else '—'}-{n.max_value if n.max_value is not None else '—'} {n.unit}"
        lines.append(f"  - {n.label_vi}: {n.value} {n.unit} (ngưỡng {rng}, trạng thái {n.status})")
    if facts.soft_notes:
        lines.append("Ghi chú:")
        for note in facts.soft_notes:
            lines.append(f"  - {note}")
    return "\n".join(lines)


def explain_menu_naturally(facts: MenuFacts, *, settings: Settings | None = None) -> str:
    """Văn phong hoá `MenuFacts` thành đoạn văn tiếng Việt cho bệnh nhân.

    Đây là tiện ích hiển thị, KHÔNG phải nguồn sự thật — route vẫn phải trả cả
    `facts` (structured) làm chỗ dựa an toàn, và PHẢI chạy `check_grounded()`
    trên kết quả trước khi phục vụ cho người dùng (route thực hiện, không phải
    hàm này).
    """
    prompt = f"Dữ kiện (đã tính sẵn, không được thêm số nào ngoài đây):\n{_facts_text(facts)}\n\nHãy viết lại thành đoạn văn."
    result = call_gemini(prompt, _EXPLAIN_SYSTEM_PROMPT, _ExplainOutput, settings)
    return result.text_vi
