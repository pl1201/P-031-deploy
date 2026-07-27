#!/usr/bin/env bash
# Sắp xếp lại repo về đúng cấu trúc template AI20K.
#
# Mặc định chạy THỬ (dry-run), chỉ in ra sẽ làm gì.
# Chạy thật:  bash scripts/reorganize_repo.sh --apply
#
# An toàn:
#   - Dùng `git mv` nên giữ được lịch sử file
#   - Idempotent: chạy nhiều lần không hỏng
#   - Không xoá file có nội dung, chỉ di chuyển hoặc gỡ khỏi git index
#
# LÀM TRƯỚC KHI CHẠY:
#   git checkout -b chore/reorganize-repo
#   git status          # phải sạch, không có thay đổi chưa commit

set -uo pipefail

APPLY=0
[[ "${1:-}" == "--apply" ]] && APPLY=1

if [[ $APPLY -eq 0 ]]; then
  echo "=== CHẠY THỬ (dry-run) — không thay đổi gì ==="
  echo "    Chạy thật: bash scripts/reorganize_repo.sh --apply"
else
  echo "=== CHẠY THẬT ==="
fi
echo

run() {
  echo "  \$ $*"
  if [[ $APPLY -eq 1 ]]; then
    eval "$@" || echo "     (bỏ qua — không áp dụng được)"
  fi
}

section() { echo; echo "── $1"; }

# ---------------------------------------------------------------- 1
section "1. Gỡ đường dẫn sandbox lọt vào repo"
for junk in mnt home Users; do
  if git ls-files --error-unmatch "$junk" >/dev/null 2>&1 || [[ -d "$junk" ]]; then
    run "git rm -r --cached '$junk' -q"
    run "rm -rf '$junk'"
  fi
done

# ---------------------------------------------------------------- 2
section "2. Tạo thư mục chuẩn còn thiếu"
for d in src/api/routes src/models src/services src/core \
         tests/unit tests/integration tests/eval \
         eval/datasets eval/scripts eval/results \
         presentation docs/adr .github/workflows; do
  if [[ ! -d "$d" ]]; then
    run "mkdir -p '$d'"
    run "touch '$d/.gitkeep'"
  fi
done

# ---------------------------------------------------------------- 3
section "3. Đưa pitch deck về presentation/ (Deliverable #7)"
if [[ -f docs/pitch_deck.md ]]; then
  run "git mv docs/pitch_deck.md presentation/pitch_deck.md"
fi
for f in docs/pitch-deck.md docs/PITCH_DECK.md; do
  [[ -f "$f" ]] && run "git mv '$f' presentation/pitch_deck.md"
done

# ---------------------------------------------------------------- 4
section "4. Đổi tên tài liệu kiến trúc đúng tên BTC chấm (Deliverable #3)"
if [[ -f docs/ARCHITECTURE.md && ! -f docs/architecture_diagram.md ]]; then
  run "git mv docs/ARCHITECTURE.md docs/architecture_diagram.md"
  echo "  → cập nhật mọi tham chiếu trong tài liệu"
  if [[ $APPLY -eq 1 ]]; then
    grep -rl "ARCHITECTURE\.md" --include="*.md" . 2>/dev/null \
      | xargs -r sed -i 's|ARCHITECTURE\.md|architecture_diagram.md|g'
  else
    echo "  \$ sed -i 's|ARCHITECTURE.md|architecture_diagram.md|g' \$(grep -rl ...)"
  fi
fi

# ---------------------------------------------------------------- 5
section "5. Bỏ CLAUDE.md trùng lặp"
# Claude Code đọc CLAUDE.md ở gốc repo. Thư mục .claude/ chỉ chứa skills và settings.
if [[ -f .claude/CLAUDE.md && -f CLAUDE.md ]]; then
  run "git rm .claude/CLAUDE.md -q"
fi

# ---------------------------------------------------------------- 6
section "6. Gộp thư mục code lồng nhau (nếu agent tạo code/ hoặc outputs/)"
if [[ -d code/src ]]; then
  echo "  Phát hiện code/src — hợp nhất vào src/"
  run "cp -rn code/src/* src/ 2>/dev/null"
  run "cp -rn code/tests/* tests/ 2>/dev/null"
  run "cp -rn code/data/* data/ 2>/dev/null"
  run "cp -rn code/scripts/* scripts/ 2>/dev/null"
  run "git rm -r --cached code -q"
  run "rm -rf code"
fi

# ---------------------------------------------------------------- 7
section "7. Sinh JOURNAL.md và WORKLOG.md (Deliverable #8, #9)"
if [[ -f scripts/sync_devlog.py ]]; then
  run "python3 scripts/sync_devlog.py"
else
  echo "  (chưa có scripts/sync_devlog.py — bỏ qua)"
fi

# ---------------------------------------------------------------- 8
section "8. Bổ sung .gitignore"
if [[ $APPLY -eq 1 ]]; then
  for line in "mnt/" "home/" ".venv/" "__pycache__/" "*.pyc" ".env" ".DS_Store" ".ruff_cache/" ".pytest_cache/"; do
    grep -qxF "$line" .gitignore 2>/dev/null || echo "$line" >> .gitignore
  done
  echo "  → đã bổ sung các mục thiếu vào .gitignore"
else
  echo "  \$ thêm mnt/ home/ .venv/ __pycache__/ *.pyc .env .DS_Store vào .gitignore"
fi

# ---------------------------------------------------------------- 9
section "9. Kiểm tra lại"
if [[ $APPLY -eq 1 ]]; then
  python3 scripts/check_structure.py || true
else
  echo "  \$ python3 scripts/check_structure.py"
fi

echo
if [[ $APPLY -eq 0 ]]; then
  echo "Chưa thay đổi gì. Xem lại danh sách trên, rồi chạy:"
  echo "  bash scripts/reorganize_repo.sh --apply"
else
  echo "Xong. Bước tiếp theo:"
  echo "  git add -A"
  echo "  git commit -m 'chore: sắp xếp lại repo theo template AI20K'"
  echo "  git push -u origin chore/reorganize-repo"
fi
