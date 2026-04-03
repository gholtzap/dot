"""Tests for dot switch."""

import subprocess
from pathlib import Path

from gitdot import git
from tests.conftest import invoke


def test_switch_create_branch(runner, tmp_repo_with_commit):
    result = invoke(runner, ["switch", "-c", "feature"])
    assert result.exit_code == 0
    assert "Created and switched to 'feature'" in result.output

    from gitdot import git

    assert git.current_branch(cwd=tmp_repo_with_commit) == "feature"


def test_switch_to_existing(runner, tmp_repo_with_commit):
    # Create a branch
    subprocess.run(
        ["git", "branch", "other"],
        cwd=tmp_repo_with_commit,
        check=True,
        capture_output=True,
    )

    result = invoke(runner, ["switch", "other"])
    assert result.exit_code == 0
    assert "Switched to 'other'" in result.output


def test_switch_list(runner, tmp_repo_with_commit):
    subprocess.run(
        ["git", "branch", "feature"],
        cwd=tmp_repo_with_commit,
        check=True,
        capture_output=True,
    )

    result = invoke(runner, ["switch", "--list"])
    assert result.exit_code == 0
    assert "feature" in result.output


def test_switch_nonexistent_branch(runner, tmp_repo_with_commit):
    result = runner.invoke(
        __import__("gitdot.cli", fromlist=["main"]).main,
        ["switch", "nonexistent"],
    )
    assert result.exit_code != 0


def test_switch_no_args_lists_branches(runner, tmp_repo_with_commit):
    result = invoke(runner, ["switch"])
    assert result.exit_code == 0
    # Should show at least the current branch
    output = result.output.lower()
    assert "main" in output or "master" in output


def test_switch_create_existing_fails(runner, tmp_repo_with_commit):
    subprocess.run(
        ["git", "branch", "feature"],
        cwd=tmp_repo_with_commit,
        check=True,
        capture_output=True,
    )

    result = runner.invoke(
        __import__("gitdot.cli", fromlist=["main"]).main,
        ["switch", "-c", "feature"],
    )
    assert result.exit_code != 0
    assert "already exists" in result.output.lower()


def test_switch_creates_default_sync_settings_file(runner, tmp_repo_with_remote):
    local_path, _ = tmp_repo_with_remote
    subprocess.run(
        ["git", "branch", "feature"],
        cwd=local_path,
        check=True,
        capture_output=True,
    )

    result = invoke(runner, ["switch", "feature"])

    assert result.exit_code == 0
    settings_file = local_path / ".dot" / "settings" / "sync.toml"
    assert settings_file.exists()
    content = settings_file.read_text()
    assert "enabled = true" in content
    assert "run_on = ['switch']" in content


def test_switch_existing_branch_auto_saves_and_rebases_when_behind_default(
    runner,
    tmp_repo_with_remote,
    tmp_path,
):
    local_path, remote_path = tmp_repo_with_remote
    default_ref = git.remote_default_branch(cwd=local_path)
    default_branch = default_ref.split("/", 1)[1]

    subprocess.run(
        ["git", "branch", "feature"],
        cwd=local_path,
        check=True,
        capture_output=True,
    )

    other = _clone_remote(remote_path, tmp_path / "other")
    (other / "remote_change.txt").write_text("from remote default\n")
    subprocess.run(["git", "add", "-A"], cwd=other, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "default branch moved"],
        cwd=other,
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "push"], cwd=other, check=True, capture_output=True)

    (local_path / "dirty.txt").write_text("save me before switching\n")

    result = invoke(runner, ["switch", "feature"])

    assert result.exit_code == 0
    assert "Saving uncommitted changes before switching..." in result.output
    assert "Saved:" in result.output
    assert "Switched to 'feature'." in result.output
    assert (
        f"This branch was 1 commit behind {default_ref}. Rebased automatically."
        in result.output
    )
    assert git.current_branch(cwd=local_path) == "feature"
    assert (local_path / "remote_change.txt").exists()
    assert not (local_path / "dirty.txt").exists()

    saved_file = subprocess.run(
        ["git", "show", f"{default_branch}:dirty.txt"],
        cwd=local_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert saved_file == "save me before switching\n"


def test_switch_existing_branch_falls_back_to_rebase_suggestion_on_conflict(
    runner,
    tmp_repo_with_remote,
    tmp_path,
):
    local_path, remote_path = tmp_repo_with_remote
    default_ref = git.remote_default_branch(cwd=local_path)
    default_branch = default_ref.split("/", 1)[1]

    (local_path / "shared.txt").write_text("base\n")
    subprocess.run(["git", "add", "-A"], cwd=local_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "add shared file"],
        cwd=local_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "push"], cwd=local_path, check=True, capture_output=True)

    subprocess.run(
        ["git", "branch", "feature"],
        cwd=local_path,
        check=True,
        capture_output=True,
    )

    subprocess.run(
        ["git", "switch", "feature"],
        cwd=local_path,
        check=True,
        capture_output=True,
    )
    (local_path / "shared.txt").write_text("feature\n")
    subprocess.run(["git", "add", "shared.txt"], cwd=local_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "feature change"],
        cwd=local_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "switch", default_branch],
        cwd=local_path,
        check=True,
        capture_output=True,
    )

    other = _clone_remote(remote_path, tmp_path / "other")
    (other / "shared.txt").write_text("remote\n")
    subprocess.run(["git", "add", "shared.txt"], cwd=other, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "remote change"],
        cwd=other,
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "push"], cwd=other, check=True, capture_output=True)

    result = invoke(runner, ["switch", "feature"])

    assert result.exit_code == 0
    assert "Switched to 'feature'." in result.output
    assert (
        f"This branch is 1 commit behind {default_ref}. "
        f"Run 'git rebase {default_ref}'."
    ) in result.output
    assert git.current_branch(cwd=local_path) == "feature"
    assert (local_path / "shared.txt").read_text() == "feature\n"
    assert not (local_path / ".git" / "rebase-merge").exists()
    assert not (local_path / ".git" / "rebase-apply").exists()


def _clone_remote(remote_path: Path, destination: Path) -> Path:
    subprocess.run(
        ["git", "clone", str(remote_path), str(destination)],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "other@test.com"],
        cwd=destination,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Other"],
        cwd=destination,
        check=True,
        capture_output=True,
    )
    return destination
