"""Cảnh báo tương tác thuốc–thực phẩm — CLN-06.

LLM: **NO**. Module nằm trong `src/clinical/` nên tuyệt đối không import LLM
client (có test `DETERMINISTIC_FILES` kiểm tra).

Bối cảnh: `data/seeds/drug_food_interactions.csv` (30 cặp) đã được seed vào DB
từ lâu nhưng **chưa một dòng code nào truy vấn** — thuốc bệnh nhân đang dùng
hoàn toàn không ảnh hưởng gì tới thực đơn được sinh ra. Đây là khoảng trống an
toàn thật, không phải nợ kỹ thuật thẩm mỹ.

Hai chế độ khớp, và chỉ MỘT trong hai được phép sinh cảnh báo tự động
------------------------------------------------------------------
Đọc kỹ dữ liệu thì 30 dòng chia làm hai loại khác hẳn nhau:

1. **Theo TÊN thực phẩm cụ thể** — "bưởi", "rau ngót", "cải bắp", "rượu bia",
   "trà và cà phê". Khớp được chắc chắn: chỉ cần thực đơn/nhật ký có món đó.
   → Sinh `Violation` kèm `evidence` = đúng tên món đã kích hoạt.

2. **Theo NHÓM chất** — "thực phẩm giàu kali", "chất xơ liều cao", "canxi (sữa
   và chế phẩm)". Muốn tự phát hiện thì phải có ngưỡng ("giàu kali" là bao
   nhiêu mg?). **Ngưỡng đó là quyết định lâm sàng, không phải quyết định kỹ
   thuật** — tự đặt số ở đây là đúng thứ DEC-008 cấm. Nên loại này KHÔNG sinh
   cảnh báo theo từng món, mà trả về dạng *lưu ý cho chuyên gia* qua
   `advisories_for()`: nêu đúng điều Dược thư nói, không tự phán món nào vi phạm.

Vì sao cảnh báo `to_verify` bị hạ xuống SOFT
--------------------------------------------
Cả 30 dòng hiện đều `verify_status='to_verify'`, trong khi PRD FR-14 nói chỉ
kích hoạt rule đã `verified`. Hai cách xử lý cực đoan đều sai:
- Bỏ hẳn không cảnh báo → giấu mất cảnh báo warfarin/vitamin K thật.
- Cho chặn cứng → một rule chưa ai rà lại có quyền chặn thực đơn.

Nên: **vẫn cảnh báo, nhưng không bao giờ HARD khi chưa `verified`**, và nói
thẳng trong câu chữ là chưa được chuyên gia xác minh. Khi R2 rà xong và đổi
`verify_status='verified'`, cặp `severity=high` sẽ tự động lên HARD.
"""

from __future__ import annotations

import csv
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from .models import FoodItem, MenuDraft, PatientProfile, Severity, Violation
from .nutrition import FoodRepository

SEEDS_DIR = Path(__file__).resolve().parents[2] / "data" / "seeds"

# Cụm từ báo hiệu dòng nói về NHÓM CHẤT chứ không phải một món cụ thể — loại
# này cần ngưỡng lâm sàng nên không tự khớp theo tên món (xem docstring).
_NUTRIENT_GROUP_MARKERS = (
    "thực phẩm giàu",
    "liều cao",
    "chứa kali",
    "và chế phẩm",
)

VERIFIED = "verified"


def _norm(text: str) -> str:
    """Chuẩn hoá để so khớp tên thuốc/thực phẩm: NFC, thường, bỏ ngoặc, gọn."""
    text = unicodedata.normalize("NFC", str(text)).strip().lower()
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"[^\w\sÀ-ỹ]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


@dataclass(frozen=True)
class DrugFoodRule:
    """Một cặp tương tác thuốc–thực phẩm đã chuẩn hoá."""

    drug_name: str
    drug_class: str | None
    food_or_nutrient: str
    severity: str  # high | moderate | low
    mechanism_vi: str
    recommendation_vi: str
    source_ref: str | None
    verify_status: str

    @property
    def is_nutrient_group(self) -> bool:
        """True khi dòng nói về nhóm chất (cần ngưỡng) chứ không phải món cụ thể."""
        low = self.food_or_nutrient.lower()
        return any(marker in low for marker in _NUTRIENT_GROUP_MARKERS)

    @property
    def effective_severity(self) -> Severity:
        """`high` + đã xác minh ⇒ chặn cứng. Mọi trường hợp khác ⇒ cảnh báo mềm.

        Rule chưa qua tay chuyên gia không được quyền chặn thực đơn (PRD FR-14),
        nhưng cũng không bị giấu đi.
        """
        if self.severity == "high" and self.verify_status == VERIFIED:
            return Severity.HARD
        return Severity.SOFT

    def food_terms(self) -> list[str]:
        """Các cụm từ dùng để dò trong tên món.

        "trà và cà phê" phải tách thành ["trà", "cà phê"] — nếu để nguyên thì
        không món nào khớp nổi.
        """
        raw = re.sub(r"\([^)]*\)", " ", self.food_or_nutrient)
        parts = re.split(r"\s*(?:,|;|/|\bvà\b|\bhoặc\b)\s*", raw)
        return [p for p in (_norm(p) for p in parts) if len(p) >= 2]


def load_drug_food_rules(path: Path | None = None) -> list[DrugFoodRule]:
    """Nạp `drug_food_interactions.csv`. Bỏ qua dòng thiếu trường bắt buộc."""
    path = path or SEEDS_DIR / "drug_food_interactions.csv"
    rules: list[DrugFoodRule] = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            drug = (row.get("drug_name") or "").strip()
            food = (row.get("food_or_nutrient") or "").strip()
            if not drug or not food:
                continue
            rules.append(
                DrugFoodRule(
                    drug_name=drug,
                    drug_class=(row.get("drug_class") or "").strip() or None,
                    food_or_nutrient=food,
                    severity=(row.get("severity") or "moderate").strip().lower(),
                    mechanism_vi=(row.get("mechanism_vi") or "").strip(),
                    recommendation_vi=(row.get("recommendation_vi") or "").strip(),
                    source_ref=(row.get("source_ref") or "").strip() or None,
                    verify_status=(row.get("verify_status") or "to_verify").strip().lower(),
                )
            )
    return rules


def rules_for_medications(medications: list[str], rules: list[DrugFoodRule]) -> list[DrugFoodRule]:
    """Lọc rule khớp danh sách thuốc bệnh nhân đang dùng.

    Khớp hai chiều theo cụm từ: đơn thuốc ghi "Metformin 500mg" phải khớp rule
    "Metformin", và ngược lại rule "Sulfonylurea (Gliclazide)" phải khớp đơn ghi
    "gliclazide" (nhờ `food_terms`-style tách ngoặc ở `_drug_terms`).
    """
    if not medications:
        return []
    meds = [_norm(m) for m in medications if str(m).strip()]
    matched: list[DrugFoodRule] = []
    for rule in rules:
        if any(_drug_matches(med, rule) for med in meds):
            matched.append(rule)
    return matched


def _drug_terms(rule: DrugFoodRule) -> list[str]:
    """Tên hoạt chất rút từ `drug_name`, gồm cả phần trong ngoặc."""
    terms = [_norm(rule.drug_name)]
    terms += [_norm(t) for t in re.findall(r"\(([^)]*)\)", rule.drug_name)]
    return [t for t in terms if len(t) >= 3]


def _drug_matches(med_normalized: str, rule: DrugFoodRule) -> bool:
    for term in _drug_terms(rule):
        if term in med_normalized or med_normalized in term:
            return True
    return False


def _foods_matching(term: str, foods: list[FoodItem]) -> list[FoodItem]:
    """Món có tên/alias chứa trọn cụm `term` (đã chuẩn hoá).

    Dùng ranh giới từ để "bưởi" không khớp nhầm vào một tên dài ngẫu nhiên có
    chứa chuỗi con đó.
    """
    pattern = re.compile(rf"(?:^|\s){re.escape(term)}(?:\s|$)")
    hits: list[FoodItem] = []
    for food in foods:
        labels = [food.name_vi, *food.aliases]
        if any(pattern.search(_norm(label)) for label in labels):
            hits.append(food)
    return hits


def check_drug_food_interactions(
    menu: MenuDraft,
    profile: PatientProfile,
    repo: FoodRepository,
    rules: list[DrugFoodRule] | None = None,
) -> list[Violation]:
    """Cảnh báo tương tác cho các món CÓ TÊN cụ thể trong thực đơn/nhật ký.

    Chỉ sinh cảnh báo khi chỉ đích danh được món đã kích hoạt — `evidence` luôn
    ghi tên món đó để chuyên gia soi lại được. Rule theo nhóm chất xem
    `advisories_for()`.
    """
    if not profile.medications:
        return []

    rules = rules if rules is not None else load_drug_food_rules()
    applicable = [r for r in rules_for_medications(profile.medications, rules) if not r.is_nutrient_group]
    if not applicable:
        return []

    foods_in_menu: list[FoodItem] = []
    seen: set[int] = set()
    for item in menu.all_items():
        if item.food_id in seen:
            continue
        food = repo.get(item.food_id)
        if food is not None:
            seen.add(item.food_id)
            foods_in_menu.append(food)

    violations: list[Violation] = []
    reported: set[tuple[str, int]] = set()
    for rule in applicable:
        for term in rule.food_terms():
            for food in _foods_matching(term, foods_in_menu):
                key = (rule.drug_name, food.id)
                if key in reported:
                    continue
                reported.add(key)
                violations.append(_to_violation(rule, food))
    return violations


def _to_violation(rule: DrugFoodRule, food: FoodItem) -> Violation:
    chua_xac_minh = "" if rule.verify_status == VERIFIED else " (⚠️ cặp tương tác này chưa được chuyên gia xác minh)"
    return Violation(
        nutrient=f"{rule.drug_name}–{food.name_vi}",
        # actual/limit để None: đây là cảnh báo ĐỊNH TÍNH, không có ngưỡng số.
        # Nhồi 0.0 vào sẽ khiến UI hiển thị "0" như một số đo thật (RULE-2).
        kind="drug_food",
        severity=rule.effective_severity,
        message_vi=(
            f"Bệnh nhân đang dùng {rule.drug_name}; thực đơn có {food.name_vi}. "
            f"{rule.mechanism_vi}.{chua_xac_minh}"
        ),
        suggestion=rule.recommendation_vi or None,
        source_ref=rule.source_ref,
        evidence=f"{rule.food_or_nutrient} → {food.name_vi}",
    )


def advisories_for(profile: PatientProfile, rules: list[DrugFoodRule] | None = None) -> list[Violation]:
    """Lưu ý theo NHÓM CHẤT cho chuyên gia — không quy kết món nào vi phạm.

    Tách riêng khỏi `check_drug_food_interactions()` vì đây không phải phát
    hiện dựa trên bằng chứng trong thực đơn: ta chỉ đang nhắc lại điều Dược thư
    nói về loại thuốc bệnh nhân đang dùng. Gộp chung sẽ khiến chuyên gia tưởng
    hệ thống đã kiểm tra và kết luận, trong khi ngưỡng "giàu kali" vẫn chưa ai
    định nghĩa (xem docstring module — cần R2 chốt).
    """
    if not profile.medications:
        return []

    rules = rules if rules is not None else load_drug_food_rules()
    applicable = [r for r in rules_for_medications(profile.medications, rules) if r.is_nutrient_group]

    out: list[Violation] = []
    for rule in applicable:
        out.append(
            Violation(
                nutrient=f"{rule.drug_name}–{rule.food_or_nutrient}",
                kind="drug_food",
                severity=Severity.SOFT,  # luôn mềm: chưa có bằng chứng món cụ thể
                message_vi=(
                    f"Bệnh nhân đang dùng {rule.drug_name} — cần lưu ý nhóm "
                    f"{rule.food_or_nutrient}. {rule.mechanism_vi}. "
                    f"Hệ thống CHƯA tự kiểm tra được nhóm này (chưa có ngưỡng lâm sàng), "
                    f"chuyên gia vui lòng tự rà."
                ),
                suggestion=rule.recommendation_vi or None,
                source_ref=rule.source_ref,
                evidence=f"nhóm chất: {rule.food_or_nutrient}",
            )
        )
    return out
