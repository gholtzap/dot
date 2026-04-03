"""Subprocess wrapper for running git commands."""

from __future__ import annotations

import re
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


@dataclass
class LocalBranch:
    name: str
    upstream: str
    tip_timestamp: int


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


def local_branch_exists(name: str, *, cwd: str | Path | None = None) -> bool:
    """Return True if the local branch exists."""
    result = run(["show-ref", "--verify", "--quiet", f"refs/heads/{name}"], cwd=cwd)
    return result.ok


def remotes(*, cwd: str | Path | None = None) -> list[str]:
    """Return configured git remotes."""
    result = run(["remote"], cwd=cwd)
    if not result.ok or not result.stdout:
        return []
    return result.stdout.splitlines()


def default_branch(*, cwd: str | Path | None = None) -> str:
    """Return the repo default branch name when git can determine it."""
    remote_names = remotes(cwd=cwd)
    ordered = ["origin"] + [name for name in remote_names if name != "origin"]
    for remote_name in ordered:
        result = run(
            ["symbolic-ref", "--quiet", "--short", f"refs/remotes/{remote_name}/HEAD"],
            cwd=cwd,
        )
        if result.ok and result.stdout:
            _, _, branch = result.stdout.partition("/")
            if branch:
                return branch

    for candidate in ("main", "master"):
        if local_branch_exists(candidate, cwd=cwd):
            return candidate

    return ""


def local_branches(*, cwd: str | Path | None = None) -> list[LocalBranch]:
    """Return local branches with upstream and tip timestamp data."""
    result = run(
        [
            "for-each-ref",
            "--format=%(refname:short)\t%(upstream:short)\t%(committerdate:unix)",
            "refs/heads",
        ],
        cwd=cwd,
    )
    if not result.ok or not result.stdout:
        return []

    branches = []
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        name, upstream, tip_timestamp = parts
        branches.append(
            LocalBranch(
                name=name,
                upstream=upstream,
                tip_timestamp=int(tip_timestamp) if tip_timestamp.isdigit() else 0,
            )
        )
    return branches


def remote_branch_exists(remote_ref: str, *, cwd: str | Path | None = None) -> bool:
    """Return True if the remote-tracking branch exists locally."""
    result = run(
        ["show-ref", "--verify", "--quiet", f"refs/remotes/{remote_ref}"],
        cwd=cwd,
    )
    return result.ok


def matching_remote_branches(name: str, *, cwd: str | Path | None = None) -> list[str]:
    """Return remote-tracking branches whose branch name matches the given name."""
    result = run(["for-each-ref", "--format=%(refname:short)", "refs/remotes"], cwd=cwd)
    if not result.ok or not result.stdout:
        return []
    matches = []
    suffix = f"/{name}"
    for ref in result.stdout.splitlines():
        if ref.endswith("/HEAD"):
            continue
        if ref.endswith(suffix):
            matches.append(ref)
    return matches


def latest_ref_activity(ref: str, *, cwd: str | Path | None = None) -> int:
    """Return the latest reflog timestamp for a ref, or 0 if unavailable."""
    result = run(
        ["reflog", "show", "--date=unix", "--format=%gd", "-n", "1", ref],
        cwd=cwd,
    )
    if not result.ok or not result.stdout:
        return 0
    return _selector_timestamp(result.stdout.splitlines()[0])


def latest_checkout_activity(branch: str, *, cwd: str | Path | None = None) -> int:
    """Return the latest time HEAD was moved to the given branch."""
    result = run(
        ["reflog", "show", "--date=unix", "--format=%gd%x09%gs", "HEAD"],
        cwd=cwd,
    )
    if not result.ok or not result.stdout:
        return 0

    pattern = re.compile(rf"^checkout: moving from .+ to {re.escape(branch)}$")
    for line in result.stdout.splitlines():
        selector, _, subject = line.partition("\t")
        if pattern.match(subject):
            return _selector_timestamp(selector)
    return 0


def ref_tip_timestamp(ref: str, *, cwd: str | Path | None = None) -> int:
    """Return the tip commit timestamp for a ref, or 0 if unavailable."""
    result = run(["log", "-1", "--format=%ct", ref], cwd=cwd)
    return int(result.stdout) if result.ok and result.stdout.isdigit() else 0


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


def pathspec_has_changes(pathspec: str, *, cwd: str | Path | None = None) -> bool:
    """Return True if the pathspec matches changed files."""
    result = run(["status", "--porcelain", "--", pathspec], cwd=cwd)
    return result.ok and bool(result.stdout)


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


def _selector_timestamp(selector: str) -> int:
    match = re.search(r"\{(\d+)\}$", selector.strip())
    return int(match.group(1)) if match else 0
