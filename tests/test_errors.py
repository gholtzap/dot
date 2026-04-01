"""Tests for friendly error translation."""

from gitdot.errors import translate


def test_not_a_git_repo():
    msg = translate("fatal: not a git repository (or any of the parent directories)")
    assert msg is not None
    assert "not a git repository" in msg
    assert "git init" in msg


def test_merge_conflict():
    msg = translate("CONFLICT (content): Merge conflict in src/main.py")
    assert msg is not None
    assert "src/main.py" in msg
    assert "<<<<" in msg


def test_diverged():
    msg = translate("Your branch and 'origin/main' have diverged")
    assert msg is not None
    assert "diverged" in msg


def test_auth_failed():
    msg = translate("fatal: Authentication failed for 'https://github.com/...'")
    assert msg is not None
    assert "authenticate" in msg


def test_missing_git_identity():
    msg = translate("Author identity unknown\n\n*** Please tell me who you are.")
    assert msg is not None
    assert "user.name" in msg
    assert "user.email" in msg


def test_missing_git_identity_empty_ident():
    msg = translate("fatal: empty ident name (for <>) not allowed")
    assert msg is not None
    assert "user.name" in msg


def test_permission_denied():
    msg = translate("Permission denied (publickey)")
    assert msg is not None
    assert "SSH" in msg


def test_cannot_read_remote():
    msg = translate("fatal: Could not read from remote repository.")
    assert msg is not None
    assert "remote repository" in msg


def test_detached_head():
    msg = translate("HEAD detached at abc1234")
    assert msg is not None
    assert "not on any branch" in msg


def test_local_changes_overwritten():
    msg = translate(
        "error: Your local changes to the following files would be overwritten by merge"
    )
    assert msg is not None
    assert "unsaved changes" in msg


def test_branch_already_exists():
    msg = translate("fatal: a branch named 'feature' already exists")
    assert msg is not None
    assert "already exists" in msg


def test_no_upstream():
    msg = translate("fatal: The current branch main has no upstream branch")
    assert msg is not None
    assert "not been pushed" in msg


def test_nothing_to_commit():
    msg = translate("nothing to commit, working tree clean")
    assert msg is not None
    assert "no changes" in msg


def test_pathspec():
    msg = translate("error: pathspec 'nonexistent.py' did not match any file(s)")
    assert msg is not None
    assert "nonexistent.py" in msg


def test_unknown_error_returns_none():
    msg = translate("some completely unknown git error message xyz123")
    assert msg is None


def test_empty_returns_none():
    assert translate("") is None
