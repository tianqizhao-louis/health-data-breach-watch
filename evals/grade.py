#!/usr/bin/env python3
"""Run the mechanical checks from evals.json against one run's outputs.

Model-graded expectations (the "expectations" list) still need a grader;
this covers the parts a script can decide: status line, word count,
forbidden strings and state fields.

Usage:
  python3 evals/grade.py <eval name or id> <outputs dir containing report.md and breach_watch_state.json>

Exit codes: 0 all checks pass, 1 a check failed, 2 bad usage.
"""
import json
import re
import sys
from pathlib import Path

EVALS = Path(__file__).with_name("evals.json")


def grade(checks, out_dir):
    results = []
    report_path, state_path = out_dir / "report.md", out_dir / "breach_watch_state.json"
    report = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    state_raw = state_path.read_text(encoding="utf-8") if state_path.exists() else ""
    try:
        state = json.loads(state_raw) if state_raw else None
    except ValueError:
        state = None
    add = lambda name, ok, detail="": results.append({"check": name, "passed": bool(ok), "detail": detail})

    add("report.md exists", report)
    add("state is valid JSON", isinstance(state, dict))
    state = state if isinstance(state, dict) else {}

    if "status" in checks:
        m = re.search(r"^Status:\s*(.+?)\s*$", report, re.M)
        got = m.group(1) if m else ""
        add(f"status is {checks['status']}", got.startswith(checks["status"]), got)
    if "max_words" in checks:
        n = len(report.split())
        add(f"report <= {checks['max_words']} words", n <= checks["max_words"], f"{n} words")
    for s in checks.get("report_must_not_contain", []):
        add(f"report omits {s!r}", s.lower() not in report.lower())
    for s in checks.get("state_must_not_contain", []):
        add(f"state omits {s!r}", s.lower() not in state_raw.lower())
    for key, want in checks.get("state_equals", {}).items():
        add(f"state.{key} == {want!r}", state.get(key) == want, repr(state.get(key)))
    for key, prefix in checks.get("state_startswith", {}).items():
        add(f"state.{key} starts with {prefix!r}", str(state.get(key, "")).startswith(prefix), repr(state.get(key)))
    for key, items in checks.get("state_list_contains", {}).items():
        have = " | ".join(map(str, state.get(key) or [])).lower()
        for item in items:
            add(f"state.{key} includes {item!r}", item.lower() in have)
    for key, items in checks.get("state_list_excludes", {}).items():
        have = " | ".join(map(str, state.get(key) or [])).lower()
        for item in items:
            add(f"state.{key} excludes {item!r}", item.lower() not in have)
    ids = {e.get("message_id") for e in state.get("emails_seen") or [] if isinstance(e, dict)}
    for mid in checks.get("state_has_message_ids", []):
        add(f"emails_seen has {mid}", mid in ids)
    return results


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    key, out_dir = sys.argv[1], Path(sys.argv[2])
    evals = json.loads(EVALS.read_text(encoding="utf-8"))["evals"]
    match = [e for e in evals if e["name"] == key or str(e["id"]) == key]
    if not match:
        print(f"no eval named {key!r}; choose from {[e['name'] for e in evals]}")
        return 2
    results = grade(match[0].get("checks", {}), out_dir)
    for r in results:
        print(f"{'PASS' if r['passed'] else 'FAIL'}  {r['check']}" + (f"  ({r['detail']})" if r["detail"] else ""))
    passed = sum(r["passed"] for r in results)
    print(f"\n{passed}/{len(results)} mechanical checks passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
