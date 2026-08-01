#!/usr/bin/env python3
"""Extract user prompts from local Codex transcripts into the AI log.

This covers Codex surfaces that persist sessions under ~/.codex/sessions,
including the VS Code chat UI, even when project lifecycle hooks do not fire.
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


VN_TZ = timezone(timedelta(hours=7))
CODEX_SESSIONS = Path.home() / ".codex" / "sessions"


if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def git(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def normalize_path(value: str) -> str:
    return value.strip().lower().replace("/", "\\").rstrip("\\")


def path_matches_repo(value: str, repo_root: str) -> bool:
    path = normalize_path(value)
    if not path or not repo_root:
        return False
    return path == repo_root or path.startswith(repo_root + "\\") or repo_root.startswith(path + "\\")


def parse_timestamp(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def logged_keys(log_dir: Path) -> tuple[set[str], set[tuple[str, str]]]:
    entry_ids: set[str] = set()
    turns: set[tuple[str, str]] = set()
    files = [log_dir / "session.jsonl"]
    archive = log_dir / "archive"
    if archive.exists():
        files.extend(archive.glob("*.jsonl"))

    for path in files:
        if not path.exists():
            continue
        try:
            with open(path, encoding="utf-8-sig") as stream:
                for line in stream:
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    entry_id = str(entry.get("entry_id", ""))
                    if entry_id:
                        entry_ids.add(entry_id)
                    session_id = str(entry.get("session_id", ""))
                    turn_id = str(entry.get("turn_id", ""))
                    if session_id and turn_id:
                        turns.add((session_id, turn_id))
        except OSError:
            continue
    return entry_ids, turns


def read_transcript(path: Path) -> tuple[set[str], list[dict]]:
    session_id = ""
    originator = "codex"
    model = "codex"
    turn_id = ""
    cwds: set[str] = set()
    messages: list[dict] = []

    try:
        stream = open(path, encoding="utf-8")
    except OSError:
        return cwds, messages

    with stream:
        for line_number, line in enumerate(stream, start=1):
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue

            payload = item.get("payload") or {}
            item_type = item.get("type")
            payload_type = payload.get("type")

            if item_type == "session_meta":
                session_id = str(payload.get("id") or payload.get("session_id") or path.stem)
                originator = str(payload.get("originator") or payload.get("source") or "codex")
                cwd = payload.get("cwd")
                if isinstance(cwd, str):
                    cwds.add(cwd)
                continue

            if item_type == "turn_context":
                turn_id = str(payload.get("turn_id") or turn_id)
                cwd = payload.get("cwd")
                if isinstance(cwd, str):
                    cwds.add(cwd)
                for root in payload.get("workspace_roots") or []:
                    if isinstance(root, str):
                        cwds.add(root)
                continue

            if item_type != "event_msg":
                continue

            if payload_type == "task_started":
                turn_id = str(payload.get("turn_id") or turn_id)
                continue

            if payload_type == "thread_settings_applied":
                settings = payload.get("thread_settings") or {}
                model = str(settings.get("model") or model)
                cwd = settings.get("cwd")
                if isinstance(cwd, str):
                    cwds.add(cwd)
                continue

            if payload_type != "user_message":
                continue

            prompt = payload.get("message")
            if not isinstance(prompt, str) or len(prompt.strip()) < 2:
                continue

            client_id = str(payload.get("client_id") or "")
            timestamp = str(item.get("timestamp") or "")
            message_key = client_id or timestamp or f"line-{line_number}"
            messages.append(
                {
                    "session_id": session_id or path.stem,
                    "turn_id": turn_id,
                    "message_key": message_key,
                    "timestamp": timestamp,
                    "model": model,
                    "originator": originator,
                    "prompt": prompt.strip(),
                }
            )

    return cwds, messages


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract prompts from local Codex session transcripts.")
    parser.add_argument("--auto", action="store_true")
    parser.add_argument("--hours", type=int, default=24)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-repo-filter", action="store_true")
    args = parser.parse_args()

    if not CODEX_SESSIONS.exists():
        print(
            f"[codex-log] No Codex sessions directory found: {CODEX_SESSIONS}",
            file=sys.stderr,
        )
        return

    repo_root = normalize_path(str(Path.cwd()))
    cutoff = None
    if not args.all:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=args.hours)

    log_dir = Path(os.environ.get("AI_LOG_DIR", ".ai-log"))
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "session.jsonl"
    entry_ids, turns = logged_keys(log_dir)

    repo_url = git("remote", "get-url", "origin")
    repo = repo_url.rstrip("/").split("/")[-1].removesuffix(".git")
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    commit = git("rev-parse", "--short", "HEAD")
    student = git("config", "user.email") or os.environ.get("USERNAME", os.environ.get("USER", "unknown"))

    new_entries: list[dict] = []
    for transcript in CODEX_SESSIONS.rglob("rollout-*.jsonl"):
        if cutoff:
            modified = datetime.fromtimestamp(transcript.stat().st_mtime, timezone.utc)
            if modified < cutoff:
                continue

        cwds, messages = read_transcript(transcript)
        if not args.no_repo_filter and not any(path_matches_repo(cwd, repo_root) for cwd in cwds):
            continue

        for message in messages:
            timestamp = parse_timestamp(message["timestamp"])
            if cutoff and timestamp and timestamp < cutoff:
                continue

            entry_id = f"codex-{message['session_id']}-{message['message_key']}"
            turn_key = (message["session_id"], message["turn_id"])
            if entry_id in entry_ids:
                continue
            if message["turn_id"] and turn_key in turns:
                continue

            local_timestamp = timestamp.astimezone(VN_TZ).isoformat() if timestamp else datetime.now(VN_TZ).isoformat()
            entry = {
                "ts": local_timestamp,
                "tool": "codex",
                "event": "UserPrompt",
                "entry_id": entry_id,
                "session_id": message["session_id"],
                "turn_id": message["turn_id"],
                "model": message["model"],
                "client": message["originator"],
                "repo": repo or Path.cwd().name,
                "branch": branch,
                "commit": commit,
                "student": student,
                "prompt": message["prompt"][:1000],
                "response_summary": "",
            }
            new_entries.append(entry)
            entry_ids.add(entry_id)
            if message["turn_id"]:
                turns.add(turn_key)

    new_entries.sort(key=lambda entry: entry["ts"])
    scope = "all" if args.all else f"{args.hours}h"

    if not new_entries:
        print(
            f"[codex-log] No new prompts (repo={repo_root}, window={scope}).",
            file=sys.stderr,
        )
        return

    if args.dry_run:
        print(f"[codex-log] Would log {len(new_entries)} prompt(s).")
        return

    with open(log_file, "a", encoding="utf-8") as stream:
        for entry in new_entries:
            stream.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(
        f"[codex-log] Logged {len(new_entries)} prompt(s) from Codex sessions.",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
