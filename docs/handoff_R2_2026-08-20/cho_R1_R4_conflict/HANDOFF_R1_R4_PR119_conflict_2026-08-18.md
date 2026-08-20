# Bàn giao R1 + R4 — PR #119 đang conflict với `main`, tối 18/08

PR: https://github.com/AI20K-Build-Phase-Cohort-3/P-031/pull/119
Branch: `feature/CLN-rule-risk-level-qd5481`
Trạng thái đo được (R2, 18/08 21:xx): `mergeable: CONFLICTING`, chưa có review nào.

Xung đột chỉ ở 4 file, không đụng `data/seeds/**` (phần R2 vừa đẩy lên sạch, sẵn sàng merge ngay khi 4 file này xong):

| File | Quy mô đổi trên branch so với `main` | Người giải |
|---|---|---|
| `src/agents/optimizer.py` | +570/-57 dòng | **R1** |
| `tests/test_cpsat_optimizer.py` | +63/-2 dòng | **R1** |
| `src/api/routes/meal_plans.py` | +150/-17 dòng | **R4** |
| `tests/test_api_meal_plans.py` | +144 dòng | **R4** |

Cả `main` lẫn branch này đều đã đổi cùng vùng code ở các file trên (dấu hiệu có PR khác đã merge vào `main` sau khi branch này tách ra) — nên đây là conflict thật, không tự giải máy móc được, cần người hiểu ý đồ cả hai bên.

---

## Prompt cho R1 (`src/agents/optimizer.py`, `tests/test_cpsat_optimizer.py`)

```
Branch feature/CLN-rule-risk-level-qd5481 (PR #119) đang conflict với main ở
src/agents/optimizer.py và tests/test_cpsat_optimizer.py — cả hai bên đều đã
sửa cùng vùng code kể từ khi branch tách ra.

Việc cần làm:
1. git fetch project main
2. git checkout feature/CLN-rule-risk-level-qd5481
3. git pull project main   (hoặc: git merge project/main)
4. Sẽ báo conflict đúng 4 file, trong đó 2 file này là của tôi (R1):
   src/agents/optimizer.py, tests/test_cpsat_optimizer.py
5. Đọc kỹ CẢ HAI phía thay đổi trước khi giải — branch này có +570/-57 dòng
   trong optimizer.py so với main, không phải conflict 1-2 dòng đơn giản.
   Hiểu đúng ý đồ mỗi bên đã đổi gì (dùng `git log main -- src/agents/optimizer.py`
   và `git log feature/CLN-rule-risk-level-qd5481 -- src/agents/optimizer.py`
   để xem lịch sử đổi độc lập của từng nhánh) trước khi merge tay.
6. Sau khi giải xong: chạy pytest tests/test_cpsat_optimizer.py tests/test_agent.py
   tests/test_graph_e2e.py và toàn bộ test agent liên quan — đảm bảo logic CP-SAT
   không bị vỡ do merge.
7. git add, git commit (không dùng --no-verify), git push project
   feature/CLN-rule-risk-level-qd5481.

Không đụng data/seeds/**, src/api/**, web-next/** trong lúc giải — phần đó
không nằm trong conflict, không cần sửa.
```

## Prompt cho R4 (`src/api/routes/meal_plans.py`, `tests/test_api_meal_plans.py`)

```
Branch feature/CLN-rule-risk-level-qd5481 (PR #119) đang conflict với main ở
src/api/routes/meal_plans.py và tests/test_api_meal_plans.py — cả hai bên đều
đã sửa cùng vùng code kể từ khi branch tách ra.

Việc cần làm:
1. git fetch project main
2. git checkout feature/CLN-rule-risk-level-qd5481
3. git pull project main   (hoặc: git merge project/main)
4. Sẽ báo conflict đúng 4 file, trong đó 2 file này là của tôi (R4):
   src/api/routes/meal_plans.py, tests/test_api_meal_plans.py
5. Đọc kỹ CẢ HAI phía thay đổi trước khi giải — branch này có +150/-17 dòng
   trong meal_plans.py so với main. Dùng `git log main -- src/api/routes/meal_plans.py`
   và `git log feature/CLN-rule-risk-level-qd5481 -- src/api/routes/meal_plans.py`
   để xem hai nhánh đã đổi route này độc lập ra sao trước khi merge tay — đừng
   chỉ chọn 1 bên và bỏ bên kia, cả hai có thể đều cần giữ.
6. Sau khi giải xong: chạy pytest tests/test_api_meal_plans.py tests/test_api_reviews.py
   và toàn bộ test API liên quan đến meal-plans — đảm bảo route không vỡ hành vi
   (đặc biệt là gate RULE-3, kiểm tra 409 khi trùng ngày, versioning/hash).
7. git add, git commit (không dùng --no-verify), git push project
   feature/CLN-rule-risk-level-qd5481.

Không đụng data/seeds/**, src/agents/**, web-next/** trong lúc giải — phần đó
không nằm trong conflict, không cần sửa.
```

---

## Sau khi cả hai xong

- PR #119 sẽ tự chuyển `mergeable: MERGEABLE` khi cả 4 file hết marker `<<<<<<<`.
- Vẫn cần **≥1 review** trước khi merge (`CLAUDE.md` §5) — chưa có ai review PR này tính đến thời điểm viết.
- Phần `data/seeds/**` (dishes/dish_ingredients/dish_unit_conversions/3 file tương tác thuốc-thực phẩm) do R2 đẩy lên tối 18/08 không nằm trong xung đột — không cần R1/R4 động vào.
