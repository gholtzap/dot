"""dot switch -- sane branch creation, switching, and listing."""

from __future__ import annotations

import click

from gitdot import git
from gitdot.errors import translate


@click.command()
@click.argument("branch", required=False)
@click.option("-c", "--create", "create_name", default=None, help="Create and switch to a new branch.")
@click.option("--list", "list_branches", is_flag=True, help="List all branches.")
def switch(
    branch: str | None,
    create_name: str | None,
    list_branches: bool,
) -> None:
    """Switch branches, create new ones, or list them.

    Usage:
        dot switch main          Switch to an existing branch
        dot switch -c feature    Create and switch to a new branch
        dot switch --list        List all branches
    """
    if list_branches:
        _list_branches()
        return

    if create_name:
        _create_branch(create_name)
        return

    if branch:
        _switch_to(branch)
        return

    # No args -- show branches as a helpful default
    _list_branches()


def _switch_to(branch: str) -> None:
    """Switch to an existing branch with detached HEAD prevention."""
    # Check if it's a real branch
    branch_check = git.run(["branch", "--list", branch])
    if branch_check.ok and not branch_check.stdout.strip():
        # Not a local branch -- check if it's a remote branch
        remote_check = git.run(["branch", "-r", "--list", f"*/{branch}"])
        if remote_check.ok and remote_check.stdout.strip():
            # Remote branch exists, git switch will auto-track it
            pass
        else:
            # Could be a tag or commit hash -- warn about detached HEAD
            tag_check = git.run(["tag", "--list", branch])
            if tag_check.ok and tag_check.stdout.strip():
                raise click.ClickException(
                    f"'{branch}' is a tag, not a branch. Switching to it would "
                    f"put you in detached HEAD state.\n"
                    f"To create a branch from this tag: dot switch -c <branch-name>\n"
                    f"Then: git reset --hard {branch}"
                )

    result = git.run(["switch", branch])
    if not result.ok:
        friendly = translate(result.stderr)
        raise click.ClickException(friendly or result.stderr)

    click.echo(f"Switched to '{branch}'.")


def _create_branch(name: str) -> None:
    """Create a new branch and switch to it."""
    result = git.run(["switch", "-c", name])
    if not result.ok:
        friendly = translate(result.stderr)
        raise click.ClickException(friendly or result.stderr)

    click.echo(f"Created and switched to '{name}'.")


def _list_branches() -> None:
    """List all branches, highlighting the current one."""
    result = git.run(["branch", "-a"])
    if not result.ok:
        friendly = translate(result.stderr)
        raise click.ClickException(friendly or result.stderr)

    if not result.stdout:
        click.echo("No branches yet. Make your first commit with 'dot save'.")
        return

    click.echo(result.stdout)
