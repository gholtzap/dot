"""Tests for dot switch."""

import subprocess

from tests.conftest import invoke


def test_switch_create_branch(runner, tmp_repo_with_commit):
    result = invoke(runner, ["switch", "-c", "feature"])
    assert result.exit_code == 0
    assert "Created and switched to 'feature'" in result.output

    from gitdot import git

    assert git.current_branch(cwd=tmp_repo_with_commit) == "feature"


def test_switch_to_existing(runner, tmp_repo_with_commit):
    # Create a branch
    subprocess.run(
        ["git", "branch", "other"],
        cwd=tmp_repo_with_commit,
        check=True,
        capture_output=True,
    )

    result = invoke(runner, ["switch", "other"])
    assert result.exit_code == 0
    assert "Switched to 'other'" in result.output


def test_switch_list(runner, tmp_repo_with_commit):
    subprocess.run(
        ["git", "branch", "feature"],
        cwd=tmp_repo_with_commit,
        check=True,
        capture_output=True,
    )

    result = invoke(runner, ["switch", "--list"])
    assert result.exit_code == 0
    assert "feature" in result.output


def test_switch_nonexistent_branch(runner, tmp_repo_with_commit):
    result = runner.invoke(
        __import__("gitdot.cli", fromlist=["main"]).main,
        ["switch", "nonexistent"],
    )
    assert result.exit_code != 0


def test_switch_no_args_lists_branches(runner, tmp_repo_with_commit):
    result = invoke(runner, ["switch"])
    assert result.exit_code == 0
    # Should show at least the current branch
    output = result.output.lower()
    assert "main" in output or "master" in output


def test_switch_create_existing_fails(runner, tmp_repo_with_commit):
    subprocess.run(
        ["git", "branch", "feature"],
        cwd=tmp_repo_with_commit,
        check=True,
        capture_output=True,
    )

    result = runner.invoke(
        __import__("gitdot.cli", fromlist=["main"]).main,
        ["switch", "-c", "feature"],
    )
    assert result.exit_code != 0
    assert "already exists" in result.output.lower()
