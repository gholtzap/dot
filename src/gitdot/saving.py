"""Shared save flow for commands that stage and commit changes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from gitdot import git
from gitdot.undo import push_entry


@dataclass
class SavedCommit:
    short_hash: str
    message: str


def save_changes(
    *,
    paths: list[str] | None = None,
    message: str | None = None,
    cwd: str | Path | None = None,
) -> SavedCommit | None:
    if paths:
        git.run_or_fail(["add"] + paths, cwd=cwd)
    else:
        git.run_or_fail(["add", "-A"], cwd=cwd)

    staged_result = git.run(["diff", "--cached", "--quiet"], cwd=cwd)
    if staged_result.ok:
        return None

    final_message = message or auto_message(cwd=cwd)
    git.run_or_fail(["commit", "-m", final_message], cwd=cwd)

    full_hash_result = git.run(["rev-parse", "HEAD"], cwd=cwd)
    if full_hash_result.ok:
        push_entry(full_hash_result.stdout, final_message)

    short_hash_result = git.run(["rev-parse", "--short", "HEAD"], cwd=cwd)
    short_hash = short_hash_result.stdout if short_hash_result.ok else "?"
    return SavedCommit(short_hash=short_hash, message=final_message)


def auto_message(*, cwd: str | Path | None = None) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    summary = git.diff_stat_summary(staged=True, cwd=cwd)
    if summary:
        return f"{timestamp} -- {summary}"
    return timestamp
