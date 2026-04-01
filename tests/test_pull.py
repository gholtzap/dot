"""Tests for dot pull."""

import subprocess

from tests.conftest import invoke


def test_pull_already_up_to_date(runner, tmp_repo_with_remote):
    local_path, _ = tmp_repo_with_remote
    result = invoke(runner, ["pull"])
    assert result.exit_code == 0
    assert "Pulled" in result.output


def test_pull_remote_changes(runner, tmp_repo_with_remote, tmp_path):
    local_path, remote_path = tmp_repo_with_remote

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

    result = invoke(runner, ["pull"])
    assert result.exit_code == 0
    assert "Pulled" in result.output
    assert (local_path / "remote_change.txt").exists()


def test_pull_no_upstream(runner, tmp_repo_with_commit):
    result = runner.invoke(
        __import__("gitdot.cli", fromlist=["main"]).main,
        ["pull"],
    )
    assert result.exit_code != 0
    assert "no upstream" in result.output.lower()


def test_pull_with_local_changes_creates_undo_entry(runner, tmp_repo_with_remote):
    local_path, _ = tmp_repo_with_remote
    (local_path / "local.txt").write_text("local\n")

    result = invoke(runner, ["pull"])
    assert result.exit_code == 0
    assert "Saved:" in result.output

    stack_file = local_path / ".dot" / "undo_stack.json"
    assert stack_file.exists()

    import json

    data = json.loads(stack_file.read_text())
    assert len(data["entries"]) == 1
