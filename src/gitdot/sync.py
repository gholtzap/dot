"""dot sync -- simplified pull + push with rebase."""

from __future__ import annotations

import click

from gitdot import git, dotdir
from gitdot.errors import translate


@click.command()
def sync() -> None:
    """Pull (rebase) and push in one step.

    Fetches from the remote, rebases local commits on top, then pushes.
    If no upstream is set, prompts to create one.
    """
    dotdir.ensure()

    branch = git.current_branch()
    if not branch:
        raise click.ClickException(
            "You are not on any branch (detached HEAD). "
            "Run 'dot switch <branch>' to get on a branch first."
        )

    # Check for upstream
    if not git.has_upstream():
        _prompt_set_upstream(branch)
        return

    upstream = git.upstream_name()

    # Fetch
    click.echo(f"Fetching from remote...")
    fetch_result = git.run(["fetch"])
    if not fetch_result.ok:
        friendly = translate(fetch_result.stderr)
        raise click.ClickException(friendly or fetch_result.stderr)

    behind = git.commit_count_behind()
    ahead = git.commit_count_ahead()

    if behind == 0 and ahead == 0:
        click.echo("Already in sync.")
        return

    # Rebase if behind
    if behind > 0:
        noun = "commit" if behind == 1 else "commits"
        click.echo(f"Rebasing {behind} {noun} onto {upstream}...")
        rebase_result = git.run(["rebase", upstream])
        if not rebase_result.ok:
            _handle_conflict()
            raise SystemExit(1)

    # Push if ahead (or after successful rebase)
    ahead_after = git.commit_count_ahead()
    if ahead_after > 0:
        click.echo(f"Pushing to {upstream}...")
        push_result = git.run(["push"])
        if not push_result.ok:
            friendly = translate(push_result.stderr)
            raise click.ClickException(friendly or push_result.stderr)

    click.echo("Synced.")


def _prompt_set_upstream(branch: str) -> None:
    """Prompt the user to set an upstream when none exists."""
    remote = _guess_remote()
    suggested = f"{remote}/{branch}"

    if click.confirm(
        f"No upstream is set. Push to '{suggested}'?",
        default=True,
    ):
        click.echo(f"Pushing to {suggested}...")
        result = git.run(["push", "-u", remote, branch])
        if not result.ok:
            friendly = translate(result.stderr)
            raise click.ClickException(friendly or result.stderr)
        click.echo("Synced.")
    else:
        click.echo("Sync cancelled.")


def _guess_remote() -> str:
    """Return the best remote name to use (usually 'origin')."""
    result = git.run(["remote"])
    if result.ok and result.stdout:
        remotes = result.stdout.splitlines()
        if "origin" in remotes:
            return "origin"
        return remotes[0]
    return "origin"


def _handle_conflict() -> None:
    """Print friendly conflict resolution instructions."""
    files = git.conflicted_files()
    click.echo()
    click.echo("Sync stopped because of conflicts in these files:")
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
    click.echo("Or to abort the sync: git rebase --abort")
