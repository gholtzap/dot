"""Tests for the git subprocess runner."""

from gitdot import git


def test_run_success(tmp_repo):
    result = git.run(["status"], cwd=tmp_repo)
    assert result.ok
    assert result.returncode == 0


def test_run_failure(tmp_path):
    # Not a git repo -- use an existing directory that's not a repo
    not_a_repo = tmp_path / "empty"
    not_a_repo.mkdir()
    result = git.run(["status"], cwd=not_a_repo)
    assert not result.ok


def test_is_repo(tmp_repo):
    assert git.is_repo(cwd=tmp_repo)


def test_is_not_repo(tmp_path):
    not_a_repo = tmp_path / "nope"
    not_a_repo.mkdir()
    assert not git.is_repo(cwd=not_a_repo)


def test_repo_root(tmp_repo):
    root = git.repo_root(cwd=tmp_repo)
    assert root == tmp_repo


def test_current_branch(tmp_repo_with_commit):
    branch = git.current_branch(cwd=tmp_repo_with_commit)
    assert branch in ("main", "master")


def test_status_porcelain_empty(tmp_repo_with_commit):
    entries = git.status_porcelain(cwd=tmp_repo_with_commit)
    assert entries == []


def test_status_porcelain_with_changes(tmp_repo_with_commit):
    (tmp_repo_with_commit / "new.txt").write_text("hello\n")
    entries = git.status_porcelain(cwd=tmp_repo_with_commit)
    assert len(entries) == 1
    assert entries[0].path == "new.txt"
    assert "?" in entries[0].code


def test_diff_stat_summary(tmp_repo_with_commit):
    (tmp_repo_with_commit / "a.txt").write_text("a\n")
    (tmp_repo_with_commit / "b.txt").write_text("b\n")
    git.run(["add", "-A"], cwd=tmp_repo_with_commit)
    summary = git.diff_stat_summary(staged=True, cwd=tmp_repo_with_commit)
    assert "added 2 files" in summary
