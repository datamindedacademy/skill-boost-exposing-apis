#!/usr/bin/env python3
"""
Apply exercise solutions.

Usage:
    apply_solutions.py reset       # back to starting state
    apply_solutions.py solve N     # apply solutions 1..N
    apply_solutions.py solve all   # apply all solutions
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC_PATH = ROOT / "src" / "checkup_api"
EX_PATH = ROOT / "exercises"
SKELETON_PATH = ROOT / "src" / "_skeleton"

# Files that the exercises mutate.
FILES = {
    "models": SRC_PATH / "models.py",
    "schemas": SRC_PATH / "schemas.py",
    "v2": SRC_PATH / "routers" / "v2.py",
    "auth": SRC_PATH / "auth.py",
    "main": SRC_PATH / "main.py",
}

# Starting state for each file.
SKELETON = {
    "models": SKELETON_PATH / "models.py",
    "schemas": SKELETON_PATH / "schemas.py",
    "v2": SKELETON_PATH / "routers" / "v2.py",
    "auth": SKELETON_PATH / "auth.py",
    "main": SKELETON_PATH / "main.py",
}

# Cumulative writes per exercise.
SOLUTIONS: dict[int, list[tuple[str, Path]]] = {
    1: [
        ("v2", EX_PATH / "01_design" / "solution" / "v2.py"),
    ],
    2: [
        ("models", EX_PATH / "02_orm" / "solution" / "models.py"),
        ("v2", EX_PATH / "02_orm" / "solution" / "v2.py"),
    ],
    3: [
        ("schemas", EX_PATH / "03_openapi" / "solution" / "schemas.py"),
        ("v2", EX_PATH / "03_openapi" / "solution" / "v2.py"),
        ("main", EX_PATH / "03_openapi" / "solution" / "main.py"),
    ],
    4: [
        ("auth", EX_PATH / "04_auth" / "solution" / "auth.py"),
        ("v2", EX_PATH / "04_auth" / "solution" / "v2.py"),
    ],
}


def reset() -> None:
    print("Resetting to starting state...")
    for key, target in FILES.items():
        shutil.copyfile(SKELETON[key], target)
        print(f"  reset {target.relative_to(ROOT)}")


def solve(level: int) -> None:
    if level < 1 or level > 4:
        sys.exit(f"level must be 1..4 (got {level})")
    reset()
    print(f"Applying solutions 1..{level}...")
    for n in range(1, level + 1):
        print(f"  -- ex{n} --")
        for key, src in SOLUTIONS[n]:
            shutil.copyfile(src, FILES[key])
            print(f"    write {FILES[key].relative_to(ROOT)}")
    print("done")


def main(argv: list[str]) -> int:
    if argv == ["reset"]:
        reset()
        return 0
    if len(argv) == 2 and argv[0] == "solve":
        if argv[1] == "all":
            solve(4)
            return 0
        if argv[1].isdigit():
            solve(int(argv[1]))
            return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
