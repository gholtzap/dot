"""Tests for dot ignore."""

from tests.conftest import invoke


def test_ignore_single_pattern(runner, tmp_repo_with_commit):
    result = invoke(runner, ["ignore", ".env"])
    assert result.exit_code == 0
    assert "Ignoring: .env" in result.output

    gitignore = tmp_repo_with_commit / ".gitignore"
    assert ".env" in gitignore.read_text()


def test_ignore_multiple_patterns(runner, tmp_repo_with_commit):
    result = invoke(runner, ["ignore", ".env", "*.pyc", "build/"])
    assert result.exit_code == 0
    content = (tmp_repo_with_commit / ".gitignore").read_text()
    assert ".env" in content
    assert "*.pyc" in content
    assert "build/" in content


def test_ignore_creates_gitignore(runner, tmp_repo):
    """If .gitignore doesn't exist, create it."""
    gitignore = tmp_repo / ".gitignore"
    assert not gitignore.exists()

    result = invoke(runner, ["ignore", ".env"])
    assert result.exit_code == 0
    assert gitignore.exists()
    assert ".env" in gitignore.read_text()


def test_ignore_skips_duplicates(runner, tmp_repo_with_commit):
    invoke(runner, ["ignore", ".env"])
    result = invoke(runner, ["ignore", ".env"])
    assert "Already ignored: .env" in result.output

    # Should only appear once
    content = (tmp_repo_with_commit / ".gitignore").read_text()
    assert content.count(".env") == 1


def test_ignore_appends_to_existing(runner, tmp_repo_with_commit):
    gitignore = tmp_repo_with_commit / ".gitignore"
    gitignore.write_text("node_modules/\n")

    invoke(runner, ["ignore", ".env"])
    content = gitignore.read_text()
    assert "node_modules/" in content
    assert ".env" in content


def test_ignore_mixed_new_and_existing(runner, tmp_repo_with_commit):
    invoke(runner, ["ignore", ".env"])
    result = invoke(runner, ["ignore", ".env", "*.log"])
    assert "Already ignored: .env" in result.output
    assert "Ignoring: *.log" in result.output
