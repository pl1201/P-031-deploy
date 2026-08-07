"""Node: generate_menu (bản hybrid)
LLM: CÓ ĐIỀU KIỆN — lượt đầu dùng CP-SAT (không LLM), chỉ gọi LLM khi cần.

Ticket: AGT-10. Đây là hộp "Hybrid Router" trong sơ đồ kiến trúc mục tiêu:
ghép `CPSATMenuOptimizer` (tất định, giải trực tiếp ràng buộc) với
`GeminiMenuGenerator` (biết đọc feedback dạng văn bản để tự sửa).

Vì sao phải phân nhánh chứ không chọn hẳn một bên:

- CP-SAT **tất định**: cùng input → cùng output. Vòng lặp retry của graph
  (`build_feedback` → `generate_menu`, tối đa `MAX_RETRIES`) vì thế vô nghĩa
  với CP-SAT — giải lại sẽ ra đúng thực đơn cũ, lãng phí 3 vòng rồi mới tới
  `fallback`. CP-SAT cũng không đọc được `feedback`, vì feedback là câu tiếng
  Việt chứ không phải ràng buộc toán học.
- Ngược lại CP-SAT rẻ hơn hẳn ở lượt đầu: không tốn token, ~0,1 s, và mọi ràng
  buộc đã mô hình hoá được **đảm bảo** thoả chứ không phải "hy vọng LLM đoán
  trúng".

Nên: lượt đầu (`feedback is None`) giao CP-SAT. Nếu CP-SAT vô nghiệm, hoặc nếu
`validate` đã fail một lần và đưa feedback về (nghĩa là có ràng buộc CHƯA mô
hình hoá được, VD tương tác thuốc — thực phẩm), thì chuyển cho LLM — bên duy
nhất có thể phản ứng với feedback.

RULE-1 vẫn giữ nguyên ở cả hai nhánh: không nhánh nào trả về giá trị dinh
dưỡng, chỉ `food_id` + `grams`.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from src.agents.nodes.core import MenuGenerator
from src.agents.optimizer import CPSATMenuOptimizer
from src.clinical.models import ClinicalTargets, FoodItem, MenuDraft, PatientProfile

logger = logging.getLogger(__name__)


class HybridMenuGenerator:
    """Bản cài đặt `Protocol MenuGenerator`: CP-SAT trước, LLM khi cần.

    `llm_factory` được gọi **trễ** (chỉ khi thật sự phải dùng LLM) để nhánh
    CP-SAT chạy được mà không cần `GEMINI_API_KEY` — nhờ vậy CI và test chạy
    được toàn bộ luồng thật mà không cần key.
    """

    def __init__(
        self,
        optimizer: MenuGenerator | None = None,
        llm_factory: Callable[[], MenuGenerator] | None = None,
    ) -> None:
        self._optimizer: MenuGenerator = optimizer or CPSATMenuOptimizer()
        self._llm_factory = llm_factory or _default_llm_factory
        self._llm: MenuGenerator | None = None

    def generate(
        self,
        profile: PatientProfile,
        targets: ClinicalTargets,
        candidates: list[FoodItem],
        feedback: str | None,
    ) -> MenuDraft:
        if feedback is None:
            draft = self._optimizer.generate(profile=profile, targets=targets, candidates=candidates, feedback=None)
            if draft.all_items():
                return draft
            logger.info("HybridMenuGenerator: CP-SAT vô nghiệm, chuyển sang LLM.")
        else:
            logger.info("HybridMenuGenerator: đã có feedback từ validate, chuyển sang LLM.")

        return self._get_llm().generate(profile=profile, targets=targets, candidates=candidates, feedback=feedback)

    def _get_llm(self) -> MenuGenerator:
        if self._llm is None:
            self._llm = self._llm_factory()
        return self._llm


def _default_llm_factory() -> MenuGenerator:
    # Import trễ: không kéo `google.genai` vào tiến trình khi chỉ dùng CP-SAT.
    from src.services.llm import GeminiMenuGenerator

    return GeminiMenuGenerator()
