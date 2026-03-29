"""Manage the .dot/ metadata directory inside git repositories."""

from __future__ import annotations

from pathlib import Path

from gitdot import git

DOT_DIR_NAME = ".dot"


def dot_path(*, cwd: str | Path | None = None) -> Path:
    """Return the path to the .dot/ directory at the repo root."""
    root = git.repo_root(cwd=cwd)
    return root / DOT_DIR_NAME


def ensure(*, cwd: str | Path | None = None) -> Path:
    """Create .dot/ if it doesn't exist, add to .gitignore, return its path."""
    path = dot_path(cwd=cwd)
    path.mkdir(exist_ok=True)
    _ensure_gitignore_entry(path.parent)
    return path


def _ensure_gitignore_entry(repo_root: Path) -> None:
    """Make sure .dot/ is listed in .gitignore."""
    gitignore = repo_root / ".gitignore"
    entry = f"/{DOT_DIR_NAME}/"

    if gitignore.exists():
        content = gitignore.read_text()
        # Check if already present (exact line match)
        for line in content.splitlines():
            if line.strip() == entry or line.strip() == f"{DOT_DIR_NAME}/":
                return
        # Append, ensuring we start on a new line
        if content and not content.endswith("\n"):
            content += "\n"
        content += entry + "\n"
        gitignore.write_text(content)
    else:
        gitignore.write_text(entry + "\n")
