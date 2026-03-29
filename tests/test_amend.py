"""Tests for dot amend."""

import subprocess

from tests.conftest import invoke


def test_amend_adds_changes(runner, tmp_repo_with_commit):
    (tmp_repo_with_commit / "file.txt").write_text("hello\n")
    invoke(runner, ["save", "first save"])

    (tmp_repo_with_commit / "forgot.txt").write_text("oops\n")
    result = invoke(runner, ["amend"])
    assert result.exit_code == 0
    assert "Amended:" in result.output

    log = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=tmp_repo_with_commit,
        capture_output=True,
        text=True,
    )
    assert log.stdout.count("\n") == 2


def test_amend_changes_message(runner, tmp_repo_with_commit):
    (tmp_repo_with_commit / "file.txt").write_text("hello\n")
    invoke(runner, ["save", "bad message"])

    result = invoke(runner, ["amend", "good message"])
    assert result.exit_code == 0
    assert "good message" in result.output


def test_amend_no_commits(runner, tmp_repo):
    result = runner.invoke(
        __import__("gitdot.cli", fromlist=["main"]).main,
        ["amend"],
    )
    assert result.exit_code != 0
    assert "Nothing to amend" in result.output
