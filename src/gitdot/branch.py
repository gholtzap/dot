"""dot branch -- exact passthrough to git branch."""

from __future__ import annotations

import click

from gitdot import git


@click.command(
    context_settings={
        "ignore_unknown_options": True,
        "allow_extra_args": True,
    },
)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def branch(ctx: click.Context, args: tuple[str, ...]) -> None:
    """Run git branch exactly as-is."""
    result = git.run(["branch"] + list(args), capture=False)
    ctx.exit(result.returncode)
