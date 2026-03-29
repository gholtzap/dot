"""Tests for .dot/ directory management."""

from gitdot import dotdir


def test_ensure_creates_dotdir(tmp_repo):
    path = dotdir.ensure(cwd=tmp_repo)
    assert path.exists()
    assert path.is_dir()
    assert path.name == ".dot"


def test_ensure_creates_gitignore_entry(tmp_repo):
    dotdir.ensure(cwd=tmp_repo)
    gitignore = tmp_repo / ".gitignore"
    assert gitignore.exists()
    assert "/.dot/" in gitignore.read_text()


def test_ensure_idempotent(tmp_repo):
    dotdir.ensure(cwd=tmp_repo)
    dotdir.ensure(cwd=tmp_repo)
    gitignore = tmp_repo / ".gitignore"
    content = gitignore.read_text()
    # Should only appear once
    assert content.count(".dot/") == 1


def test_ensure_appends_to_existing_gitignore(tmp_repo):
    gitignore = tmp_repo / ".gitignore"
    gitignore.write_text("*.pyc\n")
    dotdir.ensure(cwd=tmp_repo)
    content = gitignore.read_text()
    assert "*.pyc" in content
    assert "/.dot/" in content


def test_ensure_handles_no_trailing_newline(tmp_repo):
    gitignore = tmp_repo / ".gitignore"
    gitignore.write_text("*.pyc")  # No trailing newline
    dotdir.ensure(cwd=tmp_repo)
    content = gitignore.read_text()
    # .dot/ should be on its own line, not merged with *.pyc
    lines = content.splitlines()
    assert "*.pyc" in lines
    assert "/.dot/" in lines
