"""dot pull -- get the latest from the remote."""

from __future__ import annotations

import click

from gitdot import git
from gitdot.errors import translate


@click.command()
def pull() -> None:
    """Pull the latest changes from the remote.

    Usage:
        dot pull    Fetch and rebase onto the latest remote changes
    """
    branch = git.current_branch()
    if not branch:
        raise click.ClickException(
            "You are not on any branch (detached HEAD). "
            "Run 'dot switch <branch>' to get on a branch first."
        )

    if not git.has_upstream():
        raise click.ClickException(
            "This branch has no upstream. Push it first with 'dot push'."
        )

    upstream = git.upstream_name()
    click.echo(f"Pulling from {upstream}...")

    result = git.run(["pull", "--rebase"])
    if not result.ok:
        files = git.conflicted_files()
        if files:
            _handle_conflict(files)
            raise SystemExit(1)
        friendly = translate(result.stderr)
        raise click.ClickException(friendly or result.stderr)

    click.echo("Pulled.")


def _handle_conflict(files: list[str]) -> None:
    click.echo()
    click.echo("Pull stopped because of conflicts in these files:")
    for f in files:
        click.echo(f"  {f}")
    click.echo()
    click.echo(
        "To resolve:\n"
        "  1. Open each file above\n"
        "  2. Look for the <<<< and >>>> markers\n"
        "  3. Choose which version to keep and remove the markers\n"
        "  4. Save the file\n"
        "  5. Run: git add <file>\n"
        "  6. Run: git rebase --continue"
    )
    click.echo()
    click.echo("Or to abort: git rebase --abort")
