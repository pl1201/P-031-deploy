#!/usr/bin/env python3
"""Kiểm tra cấu trúc repo có đúng template AI20K và đủ 10 deliverables không.

Chạy:  python scripts/check_structure.py
CI:    thêm vào .github/workflows/ci.yml — exit 1 nếu có ERROR

Ba nhóm kiểm tra:
  1. ERROR   — sai template hoặc rác lọt vào repo → phải sửa trước khi merge
  2. MISSING — deliverable BTC yêu cầu nhưng chưa có → phải có trước Demo Day
  3. WARN    — chưa chuẩn nhưng chưa chặn
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# --- Thư mục bắt buộc theo template AI20K (chapter-02, quick-start) -------
REQUIRED_DIRS = [
    ("src", "Source code — Deliverable #1"),
    ("src/agents", "LangGraph agent"),
    ("src/api", "FastAPI routes"),
    ("src/models", "Pydantic schemas"),
    ("tests", "Test suite"),
    ("docs", "Tài liệu"),
    ("eval", "Evaluation — Deliverable #10"),
    ("presentation", "Demo Day materials — Deliverable #7"),
    (".github/workflows", "CI/CD"),
]

# --- 10 deliverables và vị trí chuẩn -------------------------------------
# Nguồn: docs/guide/deliverables/checklist.md + README_boilerplate.md
DELIVERABLES = [
    (1, "Source Code", "src", True),
    (2, "README.md", "README.md", True),
    (3, "Architecture Diagram", "docs/architecture_diagram.md", True),
    (4, "AI Logs", ".ai-log", False),
    (5, "Live URL", None, False),  # kiểm tra trong README
    (6, "Video Demo", None, False),  # link trong README
    (7, "Pitch Deck", "presentation/pitch_deck.pptx", False),
    (8, "Weekly Journal", "JOURNAL.md", True),
    (9, "Worklog", "WORKLOG.md", True),
    (10, "Evaluation Evidence", "eval/results/report.md", False),
]

# --- File/thư mục KHÔNG được có trong repo -------------------------------
FORBIDDEN_PATTERNS = [
    ("mnt/", "Đường dẫn sandbox của AI agent lọt vào repo"),
    ("home/claude/", "Đường dẫn sandbox của AI agent lọt vào repo"),
    ("Users/", "Đường dẫn máy cá nhân lọt vào repo"),
    (".env", "File .env chứa secret — chỉ commit .env.example"),
    ("__pycache__", "Cache Python"),
    (".DS_Store", "Rác macOS"),
    ("node_modules/", "Dependencies không được commit"),
    (".venv/", "Virtual environment không được commit"),
]

errors: list[str] = []
missing: list[str] = []
warns: list[str] = []


def tracked_files() -> list[str]:
    try:
        # Bao gồm cả file chưa git add (nhưng không bị .gitignore loại)
        # để chạy được như một bước kiểm tra trước khi commit.
        out = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        )
        return out.stdout.strip().split("\n") if out.stdout.strip() else []
    except (subprocess.CalledProcessError, FileNotFoundError):
        warns.append("Không chạy được `git ls-files` — kiểm tra trên filesystem thay thế")
        return [str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.is_file()]


def check_forbidden(files: list[str]) -> None:
    for f in files:
        for pattern, reason in FORBIDDEN_PATTERNS:
            if pattern == ".env" and (f.endswith(".env.example") or f.endswith(".env.template")):
                continue
            if pattern in f:
                errors.append(f"{f} — {reason}")
                break


def check_dirs(files: list[str]) -> None:
    present = {str(Path(f).parent) for f in files}
    present |= {str(p) for f in files for p in Path(f).parents}
    for d, purpose in REQUIRED_DIRS:
        if d not in present:
            missing.append(f"Thiếu thư mục `{d}/` ({purpose})")


def check_deliverables(files: list[str]) -> None:
    fileset = set(files)
    dirs = {str(p) for f in files for p in Path(f).parents}

    for num, name, path, required_now in DELIVERABLES:
        if path is None:
            continue
        exists = path in fileset or path in dirs or any(f.startswith(path + "/") for f in files)
        if not exists:
            tag = "BẮT BUỘC" if required_now else "cần trước Demo Day"
            missing.append(f"Deliverable #{num} {name}: thiếu `{path}` ({tag})")


def check_duplicates(files: list[str]) -> None:
    """Cùng một file nằm ở hai nơi là dấu hiệu copy nhầm."""
    by_name: dict[str, list[str]] = {}
    for f in files:
        by_name.setdefault(Path(f).name, []).append(f)

    ignore = {"__init__.py", "README.md", "index.md", ".gitkeep"}
    for name, paths in by_name.items():
        if name in ignore or len(paths) < 2:
            continue
        warns.append(f"`{name}` xuất hiện {len(paths)} nơi: {', '.join(paths)}")


def check_pitch_location(files: list[str]) -> None:
    stray = [f for f in files if "pitch" in f.lower() and not f.startswith("presentation/")]
    for f in stray:
        errors.append(f"{f} — pitch deck phải nằm trong `presentation/` (Deliverable #7)")


def check_journal_worklog(files: list[str]) -> None:
    """DEVLOG.md là file làm việc, nhưng BTC chấm theo JOURNAL.md và WORKLOG.md."""
    has_devlog = "DEVLOG.md" in files
    has_journal = "JOURNAL.md" in files
    has_worklog = "WORKLOG.md" in files
    if has_devlog and not (has_journal and has_worklog):
        errors.append(
            "Có DEVLOG.md nhưng thiếu JOURNAL.md/WORKLOG.md — BTC chấm theo đúng hai tên này. "
            "Chạy `python scripts/sync_devlog.py` để sinh tự động."
        )


def main() -> int:
    files = tracked_files()
    print(f"Kiểm tra {len(files)} file được git theo dõi...\n")

    check_forbidden(files)
    check_dirs(files)
    check_deliverables(files)
    check_duplicates(files)
    check_pitch_location(files)
    check_journal_worklog(files)

    if errors:
        print("❌ LỖI — phải sửa trước khi merge")
        for e in errors:
            print(f"   • {e}")
        print()
    if missing:
        print("⬜ THIẾU — deliverable hoặc thư mục chuẩn")
        for m in missing:
            print(f"   • {m}")
        print()
    if warns:
        print("⚠️  CẢNH BÁO")
        for w in warns:
            print(f"   • {w}")
        print()

    if not (errors or missing or warns):
        print("✅ Cấu trúc repo đúng template, đủ deliverables.")
        return 0

    print(f"Tổng: {len(errors)} lỗi · {len(missing)} thiếu · {len(warns)} cảnh báo")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
