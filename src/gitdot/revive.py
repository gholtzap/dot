"""dot revive -- bring back a deleted local branch from a remote."""

from __future__ import annotations

import click

from gitdot import git
from gitdot.errors import translate


@click.command()
@click.argument("branch")
def revive(branch: str) -> None:
    """Recreate a local branch from a matching remote branch."""
    if git.local_branch_exists(branch):
        raise click.ClickException(
            f"'{branch}' already exists locally. Run 'dot switch {branch}' to use it."
        )

    fetch_result = git.run(["fetch", "--all", "--prune"])
    if not fetch_result.ok:
        friendly = translate(fetch_result.stderr)
        raise click.ClickException(friendly or fetch_result.stderr)

    remote_refs = git.matching_remote_branches(branch)
    if not remote_refs:
        raise click.ClickException(
            f"'{branch}' does not exist on any remote. Nothing to revive."
        )

    remote_ref = _choose_remote_ref(branch, remote_refs)
    result = git.run(["branch", "--track", branch, remote_ref])
    if not result.ok:
        friendly = translate(result.stderr)
        raise click.ClickException(friendly or result.stderr)

    click.echo(f"Revived '{branch}' from '{remote_ref}'.")


def _choose_remote_ref(branch: str, remote_refs: list[str]) -> str:
    preferred = f"origin/{branch}"
    if preferred in remote_refs:
        return preferred

    if len(remote_refs) == 1:
        return remote_refs[0]

    raise click.ClickException(
        f"'{branch}' exists on multiple remotes. Run "
        f"'git branch --track {branch} <remote>/<branch>' to choose one."
    )
