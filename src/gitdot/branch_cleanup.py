"""Automatic stale branch cleanup."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import fnmatch
from pathlib import Path

import click

from gitdot import git, settings
from gitdot.errors import translate


@dataclass
class RemovedBranch:
    name: str
    remote_ref: str


@dataclass
class CleanupReport:
    removed: list[RemovedBranch]
    warnings: list[str]


def maybe_cleanup(command_name: str, *, cwd: str | Path | None = None) -> None:
    path = settings.branch_settings_path(cwd=cwd)
    try:
        branch_settings = settings.load_branch_settings(cwd=cwd)
    except settings.SettingsError as exc:
        click.echo(
            f"Warning: Could not load branch cleanup settings from {path}: {exc}"
        )
        return

    if not branch_settings.enabled or command_name not in branch_settings.run_on:
        return

    click.echo("Cleaning up stale branches...")
    report = cleanup_stale_branches(branch_settings, cwd=cwd)

    if report.removed:
        for removed in report.removed:
            click.echo(
                f"Removed stale branch '{removed.name}'. It is still available on "
                f"'{removed.remote_ref}'."
            )
    else:
        click.echo("Cleaned up nothing.")

    for warning in report.warnings:
        click.echo(f"Warning: {warning}")


def cleanup_stale_branches(
    branch_settings: settings.BranchSettings,
    *,
    cwd: str | Path | None = None,
) -> CleanupReport:
    fetch_command = "git fetch --all --prune"
    fetch_result = git.run(["fetch", "--all", "--prune"], cwd=cwd)
    if not fetch_result.ok:
        message = translate(fetch_result.stderr) or "Git could not fetch remotes."
        return CleanupReport(
            removed=[],
            warnings=[f"{message} See more details: {fetch_command}"],
        )

    protected_patterns = set(branch_settings.keep_patterns)
    default_branch = git.default_branch(cwd=cwd)
    if default_branch:
        protected_patterns.add(default_branch)

    cutoff = datetime.now().timestamp() - timedelta(
        weeks=branch_settings.after_weeks
    ).total_seconds()

    report = CleanupReport(removed=[], warnings=[])
    current_branch = git.current_branch(cwd=cwd)
    for branch in git.local_branches(cwd=cwd):
        if _is_protected(
            branch.name,
            current_branch=current_branch,
            protected_patterns=protected_patterns,
        ):
            continue

        remote_ref = _remote_ref(branch)
        last_touched = _last_touched(branch.name, remote_ref, cwd=cwd)
        if last_touched >= cutoff:
            continue

        removed = _remove_branch(branch.name, remote_ref, cwd=cwd)
        if isinstance(removed, RemovedBranch):
            report.removed.append(removed)
        else:
            report.warnings.append(removed)

    return report


def _is_protected(
    name: str,
    *,
    current_branch: str,
    protected_patterns: set[str],
) -> bool:
    if name == current_branch:
        return True
    return any(fnmatch.fnmatch(name, pattern) for pattern in protected_patterns)


def _remote_ref(branch: git.LocalBranch) -> str:
    if branch.upstream:
        return branch.upstream
    return f"origin/{branch.name}"


def _last_touched(
    branch_name: str,
    remote_ref: str,
    *,
    cwd: str | Path | None = None,
) -> int:
    times = [
        git.latest_checkout_activity(branch_name, cwd=cwd),
        git.latest_ref_activity(f"refs/heads/{branch_name}", cwd=cwd),
        git.ref_tip_timestamp(branch_name, cwd=cwd),
    ]
    if git.remote_branch_exists(remote_ref, cwd=cwd):
        times.append(git.latest_ref_activity(f"refs/remotes/{remote_ref}", cwd=cwd))
        times.append(git.ref_tip_timestamp(remote_ref, cwd=cwd))
    return max(times)


def _remove_branch(
    branch_name: str,
    remote_ref: str,
    *,
    cwd: str | Path | None = None,
) -> RemovedBranch | str:
    remote_name, remote_branch_name = _split_remote_ref(remote_ref)
    push_command = f"git push {remote_name} {branch_name}:refs/heads/{remote_branch_name}"

    needs_backup_push = True
    if git.remote_branch_exists(remote_ref, cwd=cwd):
        needs_backup_push = not git.is_ancestor(branch_name, remote_ref, cwd=cwd)

    if needs_backup_push:
        push_result = git.run(
            ["push", remote_name, f"{branch_name}:refs/heads/{remote_branch_name}"],
            cwd=cwd,
        )
        if not push_result.ok:
            message = translate(push_result.stderr) or "Git could not back up the branch."
            return (
                f"Could not remove stale branch '{branch_name}' because backing it up "
                f"to '{remote_ref}' failed. {message} See more details: {push_command}"
            )

    delete_command = f"git branch -D {branch_name}"
    delete_result = git.run(["branch", "-D", branch_name], cwd=cwd)
    if not delete_result.ok:
        message = translate(delete_result.stderr) or delete_result.stderr
        return (
            f"Could not remove stale branch '{branch_name}' after backing it up. "
            f"{message} See more details: {delete_command}"
        )

    return RemovedBranch(name=branch_name, remote_ref=remote_ref)


def _split_remote_ref(remote_ref: str) -> tuple[str, str]:
    remote_name, _, branch_name = remote_ref.partition("/")
    if branch_name:
        return remote_name, branch_name
    return "origin", remote_ref
