"""Tests for git passthrough."""

from tests.conftest import invoke


def test_passthrough_status(runner, tmp_repo_with_commit):
    result = invoke(runner, ["status"])
    assert result.exit_code == 0


def test_passthrough_log(runner, tmp_repo_with_commit):
    result = invoke(runner, ["log", "--oneline"])
    assert result.exit_code == 0


def test_passthrough_unknown_command(runner, tmp_repo_with_commit):
    # Unknown git subcommand should fail (git will error) but should not
    # be caught by dot -- just passes through
    result = runner.invoke(
        __import__("gitdot.cli", fromlist=["main"]).main,
        ["definitely-not-a-command"],
    )
    assert result.exit_code != 0
