"""Tests for dot discard."""

from tests.conftest import invoke


def test_discard_specific_file(runner, tmp_repo_with_commit):
    readme = tmp_repo_with_commit / "README.md"
    readme.write_text("modified\n")

    result = invoke(runner, ["discard", "README.md"])
    assert result.exit_code == 0
    assert "Discarded: README.md" in result.output
    assert readme.read_text() == "# test\n"


def test_discard_all_confirmed(runner, tmp_repo_with_commit):
    (tmp_repo_with_commit / "README.md").write_text("modified\n")
    (tmp_repo_with_commit / "new.txt").write_text("new\n")

    result = runner.invoke(
        __import__("gitdot.cli", fromlist=["main"]).main,
        ["discard"],
        input="y\n",
    )
    assert result.exit_code == 0
    assert "Discarded all" in result.output


def test_discard_all_cancelled(runner, tmp_repo_with_commit):
    (tmp_repo_with_commit / "README.md").write_text("modified\n")

    result = runner.invoke(
        __import__("gitdot.cli", fromlist=["main"]).main,
        ["discard"],
        input="n\n",
    )
    assert "Cancelled" in result.output
    assert (tmp_repo_with_commit / "README.md").read_text() == "modified\n"


def test_discard_nothing(runner, tmp_repo_with_commit):
    result = invoke(runner, ["discard"])
    assert result.exit_code == 0
    assert "Nothing to discard" in result.output


def test_discard_specific_untracked_file(runner, tmp_repo_with_commit):
    path = tmp_repo_with_commit / "new.txt"
    path.write_text("new\n")

    result = invoke(runner, ["discard", "new.txt"])
    assert result.exit_code == 0
    assert "Discarded: new.txt" in result.output
    assert not path.exists()


def test_discard_specific_untracked_directory(runner, tmp_repo_with_commit):
    path = tmp_repo_with_commit / "tmpdir"
    path.mkdir()
    (path / "file.txt").write_text("new\n")

    result = invoke(runner, ["discard", "tmpdir"])
    assert result.exit_code == 0
    assert "Discarded: tmpdir" in result.output
    assert not path.exists()
