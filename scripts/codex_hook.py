#!/usr/bin/env python3
"""Log Codex UserPromptSubmit hook events without affecting Codex output."""

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    payload = sys.stdin.buffer.read()
    if not payload:
        return 0

    repo_root = Path(__file__).resolve().parents[1]
    logger = repo_root / "scripts" / "log_hook.py"
    env = os.environ.copy()
    env.setdefault("AI_LOG_DIR", str(repo_root / ".ai-log"))

    try:
        subprocess.run(
            [sys.executable, str(logger), "--tool=codex"],
            input=payload,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=repo_root,
            env=env,
            timeout=10,
            check=False,
        )
    except Exception:
        # Logging must never block or alter a Codex turn.
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
