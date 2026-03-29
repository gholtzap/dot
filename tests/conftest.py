"""Shared test fixtures -- real git repos in temp directories."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from gitdot.cli import main


@pytest.fixture
def runner():
    """Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def tmp_repo(tmp_path):
    """Create a temporary git repo and chdir into it."""
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(old_cwd)


@pytest.fixture
def tmp_repo_with_commit(tmp_repo):
    """A temp repo with one initial commit."""
    (tmp_repo / "README.md").write_text("# test\n")
    subprocess.run(
        ["git", "add", "-A"], cwd=tmp_repo, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=tmp_repo,
        check=True,
        capture_output=True,
    )
    return tmp_repo


@pytest.fixture
def tmp_repo_with_remote(tmp_path):
    """A temp repo with a bare remote, for testing sync."""
    remote_path = tmp_path / "remote.git"
    local_path = tmp_path / "local"

    # Create bare remote
    subprocess.run(
        ["git", "init", "--bare", str(remote_path)],
        check=True,
        capture_output=True,
    )

    # Clone it
    subprocess.run(
        ["git", "clone", str(remote_path), str(local_path)],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=local_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=local_path,
        check=True,
        capture_output=True,
    )

    # Ensure default branch is "main" for the bare repo
    subprocess.run(
        ["git", "config", "init.defaultBranch", "main"],
        cwd=remote_path,
        check=True,
        capture_output=True,
    )

    # Create initial commit so we have a branch
    (local_path / "README.md").write_text("# test\n")
    subprocess.run(
        ["git", "add", "-A"], cwd=local_path, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=local_path,
        check=True,
        capture_output=True,
    )
    # Get the actual branch name and push
    branch_result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=local_path,
        capture_output=True,
        text=True,
    )
    branch = branch_result.stdout.strip()
    subprocess.run(
        ["git", "push", "-u", "origin", branch],
        cwd=local_path,
        check=True,
        capture_output=True,
    )

    old_cwd = os.getcwd()
    os.chdir(local_path)
    yield local_path, remote_path
    os.chdir(old_cwd)


def invoke(runner: CliRunner, args: list[str]) -> ...:
    """Helper to invoke the dot CLI."""
    return runner.invoke(main, args, catch_exceptions=False)
