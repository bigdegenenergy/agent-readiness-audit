"""Filesystem utility functions for Agent Readiness Audit."""

from __future__ import annotations

from pathlib import Path


def find_file(root: Path, *names: str) -> Path | None:
    """Find first matching file by name.

    Args:
        root: Root directory to search in.
        *names: File names to search for.

    Returns:
        Path to first found file, or None.
    """
    for name in names:
        path = root / name
        if path.is_file():
            return path
    return None


def find_files(root: Path, pattern: str, max_depth: int = 5) -> list[Path]:
    """Find files matching a glob pattern.

    Args:
        root: Root directory to search in.
        pattern: Glob pattern to match.
        max_depth: Maximum directory depth to search.

    Returns:
        List of matching file paths.
    """
    results: list[Path] = []

    def search(path: Path, depth: int) -> None:
        if depth > max_depth:
            return

        try:
            for item in path.iterdir():
                if item.is_file() and item.match(pattern):
                    results.append(item)
                elif item.is_dir() and not item.name.startswith("."):
                    search(item, depth + 1)
        except PermissionError:
            pass

    search(root, 0)
    return results


def read_file_safe(path: Path, encoding: str = "utf-8") -> str | None:
    """Safely read a file's contents.

    Args:
        path: Path to file to read.
        encoding: File encoding.

    Returns:
        File contents, or None if read failed.
    """
    try:
        return path.read_text(encoding=encoding, errors="ignore")
    except Exception:
        return None
