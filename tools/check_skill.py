#!/usr/bin/env python3
"""Check every skill in skills/ against the Agent Skills format.

Checks the frontmatter limits, the folder name, body length and that every
references/ or scripts/ file the body mentions exists. Also checks that
.claude-plugin/marketplace.json points at real skill folders.
Standard library only. Exit codes: 0 ok, 1 problems found.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ALLOWED = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None, text
    fields, current = {}, None
    for line in m.group(1).splitlines():
        if re.match(r"^\S[^:]*:", line):
            current, _, value = line.partition(":")
            fields[current.strip()] = value.strip().strip('"')
        elif current and line.startswith("  "):
            fields[current] = (fields[current] + " " + line.strip()).strip()
    return fields, text[m.end():]


def check_skill(folder):
    problems = []
    skill_md = folder / "SKILL.md"
    if not skill_md.is_file():
        return False, [f"{folder.name}: no SKILL.md"]
    fm, body = frontmatter(skill_md.read_text(encoding="utf-8"))
    if fm is None:
        return False, [f"{folder.name}: SKILL.md has no YAML frontmatter"]
    name, desc = fm.get("name", ""), fm.get("description", "")
    if not NAME_RE.match(name) or len(name) > 64:
        problems.append(f"name {name!r} must be lowercase words joined by hyphens, max 64 chars")
    if name != folder.name:
        problems.append(f"name {name!r} must match folder {folder.name!r}")
    if not desc or len(desc) > 1024:
        problems.append(f"description must be 1-1024 chars (is {len(desc)})")
    if "<" in desc or ">" in desc:
        problems.append("description must not contain angle brackets")
    if len(fm.get("compatibility", "")) > 500:
        problems.append("compatibility must be 500 chars or fewer")
    extra = set(fm) - ALLOWED
    if extra:
        problems.append(f"unexpected frontmatter keys: {sorted(extra)}")
    lines = body.count("\n")
    if lines > 500:
        problems.append(f"body is {lines} lines; keep SKILL.md under 500 and move detail to references/")
    for ref in sorted(set(re.findall(r"`((?:references|scripts)/[\w./-]+)`", body))):
        if not (folder / ref).exists():
            problems.append(f"body mentions {ref}, which doesn't exist")
    if problems:
        return False, [f"{folder.name}: {p}" for p in problems]
    return True, [f"{folder.name}: {lines} body lines, description {len(desc)} chars"]


def main():
    skills = sorted(p for p in (ROOT / "skills").iterdir() if p.is_dir())
    problems = []
    for folder in skills:
        ok, result = check_skill(folder)
        print(("ok    " if ok else "FAIL  ") + "\nFAIL  ".join(result))
        problems += [] if ok else result

    market = ROOT / ".claude-plugin" / "marketplace.json"
    if market.exists():
        data = json.loads(market.read_text(encoding="utf-8"))
        for plugin in data.get("plugins", []):
            for path in plugin.get("skills", []):
                if not (ROOT / path / "SKILL.md").is_file():
                    problems.append(f"marketplace.json: {path} has no SKILL.md")
                    print(f"FAIL  marketplace.json: {path} has no SKILL.md")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
