"""Translate git's cryptic errors into plain English."""

from __future__ import annotations

import re

_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"not a git repository", re.IGNORECASE),
        "This directory is not a git repository. Run 'git init' to create one.",
    ),
    (
        re.compile(r"CONFLICT.*Merge conflict in (.+)", re.IGNORECASE),
        "There is a merge conflict in {0}. Open the file, look for the <<<< and "
        ">>>> markers, choose which version to keep, then run 'dot save'.",
    ),
    (
        re.compile(r"have diverged", re.IGNORECASE),
        "Your local branch and the remote have diverged (both have new commits). "
        "Run 'dot pull' to get the latest, then 'dot push' to send your changes.",
    ),
    (
        re.compile(r"Authentication failed", re.IGNORECASE),
        "Git could not authenticate. Check your credentials or SSH key.",
    ),
    (
        re.compile(r"Permission denied \(publickey\)", re.IGNORECASE),
        "SSH key authentication failed. Make sure your SSH key is added to your account.",
    ),
    (
        re.compile(r"Could not read from remote repository", re.IGNORECASE),
        "Cannot reach the remote repository. Check your internet connection and "
        "that the remote URL is correct.",
    ),
    (
        re.compile(r"HEAD detached|detached HEAD", re.IGNORECASE),
        "You are not on any branch. Run 'dot switch <branch>' to get back on a branch.",
    ),
    (
        re.compile(
            r"(?:local changes|Your local changes).*would be overwritten",
            re.IGNORECASE | re.DOTALL,
        ),
        "You have unsaved changes that would be lost. Run 'dot save' first, then try again.",
    ),
    (
        re.compile(r"already exists", re.IGNORECASE),
        "A branch with that name already exists. Pick a different name or "
        "switch to it with 'dot switch <name>'.",
    ),
    (
        re.compile(r"has no upstream branch", re.IGNORECASE),
        "This branch has not been pushed yet. Run 'dot push' to push it for the first time.",
    ),
    (
        re.compile(r"nothing to commit", re.IGNORECASE),
        "There are no changes to save.",
    ),
    (
        re.compile(r"pathspec '(.+)' did not match any file", re.IGNORECASE),
        "The file '{0}' does not exist or is not tracked by git.",
    ),
    (
        re.compile(r"did not match any branch\(es\) known", re.IGNORECASE),
        "That branch does not exist. Run 'dot switch --list' to see available branches.",
    ),
]


def translate(stderr: str) -> str | None:
    """Translate a git error message into a friendly one.

    Returns None if no pattern matches (caller should show the raw message).
    """
    if not stderr:
        return None

    for pattern, template in _PATTERNS:
        match = pattern.search(stderr)
        if match:
            groups = match.groups()
            if groups:
                return template.format(*groups)
            return template

    return None
