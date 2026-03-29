"""Tests for dot sync."""

import subprocess

from tests.conftest import invoke


def test_sync_already_synced(runner, tmp_repo_with_remote):
    local_path, _ = tmp_repo_with_remote
    result = invoke(runner, ["sync"])
    assert result.exit_code == 0
    assert "Already in sync" in result.output


def test_sync_push_local_commits(runner, tmp_repo_with_remote):
    local_path, _ = tmp_repo_with_remote
    (local_path / "new.txt").write_text("hello\n")
    subprocess.run(["git", "add", "-A"], cwd=local_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "local change"],
        cwd=local_path,
        check=True,
        capture_output=True,
    )
    result = invoke(runner, ["sync"])
    assert result.exit_code == 0
    assert "Pushing" in result.output
    assert "Synced" in result.output


def test_sync_pull_remote_commits(runner, tmp_repo_with_remote, tmp_path):
    local_path, remote_path = tmp_repo_with_remote

    # Clone the remote again elsewhere and push a change
    other = tmp_path / "other"
    subprocess.run(
        ["git", "clone", str(remote_path), str(other)],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "other@test.com"],
        cwd=other,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Other"],
        cwd=other,
        check=True,
        capture_output=True,
    )
    (other / "remote_change.txt").write_text("from other\n")
    subprocess.run(["git", "add", "-A"], cwd=other, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "remote change"],
        cwd=other,
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "push"], cwd=other, check=True, capture_output=True)

    # Now sync from the local clone
    result = invoke(runner, ["sync"])
    assert result.exit_code == 0
    assert "Rebasing" in result.output
    assert "Synced" in result.output

    # The file should be there now
    assert (local_path / "remote_change.txt").exists()


def test_sync_no_upstream_decline(runner, tmp_repo_with_commit):
    # This repo has no remote -- sync should prompt
    result = runner.invoke(
        __import__("gitdot.cli", fromlist=["main"]).main,
        ["sync"],
        input="n\n",
    )
    assert "No upstream is set" in result.output
    assert "cancelled" in result.output.lower()
