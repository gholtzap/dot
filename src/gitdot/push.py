"""dot push -- save everything and push it up."""

from __future__ import annotations

import click

from gitdot import branch_cleanup, dotdir, git, sync
from gitdot.errors import translate
from gitdot.saving import save_changes


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
        saved = save_changes(paths=paths or None, message=message)
        if saved is not None:
            click.echo(f"Saved: {saved.short_hash} {saved.message}")

    if not sync.maybe_sync("push"):
        return

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
            branch_cleanup.maybe_cleanup("push")
        else:
            click.echo("Push cancelled.")
        return

    upstream = git.upstream_name()
    _pull_if_remote_ahead()
    click.echo(f"Pushing to {upstream}...")
    result = git.run(["push"])
    if not result.ok:
        if _pull_if_remote_ahead():
            click.echo(f"Pushing to {upstream}...")
            retry = git.run(["push"])
            if not retry.ok:
                friendly = translate(retry.stderr)
                raise click.ClickException(friendly or retry.stderr)
        else:
            friendly = translate(result.stderr)
            raise click.ClickException(friendly or result.stderr)
    click.echo("Pushed.")
    branch_cleanup.maybe_cleanup("push")


def _parse_args(args: tuple[str, ...]) -> tuple[list[str], str | None]:
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
def _guess_remote() -> str:
    result = git.run(["remote"])
    if result.ok and result.stdout:
        remotes = result.stdout.splitlines()
        if "origin" in remotes:
            return "origin"
        return remotes[0]
    return "origin"


def _pull_if_remote_ahead() -> bool:
    fetch_result = git.run(["fetch"])
    if not fetch_result.ok:
        friendly = translate(fetch_result.stderr)
        raise click.ClickException(friendly or fetch_result.stderr)

    if git.commit_count_behind() == 0:
        return False

    click.echo("Remote has new changes. Pulling first...")
    pull_result = git.run(["pull", "--rebase"])
    if not pull_result.ok:
        files = git.conflicted_files()
        if files:
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
                "  6. Run: git rebase --continue\n"
                "  7. Run: dot push"
            )
            click.echo()
            click.echo("Or to abort: git rebase --abort")
            raise SystemExit(1)
        friendly = translate(pull_result.stderr)
        raise click.ClickException(friendly or pull_result.stderr)

    return True
