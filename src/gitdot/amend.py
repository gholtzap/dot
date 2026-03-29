"""dot amend -- fix the last save."""

from __future__ import annotations

import click

from gitdot import git, dotdir


@click.command()
@click.argument("message", required=False)
def amend(message: str | None) -> None:
    """Fix the last save by adding current changes or updating the message.

    Usage:
        dot amend                Stage all changes into the last save
        dot amend "new message"  Change the last save's message (and stage changes)
    """
    dotdir.ensure()

    log_result = git.run(["log", "--oneline", "-1"])
    if not log_result.ok or not log_result.stdout:
        raise click.ClickException(
            "Nothing to amend. Make your first save with 'dot save'."
        )

    git.run_or_fail(["add", "-A"])

    args = ["commit", "--amend", "--no-edit"]
    if message is not None:
        args = ["commit", "--amend", "-m", message]

    git.run_or_fail(args)

    result = git.run(["log", "--oneline", "-1"])
    click.echo(f"Amended: {result.stdout}")
