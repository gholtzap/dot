"""Tests for dot push."""

import subprocess

from tests.conftest import invoke


def test_push_with_changes(runner, tmp_repo_with_remote):
    local_path, _ = tmp_repo_with_remote
    (local_path / "new.txt").write_text("hello\n")
    result = invoke(runner, ["push", "shipped it"])
    assert result.exit_code == 0
    assert "Saved:" in result.output
    assert "Pushed" in result.output


def test_push_with_auto_message(runner, tmp_repo_with_remote):
    local_path, _ = tmp_repo_with_remote
    (local_path / "new.txt").write_text("hello\n")
    result = invoke(runner, ["push"])
    assert result.exit_code == 0
    assert "Saved:" in result.output
    assert "Pushed" in result.output


def test_push_already_committed(runner, tmp_repo_with_remote):
    local_path, _ = tmp_repo_with_remote
    (local_path / "new.txt").write_text("hello\n")
    subprocess.run(["git", "add", "-A"], cwd=local_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "already committed"],
        cwd=local_path,
        check=True,
        capture_output=True,
    )
    result = invoke(runner, ["push"])
    assert result.exit_code == 0
    assert "Pushed" in result.output


def test_push_no_upstream_decline(runner, tmp_repo_with_commit):
    (tmp_repo_with_commit / "file.txt").write_text("hello\n")
    result = runner.invoke(
        __import__("gitdot.cli", fromlist=["main"]).main,
        ["push", "test"],
        input="n\n",
    )
    assert "No upstream is set" in result.output
    assert "cancelled" in result.output.lower()


def test_push_no_upstream_accept(runner, tmp_repo_with_remote):
    local_path, remote_path = tmp_repo_with_remote
    subprocess.run(
        ["git", "switch", "-c", "new-branch"],
        cwd=local_path,
        check=True,
        capture_output=True,
    )
    (local_path / "new.txt").write_text("hello\n")
    result = runner.invoke(
        __import__("gitdot.cli", fromlist=["main"]).main,
        ["push", "first push"],
        input="y\n",
    )
    assert result.exit_code == 0
    assert "Pushed" in result.output


def test_push_deleted_file_path_is_not_treated_as_message(runner, tmp_repo_with_remote):
    local_path, _ = tmp_repo_with_remote

    tracked = local_path / "old.txt"
    tracked.write_text("hello\n")
    subprocess.run(["git", "add", "-A"], cwd=local_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "add old file"],
        cwd=local_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "push"], cwd=local_path, check=True, capture_output=True)

    tracked.unlink()
    (local_path / "keep.txt").write_text("keep me local\n")

    result = invoke(runner, ["push", "old.txt"])
    assert result.exit_code == 0
    assert "Pushed" in result.output

    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=local_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "keep.txt" in status

    subject = subprocess.run(
        ["git", "log", "-1", "--pretty=%s"],
        cwd=local_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert subject != "old.txt"


def test_push_with_changes_creates_undo_entry(runner, tmp_repo_with_remote):
    local_path, _ = tmp_repo_with_remote
    (local_path / "new.txt").write_text("hello\n")

    result = invoke(runner, ["push", "shipped it"])
    assert result.exit_code == 0

    stack_file = local_path / ".dot" / "undo_stack.json"
    assert stack_file.exists()

    import json

    data = json.loads(stack_file.read_text())
    assert data["entries"][-1]["message"] == "shipped it"
