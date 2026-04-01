"""dot save -- stage and commit in one step."""

from __future__ import annotations

from datetime import datetime

import click

from gitdot import git, dotdir


@click.command()
@click.argument("args", nargs=-1)
def save(args: tuple[str, ...]) -> None:
    """Stage and commit changes in one step.

    Usage:
        dot save                        Save all changes with auto-generated message
        dot save "fix login bug"        Save all changes with a message
        dot save src/foo.py             Save specific file with auto-message
        dot save src/foo.py "fix foo"   Save specific file with a message
    """
    dotdir.ensure()

    paths, message = _parse_args(args)

    # Check for changes before staging
    status = git.status_porcelain()
    if not status and not paths:
        click.echo("There are no changes to save.")
        return

    # Stage
    if paths:
        git.run_or_fail(["add"] + paths)
    else:
        git.run_or_fail(["add", "-A"])

    # Check if anything is staged after adding
    staged_result = git.run(["diff", "--cached", "--quiet"])
    if staged_result.ok:
        click.echo("There are no changes to save.")
        return

    # Generate message if not provided
    if message is None:
        message = _auto_message()

    # Commit
    git.run_or_fail(["commit", "-m", message])

    # Get the commit hash for the undo stack and confirmation
    result = git.run(["rev-parse", "--short", "HEAD"])
    short_hash = result.stdout if result.ok else "?"

    # Push to undo stack
    full_hash_result = git.run(["rev-parse", "HEAD"])
    if full_hash_result.ok:
        from gitdot.undo import push_entry

        push_entry(full_hash_result.stdout, message)

    click.echo(f"Saved: {short_hash} {message}")


def _parse_args(args: tuple[str, ...]) -> tuple[list[str], str | None]:
    """Split args into (file paths, optional message).

    The last arg is the message if it does not correspond to an existing file path.
    Everything else is treated as file paths.
    """
    if not args:
        return [], None

    args_list = list(args)

    if len(args_list) == 1:
        if git.pathspec_has_changes(args_list[0]):
            return args_list, None
        return [], args_list[0]

    if git.pathspec_has_changes(args_list[-1]):
        return args_list, None

    return args_list[:-1], args_list[-1]


def _auto_message() -> str:
    """Generate an auto commit message: timestamp + diff summary."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    summary = git.diff_stat_summary(staged=True)
    if summary:
        return f"{timestamp} -- {summary}"
    return timestamp
