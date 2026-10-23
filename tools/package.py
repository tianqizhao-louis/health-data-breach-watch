#!/usr/bin/env python3
"""Zip each skill in skills/ into dist/<name>.zip for upload to Claude apps.

The zip holds the skill folder at its root (<name>/SKILL.md, ...), which is
what the Claude app's skill upload expects. Caches and OS junk are skipped,
and timestamps are fixed so the same source gives the same zip.
"""
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache"}
SKIP_FILES = {".DS_Store", "Thumbs.db"}


def package(folder, dist):
    out = dist / f"{folder.name}.zip"
    files = sorted(p for p in folder.rglob("*")
                   if p.is_file() and p.name not in SKIP_FILES and not SKIP_DIRS & set(p.parts)
                   and p.suffix != ".pyc")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            info = zipfile.ZipInfo(str(f.relative_to(folder.parent)), date_time=(2026, 1, 1, 0, 0, 0))
            info.external_attr = (0o755 if f.suffix == ".py" else 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, f.read_bytes())
    return out, len(files)


def main():
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    for folder in sorted(p for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").is_file()):
        out, n = package(folder, dist)
        print(f"{out.relative_to(ROOT)}  ({n} files, {out.stat().st_size // 1024 or 1} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
