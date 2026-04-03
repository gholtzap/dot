"""Load and write dot settings stored in .dot/settings."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from gitdot import dotdir

SETTINGS_DIR_NAME = "settings"
BRANCH_SETTINGS_FILE = "branches.toml"
SYNC_SETTINGS_FILE = "sync.toml"
ALLOWED_RUN_ON = {"save", "pull", "switch", "push"}


class SettingsError(ValueError):
    """Raised when the settings file cannot be parsed or validated."""


@dataclass(frozen=True)
class BranchSettings:
    enabled: bool = True
    after_weeks: int = 2
    run_on: tuple[str, ...] = ("push",)
    keep_patterns: tuple[str, ...] = (
        "main",
        "master",
        "dev",
        "staging",
        "production",
        "release/*",
    )


DEFAULT_BRANCH_SETTINGS = BranchSettings()


@dataclass(frozen=True)
class SyncSettings:
    enabled: bool = True
    run_on: tuple[str, ...] = ("switch",)


DEFAULT_SYNC_SETTINGS = SyncSettings()


def settings_dir(*, cwd: str | Path | None = None) -> Path:
    path = dotdir.ensure(cwd=cwd) / SETTINGS_DIR_NAME
    path.mkdir(exist_ok=True)
    return path


def branch_settings_path(*, cwd: str | Path | None = None) -> Path:
    return settings_dir(cwd=cwd) / BRANCH_SETTINGS_FILE


def sync_settings_path(*, cwd: str | Path | None = None) -> Path:
    return settings_dir(cwd=cwd) / SYNC_SETTINGS_FILE


def load_branch_settings(*, cwd: str | Path | None = None) -> BranchSettings:
    path = branch_settings_path(cwd=cwd)
    if not path.exists():
        path.write_text(_serialize(DEFAULT_BRANCH_SETTINGS))
        return DEFAULT_BRANCH_SETTINGS

    raw = _parse(
        path.read_text(),
        allowed_keys={"enabled", "after_weeks", "run_on", "keep_patterns"},
    )
    return BranchSettings(
        enabled=_validate_bool(raw, "enabled", DEFAULT_BRANCH_SETTINGS.enabled),
        after_weeks=_validate_non_negative_int(
            raw,
            "after_weeks",
            DEFAULT_BRANCH_SETTINGS.after_weeks,
        ),
        run_on=_validate_string_list(raw, "run_on", DEFAULT_BRANCH_SETTINGS.run_on),
        keep_patterns=_validate_string_list(
            raw,
            "keep_patterns",
            DEFAULT_BRANCH_SETTINGS.keep_patterns,
        ),
    )


def load_sync_settings(*, cwd: str | Path | None = None) -> SyncSettings:
    path = sync_settings_path(cwd=cwd)
    if not path.exists():
        path.write_text(_serialize_sync(DEFAULT_SYNC_SETTINGS))
        return DEFAULT_SYNC_SETTINGS

    raw = _parse(path.read_text(), allowed_keys={"enabled", "run_on"})
    return SyncSettings(
        enabled=_validate_bool(raw, "enabled", DEFAULT_SYNC_SETTINGS.enabled),
        run_on=_validate_string_list(raw, "run_on", DEFAULT_SYNC_SETTINGS.run_on),
    )


def _serialize(settings: BranchSettings) -> str:
    lines = [
        f"enabled = {_toml_bool(settings.enabled)}",
        f"after_weeks = {settings.after_weeks}",
        f"run_on = {_toml_list(settings.run_on)}",
        f"keep_patterns = {_toml_list(settings.keep_patterns)}",
    ]
    return "\n".join(lines) + "\n"


def _serialize_sync(settings: SyncSettings) -> str:
    lines = [
        f"enabled = {_toml_bool(settings.enabled)}",
        f"run_on = {_toml_list(settings.run_on)}",
    ]
    return "\n".join(lines) + "\n"


def _parse(content: str, *, allowed_keys: set[str]) -> dict[str, object]:
    values: dict[str, object] = {}
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            raise SettingsError("Settings must be written as key = value.")
        key, raw_value = stripped.split("=", 1)
        key = key.strip()
        if key not in allowed_keys:
            raise SettingsError(f"Unknown setting '{key}'.")
        values[key] = _parse_value(raw_value.strip(), key)
    return values


def _parse_value(raw: str, key: str) -> object:
    if raw == "true":
        return True
    if raw == "false":
        return False
    if raw.isdigit():
        return int(raw)
    try:
        return ast.literal_eval(raw)
    except (SyntaxError, ValueError) as exc:
        raise SettingsError(f"Could not parse '{key}'.") from exc


def _validate_bool(
    values: dict[str, object],
    key: str,
    default: bool,
) -> bool:
    value = values.get(key, default)
    if isinstance(value, bool):
        return value
    raise SettingsError(f"'{key}' must be true or false.")


def _validate_non_negative_int(
    values: dict[str, object],
    key: str,
    default: int,
) -> int:
    value = values.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int):
        raise SettingsError(f"'{key}' must be a whole number.")
    if value < 0:
        raise SettingsError(f"'{key}' cannot be negative.")
    return value


def _validate_string_list(
    values: dict[str, object],
    key: str,
    default: tuple[str, ...],
) -> tuple[str, ...]:
    value = values.get(key, default)
    if isinstance(value, tuple):
        return value
    if not isinstance(value, list):
        raise SettingsError(f"'{key}' must be a list of strings.")
    if not all(isinstance(item, str) and item for item in value):
        raise SettingsError(f"'{key}' must be a list of strings.")
    if key == "run_on":
        unknown = [item for item in value if item not in ALLOWED_RUN_ON]
        if unknown:
            allowed = ", ".join(sorted(ALLOWED_RUN_ON))
            raise SettingsError(
                f"Unknown run_on value '{unknown[0]}'. Allowed values: {allowed}."
            )
    return tuple(value)


def _toml_bool(value: bool) -> str:
    return "true" if value else "false"


def _toml_list(values: tuple[str, ...]) -> str:
    return "[" + ", ".join(repr(value) for value in values) + "]"
