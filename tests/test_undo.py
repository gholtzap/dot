"""Tests for dot undo."""

import json
import subprocess

from tests.conftest import invoke


def test_undo_single(runner, tmp_repo_with_commit):
    # Make a save
    (tmp_repo_with_commit / "file.txt").write_text("hello\n")
    invoke(runner, ["save", "add file"])

    # Undo it
    result = invoke(runner, ["undo"])
    assert result.exit_code == 0
    assert "1 save reverted" in result.output

    # The file should still exist (revert creates a new commit, doesn't delete)
    # but its content should be reverted
    log = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=tmp_repo_with_commit,
        capture_output=True,
        text=True,
    )
    assert "Revert" in log.stdout


def test_undo_multiple(runner, tmp_repo_with_commit):
    # Make 3 saves
    for i in range(3):
        (tmp_repo_with_commit / f"file{i}.txt").write_text(f"{i}\n")
        invoke(runner, ["save", f"save {i}"])

    # Undo 2
    result = invoke(runner, ["undo", "2"])
    assert result.exit_code == 0
    assert "2 saves reverted" in result.output

    # Stack should have 1 entry left
    stack_file = tmp_repo_with_commit / ".dot" / "undo_stack.json"
    data = json.loads(stack_file.read_text())
    assert len(data["entries"]) == 1


def test_undo_empty_stack(runner, tmp_repo_with_commit):
    result = invoke(runner, ["undo"])
    assert result.exit_code == 0
    assert "Nothing to undo" in result.output


def test_undo_too_many(runner, tmp_repo_with_commit):
    (tmp_repo_with_commit / "file.txt").write_text("hello\n")
    invoke(runner, ["save", "one save"])

    result = invoke(runner, ["undo", "5"])
    assert result.exit_code == 0
    assert "Only 1 save(s)" in result.output


def test_undo_stack_max_size(runner, tmp_repo_with_commit):
    from gitdot.undo import MAX_STACK_SIZE, _read_stack

    # Create more entries than the max
    for i in range(MAX_STACK_SIZE + 5):
        (tmp_repo_with_commit / "file.txt").write_text(f"v{i}\n")
        invoke(runner, ["save", f"save {i}"])

    entries = _read_stack(cwd=tmp_repo_with_commit)
    assert len(entries) == MAX_STACK_SIZE
