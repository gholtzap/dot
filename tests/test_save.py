"""Tests for dot save."""

import subprocess

from tests.conftest import invoke


def test_save_all_with_message(runner, tmp_repo_with_commit):
    (tmp_repo_with_commit / "file.txt").write_text("hello\n")
    result = invoke(runner, ["save", "add file"])
    assert result.exit_code == 0
    assert "Saved:" in result.output
    assert "add file" in result.output


def test_save_all_auto_message(runner, tmp_repo_with_commit):
    (tmp_repo_with_commit / "file.txt").write_text("hello\n")
    result = invoke(runner, ["save"])
    assert result.exit_code == 0
    assert "Saved:" in result.output
    # Auto-message should contain "added"
    assert "added" in result.output


def test_save_specific_file(runner, tmp_repo_with_commit):
    (tmp_repo_with_commit / "a.txt").write_text("a\n")
    (tmp_repo_with_commit / "b.txt").write_text("b\n")
    result = invoke(runner, ["save", "a.txt", "save only a"])
    assert result.exit_code == 0
    assert "save only a" in result.output

    # b.txt should still be untracked
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=tmp_repo_with_commit,
        capture_output=True,
        text=True,
    )
    assert "b.txt" in status.stdout


def test_save_nothing_to_commit(runner, tmp_repo_with_commit):
    # First save picks up the .gitignore created by dotdir; do a save to clear it
    invoke(runner, ["save", "clear"])
    # Now there should be nothing to save
    result = invoke(runner, ["save"])
    assert result.exit_code == 0
    assert "no changes" in result.output.lower()


def test_save_creates_undo_entry(runner, tmp_repo_with_commit):
    (tmp_repo_with_commit / "file.txt").write_text("hello\n")
    invoke(runner, ["save", "test save"])
    stack_file = tmp_repo_with_commit / ".dot" / "undo_stack.json"
    assert stack_file.exists()
    import json
    data = json.loads(stack_file.read_text())
    assert len(data["entries"]) == 1
    assert data["entries"][0]["message"] == "test save"


def test_save_modified_file_auto_message(runner, tmp_repo_with_commit):
    # Modify an existing file
    (tmp_repo_with_commit / "README.md").write_text("# updated\n")
    result = invoke(runner, ["save"])
    assert result.exit_code == 0
    assert "modified" in result.output


def test_save_deleted_file_path_is_not_treated_as_message(runner, tmp_repo_with_commit):
    path = tmp_repo_with_commit / "old.txt"
    path.write_text("hello\n")
    subprocess.run(["git", "add", "-A"], cwd=tmp_repo_with_commit, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "add old file"],
        cwd=tmp_repo_with_commit,
        check=True,
        capture_output=True,
    )

    path.unlink()

    result = invoke(runner, ["save", "old.txt"])
    assert result.exit_code == 0
    assert "deleted" in result.output

    subject = subprocess.run(
        ["git", "log", "-1", "--pretty=%s"],
        cwd=tmp_repo_with_commit,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert subject != "old.txt"


def test_save_quoted_pathspec_is_not_treated_as_message(runner, tmp_repo_with_commit):
    (tmp_repo_with_commit / "a.py").write_text("print('a')\n")
    (tmp_repo_with_commit / "b.txt").write_text("b\n")

    result = invoke(runner, ["save", "*.py"])
    assert result.exit_code == 0
    assert "added" in result.output

    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=tmp_repo_with_commit,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "b.txt" in status

    subject = subprocess.run(
        ["git", "log", "-1", "--pretty=%s"],
        cwd=tmp_repo_with_commit,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert subject != "*.py"
