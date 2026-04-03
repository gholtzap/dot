"""Keep branches up to date with the remote default branch."""

from __future__ import annotations

import re
from pathlib import Path

import click

from gitdot import git, settings
from gitdot.errors import translate
from gitdot.saving import SavedCommit, save_changes


def should_run(command_name: str, *, cwd: str | Path | None = None) -> bool:
    path = settings.sync_settings_path(cwd=cwd)
    try:
        sync_settings = settings.load_sync_settings(cwd=cwd)
    except settings.SettingsError as exc:
        click.echo(
            f"Warning: Could not load branch sync settings from {path}: {exc}"
        )
        return False
    return sync_settings.enabled and command_name in sync_settings.run_on


def save_before_switch(*, cwd: str | Path | None = None) -> SavedCommit | None:
    if not should_run("switch", cwd=cwd):
        return None
    if not git.status_porcelain(cwd=cwd):
        return None
    return save_changes(cwd=cwd)


def maybe_sync(command_name: str, *, cwd: str | Path | None = None) -> bool:
    if not should_run(command_name, cwd=cwd):
        return True
    return _sync_current_branch(cwd=cwd)


def _sync_current_branch(*, cwd: str | Path | None = None) -> bool:
    branch = git.current_branch(cwd=cwd)
    if not branch:
        return True

    default_ref = git.remote_default_branch(cwd=cwd)
    if not default_ref:
        return True

    _, _, default_branch = default_ref.partition("/")
    if not default_branch or branch == default_branch:
        return True

    fetch_result = git.run(["fetch"], cwd=cwd)
    if not fetch_result.ok:
        return True

    behind = git.commit_count_behind(default_ref, cwd=cwd)
    if behind == 0:
        return True

    rebase_result = git.run(["rebase", default_ref], cwd=cwd)
    if rebase_result.ok:
        click.echo(
            f"This branch was {behind} {_commit_word(behind)} behind {default_ref}. "
            "Rebased automatically."
        )
        return True

    if git.conflicted_files(cwd=cwd) or _looks_like_conflict(rebase_result.stderr):
        git.run(["rebase", "--abort"], cwd=cwd)
        click.echo(
            f"This branch is {behind} {_commit_word(behind)} behind {default_ref}. "
            f"Run 'git rebase {default_ref}'."
        )
        return False

    friendly = translate(rebase_result.stderr)
    raise click.ClickException(friendly or rebase_result.stderr)


def _commit_word(count: int) -> str:
    return "commit" if count == 1 else "commits"


def _looks_like_conflict(stderr: str) -> bool:
    return bool(
        re.search(
            r"CONFLICT|could not apply|Resolve all conflicts manually",
            stderr,
            re.IGNORECASE,
        )
    )
