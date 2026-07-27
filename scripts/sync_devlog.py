#!/usr/bin/env python3
"""Sinh JOURNAL.md (Deliverable #8) và WORKLOG.md (Deliverable #9) từ DEVLOG.md + git log.

Vì sao cần script này:
  Đội ghi nhật ký vào một file duy nhất `DEVLOG.md` cho tiện. Nhưng BTC chấm
  theo đúng hai tên `JOURNAL.md` và `WORKLOG.md` ở gốc repo. Script này giữ
  DEVLOG.md làm nguồn sự thật duy nhất và sinh ra hai file kia — không phải
  chép tay ba lần.

Chạy:  python scripts/sync_devlog.py
Nên chạy: mỗi cuối tuần, và bắt buộc trước khi nộp bài.
"""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

if sys.stdout.encoding is None or sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
DEVLOG = ROOT / "DEVLOG.md"
JOURNAL = ROOT / "JOURNAL.md"
WORKLOG = ROOT / "WORKLOG.md"

BANNER = (
    "> ⚙️ File này được sinh tự động từ `DEVLOG.md` bằng `scripts/sync_devlog.py`.\n"
    "> Đừng sửa trực tiếp — hãy sửa `DEVLOG.md` rồi chạy lại script.\n"
)


def read_devlog() -> str:
    if not DEVLOG.exists():
        raise SystemExit("Không tìm thấy DEVLOG.md ở gốc repo.")
    return DEVLOG.read_text(encoding="utf-8")


def extract_section(text: str, heading_pattern: str) -> str:
    """Lấy nội dung một mục `## N. Tiêu đề` cho tới mục `##` kế tiếp."""
    m = re.search(rf"^## {heading_pattern}.*?$", text, re.MULTILINE)
    if not m:
        return ""
    start = m.end()
    nxt = re.search(r"^## ", text[start:], re.MULTILINE)
    return text[start : start + nxt.start()].strip() if nxt else text[start:].strip()


def git_log() -> list[str]:
    try:
        out = subprocess.run(
            [
                "git", "log",
                "--date=short",
                "--pretty=format:| %ad | %an | %s |",
            ],
            cwd=ROOT, capture_output=True, text=True, check=True,
        )
        return out.stdout.strip().split("\n") if out.stdout.strip() else []
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def git_stats() -> str:
    try:
        authors = subprocess.run(
            ["git", "shortlog", "-sn", "--all"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
        if not authors:
            return ""
        rows = ["| Thành viên | Số commit |", "|---|---|"]
        for line in authors.split("\n"):
            parts = line.strip().split("\t")
            if len(parts) == 2:
                rows.append(f"| {parts[1]} | {parts[0]} |")
        return "\n".join(rows)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def build_journal(devlog: str) -> str:
    weekly = extract_section(devlog, r"\d+\.\s*Tổng kết tuần")
    decisions = extract_section(devlog, r"\d+\.\s*Quyết định kỹ thuật")
    incidents = extract_section(devlog, r"\d+\.\s*Sự cố")

    parts = [
        "# JOURNAL — Nhật ký phát triển theo tuần",
        "",
        BANNER,
        f"> Cập nhật lần cuối: {datetime.now():%d/%m/%Y %H:%M}",
        "",
        "---",
        "",
        "## Tổng kết theo tuần",
        "",
        weekly or "_Chưa có dữ liệu — điền vào mục 'Tổng kết tuần' trong DEVLOG.md_",
        "",
        "---",
        "",
        "## Quyết định kỹ thuật",
        "",
        decisions or "_Chưa có_",
    ]
    if incidents and not incidents.startswith("| | | |"):
        parts += ["", "---", "", "## Sự cố & bài học", "", incidents]
    return "\n".join(parts) + "\n"


def build_worklog(devlog: str) -> str:
    daily = extract_section(devlog, r"\d+\.\s*Nhật ký hằng ngày")
    commits = git_log()
    stats = git_stats()

    parts = [
        "# WORKLOG — Nhật ký công việc",
        "",
        BANNER,
        f"> Cập nhật lần cuối: {datetime.now():%d/%m/%Y %H:%M} · {len(commits)} commit",
        "",
        "---",
        "",
        "## 1. Đóng góp theo thành viên",
        "",
        stats or "_Chưa có commit_",
        "",
        "---",
        "",
        "## 2. Nhật ký công việc hằng ngày",
        "",
        daily or "_Chưa có dữ liệu_",
        "",
        "---",
        "",
        "## 3. Lịch sử commit",
        "",
        "| Ngày | Người | Nội dung |",
        "|---|---|---|",
    ]
    parts += commits if commits else ["| — | — | _chưa có commit_ |"]
    return "\n".join(parts) + "\n"


def main() -> None:
    devlog = read_devlog()

    JOURNAL.write_text(build_journal(devlog), encoding="utf-8")
    WORKLOG.write_text(build_worklog(devlog), encoding="utf-8")

    print(f"✅ Đã sinh {JOURNAL.name} ({JOURNAL.stat().st_size:,} bytes)")
    print(f"✅ Đã sinh {WORKLOG.name} ({WORKLOG.stat().st_size:,} bytes)")
    print("\nNhớ commit cả hai file — BTC chấm Deliverable #8 và #9 theo đúng hai tên này.")


if __name__ == "__main__":
    main()
