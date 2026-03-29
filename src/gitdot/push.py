"""dot push -- save everything and push it up."""

from __future__ import annotations

import os
from datetime import datetime

import click

from gitdot import git, dotdir
from gitdot.errors import translate


@click.command()
@click.argument("args", nargs=-1)
def push(args: tuple[str, ...]) -> None:
    """Save all changes and push to the remote.

    Usage:
        dot push                  Save and push with auto-generated message
        dot push "shipped it"     Save and push with a message
    """
    dotdir.ensure()

    branch = git.current_branch()
    if not branch:
        raise click.ClickException(
            "You are not on any branch (detached HEAD). "
            "Run 'dot switch <branch>' to get on a branch first."
        )

    paths, message = _parse_args(args)

    status = git.status_porcelain()
    if status or paths:
        if paths:
            git.run_or_fail(["add"] + paths)
        else:
            git.run_or_fail(["add", "-A"])

        staged_result = git.run(["diff", "--cached", "--quiet"])
        if not staged_result.ok:
            if message is None:
                message = _auto_message()
            git.run_or_fail(["commit", "-m", message])

            full_hash_result = git.run(["rev-parse", "HEAD"])
            if full_hash_result.ok:
                from gitdot.undo import push_entry
                push_entry(full_hash_result.stdout, message)

            result = git.run(["rev-parse", "--short", "HEAD"])
            short_hash = result.stdout if result.ok else "?"
            click.echo(f"Saved: {short_hash} {message}")

    if not git.has_upstream():
        remote = _guess_remote()
        suggested = f"{remote}/{branch}"
        if click.confirm(
            f"No upstream is set. Push to '{suggested}'?",
            default=True,
        ):
            result = git.run(["push", "-u", remote, branch])
            if not result.ok:
                friendly = translate(result.stderr)
                raise click.ClickException(friendly or result.stderr)
            click.echo(f"Pushed to {suggested}.")
        else:
            click.echo("Push cancelled.")
        return

    upstream = git.upstream_name()
    click.echo(f"Pushing to {upstream}...")
    result = git.run(["push"])
    if not result.ok:
        friendly = translate(result.stderr)
        raise click.ClickException(friendly or result.stderr)
    click.echo("Pushed.")


def _parse_args(args: tuple[str, ...]) -> tuple[list[str], str | None]:
    if not args:
        return [], None
    args_list = list(args)
    if len(args_list) == 1:
        if os.path.exists(args_list[0]):
            return args_list, None
        return [], args_list[0]
    if os.path.exists(args_list[-1]):
        return args_list, None
    return args_list[:-1], args_list[-1]


def _auto_message() -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    summary = git.diff_stat_summary(staged=True)
    if summary:
        return f"{timestamp} -- {summary}"
    return timestamp


def _guess_remote() -> str:
    result = git.run(["remote"])
    if result.ok and result.stdout:
        remotes = result.stdout.splitlines()
        if "origin" in remotes:
            return "origin"
        return remotes[0]
    return "origin"
