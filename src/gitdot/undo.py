"""dot undo -- revert saves with a persistent undo stack."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import click

from gitdot import git, dotdir

MAX_STACK_SIZE = 50
STACK_FILE = "undo_stack.json"


def _stack_path(*, cwd: str | Path | None = None) -> Path:
    return dotdir.dot_path(cwd=cwd) / STACK_FILE


def _read_stack(*, cwd: str | Path | None = None) -> list[dict]:
    path = _stack_path(cwd=cwd)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        return data.get("entries", [])
    except (json.JSONDecodeError, KeyError):
        return []


def _write_stack(entries: list[dict], *, cwd: str | Path | None = None) -> None:
    path = _stack_path(cwd=cwd)
    data = {"version": 1, "entries": entries}
    path.write_text(json.dumps(data, indent=2) + "\n")


def push_entry(
    commit_hash: str, message: str, entry_type: str = "save"
) -> None:
    """Add an entry to the undo stack."""
    dotdir.ensure()
    branch = git.current_branch()
    entries = _read_stack()
    entry = {
        "commit_hash": commit_hash,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": entry_type,
    }
    if branch:
        entry["branch"] = branch
    entries.append(entry)
    # Trim to max size
    if len(entries) > MAX_STACK_SIZE:
        entries = entries[-MAX_STACK_SIZE:]
    _write_stack(entries)


@click.command()
@click.argument("count", default=1, type=int)
def undo(count: int) -> None:
    """Undo the last save(s) by reverting commits.

    Usage:
        dot undo       Undo the last save
        dot undo 3     Undo the last 3 saves
    """
    dotdir.ensure()
    entries = _read_stack()

    if not entries:
        click.echo("Nothing to undo.")
        return

    if count < 1:
        click.echo("Count must be at least 1.")
        return

    available = len(entries)
    if count > available:
        click.echo(
            f"Only {available} save(s) in the undo stack. "
            f"Run 'dot undo {available}' to undo all of them."
        )
        return

    # Pop entries from the end (newest first)
    to_undo = entries[-count:]
    current_branch = git.current_branch()
    for entry in reversed(to_undo):
        error = _undo_block_reason(entry, current_branch)
        if error:
            raise click.ClickException(error)

    remaining = entries[:-count]
    reverted = 0
    for entry in reversed(to_undo):
        result = git.run(
            ["revert", entry["commit_hash"], "--no-edit"],
        )
        if not result.ok:
            # Push back the entries we couldn't revert
            failed_entries = to_undo[: len(to_undo) - reverted]
            _write_stack(remaining + failed_entries)

            files = git.conflicted_files()
            if files:
                click.echo("Undo stopped because of conflicts in these files:")
                for f in files:
                    click.echo(f"  {f}")
                click.echo()
                click.echo(
                    "Open each file, look for the <<<< and >>>> markers, "
                    "choose which version to keep, save the file, then run:"
                )
                click.echo("  git revert --continue")
            else:
                from gitdot.errors import translate

                friendly = translate(result.stderr)
                click.echo(friendly or result.stderr)
            raise SystemExit(1)
        reverted += 1

    _write_stack(remaining)

    noun = "save" if reverted == 1 else "saves"
    click.echo(f"Undone: {reverted} {noun} reverted.")


def _undo_block_reason(entry: dict, current_branch: str) -> str | None:
    entry_branch = entry.get("branch", "")
    if entry_branch and entry_branch != current_branch:
        return (
            f"The last save was made on '{entry_branch}'. "
            f"Switch back to '{entry_branch}' to undo it."
        )

    if not git.is_ancestor(entry["commit_hash"]):
        return (
            "The last save is not part of the current branch history anymore. "
            "Switch to the branch where you made it to undo it."
        )

    return None
