from __future__ import annotations

import shutil
from os import PathLike
from pathlib import Path


OutputPath = str | PathLike[str]


def _is_output_tree(relative_path: Path) -> bool:
    top_level = relative_path.parts[0]
    return top_level == "outputs" or top_level.startswith("outputs_")


def assert_safe_output_path(target: OutputPath, repo_root: OutputPath | None = None) -> Path:
    """Return a resolved output path only if it is safely inside this repo."""
    root = Path(repo_root or Path.cwd()).resolve()
    resolved = Path(target).resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Refusing to operate outside repository root: {resolved}") from exc

    if not relative.parts:
        raise ValueError(f"Refusing to operate on repository root: {resolved}")

    if relative.parts[0] == "outputs" and len(relative.parts) == 1:
        raise ValueError(f"Refusing to operate on generic outputs root: {resolved}")

    if not _is_output_tree(relative):
        raise ValueError(
            f"Refusing to operate on non-output path: {resolved}. "
            "Expected a top-level outputs* directory."
        )
    return resolved


def safe_rmtree(target: OutputPath, repo_root: OutputPath | None = None, *, missing_ok: bool = False) -> None:
    resolved = assert_safe_output_path(target, repo_root)
    if not resolved.exists():
        if missing_ok:
            return
        raise FileNotFoundError(resolved)
    if not resolved.is_dir():
        raise NotADirectoryError(resolved)
    shutil.rmtree(resolved)
