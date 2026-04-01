"""Subprocess wrapper for running git commands."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

import click


@dataclass
class GitResult:
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


class StatusEntry(NamedTuple):
    code: str  # two-character status code (e.g., "M ", "??", "A ")
    path: str


def run(
    args: list[str],
    *,
    capture: bool = True,
    cwd: str | Path | None = None,
) -> GitResult:
    """Run a git command and return the result.

    If capture=False, stdout/stderr go directly to the terminal.
    """
    kwargs: dict = {
        "cwd": cwd,
    }
    if capture:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE
        kwargs["text"] = True

    result = subprocess.run(["git"] + args, **kwargs)

    if capture:
        return GitResult(
            returncode=result.returncode,
            stdout=(result.stdout or "").strip(),
            stderr=(result.stderr or "").strip(),
        )
    return GitResult(returncode=result.returncode, stdout="", stderr="")


def run_or_fail(
    args: list[str],
    *,
    cwd: str | Path | None = None,
) -> GitResult:
    """Run a git command; raise ClickException with a friendly message on failure."""
    from gitdot.errors import translate

    result = run(args, cwd=cwd)
    if not result.ok:
        friendly = translate(result.stderr)
        raise click.ClickException(friendly or result.stderr)
    return result


def current_branch(*, cwd: str | Path | None = None) -> str:
    """Return the current branch name, or empty string if detached."""
    result = run(["branch", "--show-current"], cwd=cwd)
    return result.stdout


def has_upstream(*, cwd: str | Path | None = None) -> bool:
    """Check if the current branch has an upstream configured."""
    result = run(["rev-parse", "--abbrev-ref", "@{u}"], cwd=cwd)
    return result.ok


def upstream_name(*, cwd: str | Path | None = None) -> str:
    """Return the upstream ref (e.g., 'origin/main'), or empty string."""
    result = run(["rev-parse", "--abbrev-ref", "@{u}"], cwd=cwd)
    return result.stdout if result.ok else ""


def is_repo(*, cwd: str | Path | None = None) -> bool:
    """Check if the current directory is inside a git repository."""
    result = run(["rev-parse", "--is-inside-work-tree"], cwd=cwd)
    return result.ok and result.stdout == "true"


def repo_root(*, cwd: str | Path | None = None) -> Path:
    """Return the root directory of the git repository."""
    result = run_or_fail(["rev-parse", "--show-toplevel"], cwd=cwd)
    return Path(result.stdout)


def status_porcelain(*, cwd: str | Path | None = None) -> list[StatusEntry]:
    """Return structured status entries from git status --porcelain."""
    result = run(["status", "--porcelain"], cwd=cwd)
    if not result.ok or not result.stdout:
        return []
    entries = []
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        code = line[:2]
        path = line[3:]
        # Handle renames: "R  old -> new"
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        entries.append(StatusEntry(code=code, path=path))
    return entries


def diff_stat_summary(*, staged: bool = True, cwd: str | Path | None = None) -> str:
    """Return a human-readable summary of changes (e.g., 'modified 3 files, added 1 file')."""
    args = ["diff", "--name-status"]
    if staged:
        args.append("--cached")
    result = run(args, cwd=cwd)
    if not result.ok or not result.stdout:
        return ""

    counts: dict[str, int] = {}
    labels = {
        "M": "modified",
        "A": "added",
        "D": "deleted",
        "R": "renamed",
        "C": "copied",
    }
    for line in result.stdout.splitlines():
        parts = line.split("\t", 1)
        if not parts:
            continue
        status_char = parts[0][0]  # first char handles R100, C100, etc.
        label = labels.get(status_char, "changed")
        counts[label] = counts.get(label, 0) + 1

    if not counts:
        return ""

    parts_list = []
    for label in ["modified", "added", "deleted", "renamed", "copied", "changed"]:
        n = counts.get(label, 0)
        if n > 0:
            noun = "file" if n == 1 else "files"
            parts_list.append(f"{label} {n} {noun}")
    return ", ".join(parts_list)


def commit_count_ahead(*, cwd: str | Path | None = None) -> int:
    """Number of local commits ahead of upstream."""
    result = run(["rev-list", "@{u}..HEAD", "--count"], cwd=cwd)
    return int(result.stdout) if result.ok and result.stdout.isdigit() else 0


def commit_count_behind(*, cwd: str | Path | None = None) -> int:
    """Number of upstream commits not yet in local."""
    result = run(["rev-list", "HEAD..@{u}", "--count"], cwd=cwd)
    return int(result.stdout) if result.ok and result.stdout.isdigit() else 0


def is_ancestor(
    ancestor: str,
    descendant: str = "HEAD",
    *,
    cwd: str | Path | None = None,
) -> bool:
    """Return True if ancestor is reachable from descendant."""
    result = run(["merge-base", "--is-ancestor", ancestor, descendant], cwd=cwd)
    return result.returncode == 0


def conflicted_files(*, cwd: str | Path | None = None) -> list[str]:
    """Return list of files with merge conflicts."""
    result = run(["diff", "--name-only", "--diff-filter=U"], cwd=cwd)
    if not result.ok or not result.stdout:
        return []
    return result.stdout.splitlines()
