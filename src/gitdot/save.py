"""dot save -- stage and commit in one step."""

from __future__ import annotations

import click

from gitdot import branch_cleanup, dotdir, git
from gitdot.saving import save_changes


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
        branch_cleanup.maybe_cleanup("save")
        return

    saved = save_changes(paths=paths or None, message=message)
    if saved is None:
        click.echo("There are no changes to save.")
        branch_cleanup.maybe_cleanup("save")
        return

    click.echo(f"Saved: {saved.short_hash} {saved.message}")
    branch_cleanup.maybe_cleanup("save")


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
