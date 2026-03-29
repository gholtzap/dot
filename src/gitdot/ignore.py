"""dot ignore -- add patterns to .gitignore."""

from __future__ import annotations

import click

from gitdot import git


@click.command()
@click.argument("patterns", nargs=-1, required=True)
def ignore(patterns: tuple[str, ...]) -> None:
    """Add files or patterns to .gitignore.

    Usage:
        dot ignore .env              Ignore a single file
        dot ignore "*.pyc" .env      Ignore multiple patterns
        dot ignore build/            Ignore a directory
    """
    root = git.repo_root()
    gitignore = root / ".gitignore"

    existing: set[str] = set()
    if gitignore.exists():
        content = gitignore.read_text()
        existing = {line.strip() for line in content.splitlines()}
    else:
        content = ""

    added = []
    skipped = []
    for pattern in patterns:
        if pattern in existing:
            skipped.append(pattern)
        else:
            added.append(pattern)

    if not added:
        for p in skipped:
            click.echo(f"Already ignored: {p}")
        return

    if content and not content.endswith("\n"):
        content += "\n"
    content += "\n".join(added) + "\n"
    gitignore.write_text(content)

    for p in added:
        click.echo(f"Ignoring: {p}")
    for p in skipped:
        click.echo(f"Already ignored: {p}")
