"""Tests for dot start."""

import os
import subprocess

from tests.conftest import invoke


def test_start_local_only(runner, tmp_path):
    project = tmp_path / "myproject"
    project.mkdir()
    os.chdir(project)

    result = invoke(runner, ["start"])
    assert result.exit_code == 0
    assert "Initialized" in result.output

    assert (project / ".git").is_dir()
    assert (project / ".gitignore").exists()
    assert (project / "README.md").exists()
    assert "# myproject" in (project / "README.md").read_text()

    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=project,
        capture_output=True,
        text=True,
    )
    assert branch.stdout.strip() == "main"


def test_start_with_remote(runner, tmp_path):
    remote_path = tmp_path / "remote.git"
    subprocess.run(
        ["git", "init", "--bare", str(remote_path)],
        check=True,
        capture_output=True,
    )

    project = tmp_path / "myproject"
    project.mkdir()
    os.chdir(project)

    result = invoke(runner, ["start", str(remote_path)])
    assert result.exit_code == 0
    assert "Pushed" in result.output

    remote_check = subprocess.run(
        ["git", "remote", "-v"],
        cwd=project,
        capture_output=True,
        text=True,
    )
    assert "origin" in remote_check.stdout


def test_start_already_a_repo(runner, tmp_repo_with_commit):
    result = runner.invoke(
        __import__("gitdot.cli", fromlist=["main"]).main,
        ["start"],
    )
    assert result.exit_code != 0
    assert "Already a git repository" in result.output


def test_start_preserves_existing_files(runner, tmp_path):
    project = tmp_path / "myproject"
    project.mkdir()
    (project / "app.py").write_text("print('hello')\n")
    (project / "README.md").write_text("# My Custom Readme\n")
    os.chdir(project)

    result = invoke(runner, ["start"])
    assert result.exit_code == 0

    assert (project / "README.md").read_text() == "# My Custom Readme\n"
    assert (project / "app.py").exists()

    log = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=project,
        capture_output=True,
        text=True,
    )
    assert "initial commit" in log.stdout
