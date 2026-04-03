"""Tests for automatic stale branch cleanup and revive."""

import subprocess
import time

from gitdot import settings
from tests.conftest import invoke


def test_push_creates_default_branch_settings_file(runner, tmp_repo_with_remote):
    local_path, _ = tmp_repo_with_remote
    (local_path / "new.txt").write_text("hello\n")

    result = invoke(runner, ["push", "ship"])

    assert result.exit_code == 0
    settings_file = local_path / ".dot" / "settings" / "branches.toml"
    assert settings_file.exists()
    content = settings_file.read_text()
    assert "enabled = true" in content
    assert "after_weeks = 2" in content
    assert "run_on = ['push']" in content


def test_push_cleans_up_stale_branch_with_remote_backup(runner, tmp_repo_with_remote):
    local_path, _ = tmp_repo_with_remote
    settings.load_branch_settings(cwd=local_path)
    settings_file = local_path / ".dot" / "settings" / "branches.toml"
    settings_file.write_text(
        "enabled = true\n"
        "after_weeks = 0\n"
        "run_on = ['push']\n"
        "keep_patterns = ['main', 'master', 'dev', 'staging', 'production', 'release/*']\n"
    )

    subprocess.run(
        ["git", "switch", "-c", "feature"],
        cwd=local_path,
        check=True,
        capture_output=True,
    )
    (local_path / "feature.txt").write_text("feature\n")
    subprocess.run(["git", "add", "-A"], cwd=local_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "feature work"],
        cwd=local_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "push", "-u", "origin", "feature"],
        cwd=local_path,
        check=True,
        capture_output=True,
    )
    time.sleep(1)
    subprocess.run(
        ["git", "switch", "main"],
        cwd=local_path,
        check=False,
        capture_output=True,
    )
    subprocess.run(
        ["git", "switch", "master"],
        cwd=local_path,
        check=False,
        capture_output=True,
    )

    (local_path / "main.txt").write_text("main\n")
    result = invoke(runner, ["push", "ship main"])

    assert result.exit_code == 0
    assert "Cleaning up stale branches..." in result.output
    assert "Removed stale branch 'feature'" in result.output

    local_branches = subprocess.run(
        ["git", "branch", "--list", "feature"],
        cwd=local_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert not local_branches

    remote_branches = subprocess.run(
        ["git", "branch", "-r", "--list", "origin/feature"],
        cwd=local_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert remote_branches


def test_push_cleans_up_stale_branch_by_pushing_it_first(runner, tmp_repo_with_remote):
    local_path, _ = tmp_repo_with_remote
    settings.load_branch_settings(cwd=local_path)
    settings_file = local_path / ".dot" / "settings" / "branches.toml"
    settings_file.write_text(
        "enabled = true\n"
        "after_weeks = 0\n"
        "run_on = ['push']\n"
        "keep_patterns = ['main', 'master', 'dev', 'staging', 'production', 'release/*']\n"
    )

    subprocess.run(
        ["git", "switch", "-c", "feature"],
        cwd=local_path,
        check=True,
        capture_output=True,
    )
    (local_path / "feature.txt").write_text("feature\n")
    subprocess.run(["git", "add", "-A"], cwd=local_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "feature work"],
        cwd=local_path,
        check=True,
        capture_output=True,
    )
    time.sleep(1)
    subprocess.run(
        ["git", "switch", "main"],
        cwd=local_path,
        check=False,
        capture_output=True,
    )
    subprocess.run(
        ["git", "switch", "master"],
        cwd=local_path,
        check=False,
        capture_output=True,
    )

    (local_path / "main.txt").write_text("main\n")
    result = invoke(runner, ["push", "ship main"])

    assert result.exit_code == 0
    assert "Removed stale branch 'feature'" in result.output

    remote_branches = subprocess.run(
        ["git", "branch", "-r", "--list", "origin/feature"],
        cwd=local_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert remote_branches


def test_dot_branch_matches_git_branch(runner, tmp_repo_with_commit):
    result = invoke(runner, ["branch", "feature"])

    assert result.exit_code == 0

    branches = subprocess.run(
        ["git", "branch", "--list", "feature"],
        cwd=tmp_repo_with_commit,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert branches


def test_revive_recreates_local_branch_without_switching(runner, tmp_repo_with_remote):
    local_path, _ = tmp_repo_with_remote

    subprocess.run(
        ["git", "switch", "-c", "feature"],
        cwd=local_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "push", "-u", "origin", "feature"],
        cwd=local_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "switch", "main"],
        cwd=local_path,
        check=False,
        capture_output=True,
    )
    subprocess.run(
        ["git", "switch", "master"],
        cwd=local_path,
        check=False,
        capture_output=True,
    )
    subprocess.run(
        ["git", "branch", "-D", "feature"],
        cwd=local_path,
        check=True,
        capture_output=True,
    )

    current_branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=local_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    result = invoke(runner, ["revive", "feature"])

    assert result.exit_code == 0
    assert "Revived 'feature' from 'origin/feature'." in result.output
    assert current_branch == subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=local_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
