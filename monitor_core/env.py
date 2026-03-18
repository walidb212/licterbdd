from __future__ import annotations

import os
from pathlib import Path


def _parse_env_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        return None
    key, value = stripped.split("=", 1)
    key = key.strip()
    if not key:
        return None
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1]
    return key, value


def load_env_file(path: str | Path, *, override: bool = False) -> dict[str, str]:
    env_path = Path(path)
    if not env_path.exists():
        return {}
    loaded: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        parsed = _parse_env_line(line)
        if parsed is None:
            continue
        key, value = parsed
        if override or key not in os.environ:
            os.environ[key] = value
        loaded[key] = os.environ.get(key, value)
    return loaded


def load_workspace_env(root: str | Path | None = None, *, override: bool = False) -> dict[str, str]:
    base_dir = Path(root) if root is not None else Path.cwd()
    loaded: dict[str, str] = {}
    for name in (".env", ".env.local"):
        loaded.update(load_env_file(base_dir / name, override=override))
    return loaded


def resolve_openai_api_key() -> str:
    return (
        os.environ.get("OPENAI_API_KEY")
        or os.environ.get("OPENAI_API_TOKEN")
        or ""
    ).strip()
