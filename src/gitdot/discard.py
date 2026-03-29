"""dot discard -- throw away uncommitted changes."""

from __future__ import annotations

import click

from gitdot import git


@click.command()
@click.argument("paths", nargs=-1)
def discard(paths: tuple[str, ...]) -> None:
    """Throw away uncommitted changes.

    Usage:
        dot discard              Discard all uncommitted changes
        dot discard src/foo.py   Discard changes in a specific file
    """
    status = git.status_porcelain()
    if not status:
        click.echo("Nothing to discard.")
        return

    if paths:
        git.run_or_fail(["checkout", "--"] + list(paths))
        for p in paths:
            click.echo(f"Discarded: {p}")
    else:
        count = len(status)
        noun = "file" if count == 1 else "files"
        if not click.confirm(f"Discard all changes in {count} {noun}?", default=False):
            click.echo("Cancelled.")
            return
        git.run_or_fail(["checkout", "--", "."])
        git.run(["clean", "-fd"])
        click.echo(f"Discarded all changes in {count} {noun}.")
