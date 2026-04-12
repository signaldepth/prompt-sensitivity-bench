"""Fail if the public repository contains files or text that should stay private."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FORBIDDEN_TRACKED_PREFIXES = (
    ".local/",
    "data/private/",
    "data/experiments/",
    ".output/",
    "site/",
)

FORBIDDEN_TEXT_MARKERS = (
    ".local/HANDOFF.md",
    "/Users/chris/",
    "projects/knowledge/",
    "ctxray",
)

TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".py",
    ".json",
    ".yml",
    ".yaml",
    ".toml",
    ".svg",
}


def git_ls_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def is_text_path(path: Path) -> bool:
    return path.suffix in TEXT_SUFFIXES or path.name in {"README", "LICENSE", ".gitignore"}


def main() -> None:
    tracked = git_ls_files()
    errors: list[str] = []
    self_rel = str(Path(__file__).relative_to(ROOT))

    for rel in tracked:
        if rel.startswith(FORBIDDEN_TRACKED_PREFIXES):
            errors.append(f"forbidden tracked path: {rel}")

        path = ROOT / rel
        if rel == self_rel or not path.exists() or not path.is_file() or not is_text_path(path):
            continue

        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue

        for marker in FORBIDDEN_TEXT_MARKERS:
            if marker in text:
                errors.append(f"forbidden text marker {marker!r} found in {rel}")

    required = [
        ROOT / "data" / "public" / "findings.json",
        ROOT / "data" / "public" / "models.json",
        ROOT / "data" / "examples" / "e9_specificity_fixture.json",
    ]
    for path in required:
        if not path.exists():
            errors.append(f"required public artifact missing: {path.relative_to(ROOT)}")

    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        raise SystemExit(1)

    print("OK: public repo boundary checks passed")


if __name__ == "__main__":
    main()
