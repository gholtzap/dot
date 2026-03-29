"""dot start -- initialize a new project and push it up."""

from __future__ import annotations

import click

from gitdot import git
from gitdot.errors import translate


@click.command()
@click.argument("remote_url", required=False)
def start(remote_url: str | None) -> None:
    """Initialize a new project and optionally push to a remote.

    Usage:
        dot start                                  Initialize a local repo
        dot start https://github.com/user/repo.git Initialize and push to remote
    """
    if git.is_repo():
        raise click.ClickException(
            "Already a git repository. Nothing to do."
        )

    git.run_or_fail(["init"])
    git.run_or_fail(["branch", "-M", "main"])

    if remote_url:
        git.run_or_fail(["remote", "add", "origin", remote_url])

    _create_initial_files()

    git.run_or_fail(["add", "-A"])
    git.run_or_fail(["commit", "-m", "initial commit"])

    click.echo("Initialized new project on 'main'.")

    if remote_url:
        click.echo(f"Pushing to {remote_url}...")
        result = git.run(["push", "-u", "origin", "main"])
        if not result.ok:
            friendly = translate(result.stderr)
            raise click.ClickException(friendly or result.stderr)
        click.echo("Pushed.")


def _create_initial_files() -> None:
    from pathlib import Path

    root = Path.cwd()

    gitignore = root / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("")

    readme = root / "README.md"
    if not readme.exists():
        name = root.name
        readme.write_text(f"# {name}\n")
