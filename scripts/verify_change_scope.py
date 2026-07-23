#!/usr/bin/env python3
"""Verify that local Git changes stay inside an explicit file scope.

Examples:
    python scripts/verify_change_scope.py --allow 'src/**' --allow 'tests/**'
    python scripts/verify_change_scope.py --allow '**/*.py' --deny 'migrations/**'
    python scripts/verify_change_scope.py --base origin/main --allow 'game/**'

The script checks staged, unstaged, deleted, renamed, copied, and untracked
paths. It also runs ``git diff --check`` for tracked changes. It never modifies
the repository.
"""

from __future__ import annotations

import argparse
import fnmatch
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


def run(command: Sequence[str], cwd: Path) -> CommandResult:
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def run_bytes(command: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def git_root(start: Path) -> Path:
    result = run(["git", "rev-parse", "--show-toplevel"], start)
    if result.returncode != 0:
        detail = result.stderr.strip() or "not inside a Git repository"
        raise RuntimeError(detail)
    return Path(result.stdout.strip()).resolve()


def resolve_base(root: Path, base: str) -> str | None:
    result = run(["git", "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}"], root)
    if result.returncode == 0:
        return base
    if base == "HEAD":
        return None
    raise RuntimeError(f"invalid Git revision: {base}")


def parse_name_status_z(data: bytes) -> set[str]:
    fields = data.decode("utf-8", errors="surrogateescape").split("\0")
    paths: set[str] = set()
    index = 0

    while index < len(fields):
        status = fields[index]
        index += 1
        if not status:
            continue

        kind = status[0]
        path_count = 2 if kind in {"R", "C"} else 1
        if index + path_count > len(fields):
            raise RuntimeError("unexpected git --name-status output")

        for _ in range(path_count):
            path = fields[index]
            index += 1
            if path:
                paths.add(path.replace("\\", "/"))

    return paths


def null_paths(data: bytes) -> set[str]:
    return {
        item.decode("utf-8", errors="surrogateescape").replace("\\", "/")
        for item in data.split(b"\0")
        if item
    }


def changed_files(root: Path, base: str | None) -> list[str]:
    paths: set[str] = set()

    if base is None:
        listed = run_bytes(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            root,
        )
        if listed.returncode != 0:
            detail = listed.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(detail or "git ls-files failed")
        paths.update(null_paths(listed.stdout))
    else:
        diff = run_bytes(
            ["git", "diff", "--name-status", "-z", "--find-renames", "--find-copies", base, "--"],
            root,
        )
        if diff.returncode != 0:
            detail = diff.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(detail or "git diff failed")
        paths.update(parse_name_status_z(diff.stdout))

        untracked = run_bytes(
            ["git", "ls-files", "--others", "--exclude-standard", "-z"],
            root,
        )
        if untracked.returncode != 0:
            detail = untracked.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(detail or "git ls-files failed")
        paths.update(null_paths(untracked.stdout))

    return sorted(paths)


def matches(path: str, patterns: Sequence[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fail when local changes fall outside allowed globs or match denied globs."
    )
    parser.add_argument(
        "--base",
        default="HEAD",
        help="Git revision used as the tracked-change diff base (default: HEAD).",
    )
    parser.add_argument(
        "--allow",
        action="append",
        default=[],
        metavar="GLOB",
        help="Allowed repository-relative path glob. Repeat as needed.",
    )
    parser.add_argument(
        "--deny",
        action="append",
        default=[],
        metavar="GLOB",
        help="Denied repository-relative path glob. Repeat as needed.",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="Path inside the repository (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        root = git_root(args.repo.resolve())
        resolved_base = resolve_base(root, args.base)
        files = changed_files(root, resolved_base)
    except (OSError, RuntimeError) as exc:
        print(f"scope-check error: {exc}", file=sys.stderr)
        return 2

    unexpected = [path for path in files if args.allow and not matches(path, args.allow)]
    denied = [path for path in files if args.deny and matches(path, args.deny)]

    if resolved_base is None:
        diff_check = run(["git", "diff", "--cached", "--check", "--"], root)
        base_label = "empty tree (no HEAD)"
    else:
        diff_check = run(["git", "diff", "--check", resolved_base, "--"], root)
        base_label = resolved_base

    print(f"Repository: {root}")
    print(f"Diff base: {base_label}")
    print(f"Changed files: {len(files)}")
    for path in files:
        print(f"  {path}")

    failed = False
    if unexpected:
        failed = True
        print("\nOutside allowed scope:", file=sys.stderr)
        for path in unexpected:
            print(f"  {path}", file=sys.stderr)

    if denied:
        failed = True
        print("\nMatched denied scope:", file=sys.stderr)
        for path in denied:
            print(f"  {path}", file=sys.stderr)

    if diff_check.returncode != 0:
        failed = True
        print("\ngit diff --check failed:", file=sys.stderr)
        if diff_check.stdout.strip():
            print(diff_check.stdout.rstrip(), file=sys.stderr)
        if diff_check.stderr.strip():
            print(diff_check.stderr.rstrip(), file=sys.stderr)

    if failed:
        return 1

    print("\nScope and whitespace checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
