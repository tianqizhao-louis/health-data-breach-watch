#!/usr/bin/env python3
"""Check health-breach-watch state and report files before a report is sent.

State: valid JSON, required keys, known verdicts, unique message IDs, no
fields that would hold email content or personal data.
Report: header and status lines, the 250-word limit.
Both: no SSN-shaped numbers, no embedded images, none of the --forbid strings
(member IDs, enrollment codes, test names you saw this run; compared locally,
never stored or printed).

Usage:
  python3 validate_state.py --state breach_watch_state.json [--report report.md] [--forbid S ...]
  python3 validate_state.py --state breach_watch_state.json --init [--domain questdiagnostics.com]

Exit codes: 0 no errors, 1 errors found, 2 bad usage.
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime

REQUIRED_KEYS = {
    "last_run", "confirmed_company_domains", "confirmed_notice_senders",
    "official_facts", "emails_seen", "notice_received", "user_actions_done",
}
OPTIONAL_KEYS = {
    "schema_version", "sources_unreachable", "eob_claims_flagged",
    "deadline_note_given", "known_providers",
}
VERDICTS = {"genuine", "unverified", "suspicious", "routine"}
ACTION_SLUGS = {
    "credit_freezes", "irs_ip_pin", "review_eobs", "portal_password_2fa",
    "email_2fa", "enroll_monitoring", "identitytheft_gov",
}
# Keys that would hold email content or personal data.
FORBIDDEN_FIELDS = {
    "body", "raw", "html", "snippet", "subject", "ssn", "member_id", "dob",
    "enrollment_code", "activation_code", "test_name", "test_result", "amount",
}
LEAK_PATTERNS = [
    (re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)"), "SSN-shaped number"),
    (re.compile(r"!\[[^\]]*\]\([^)]*\)"), "Markdown image"),
    (re.compile(r"<img\b", re.I), "HTML image tag"),
]
STATUS_RE = re.compile(r"^Status:\s*(ALERT|Update|Nothing new)\b")
MAX_WORDS = 250


def leaks(text, label, forbid):
    found = [f"{label} contains a {desc}" for rx, desc in LEAK_PATTERNS if rx.search(text)]
    low = text.lower()
    for i, s in enumerate(forbid, 1):
        if s and s.lower() in low:
            found.append(f"{label} contains --forbid string #{i}")
    return found


def walk_keys(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield f"{path}.{k}" if path else k, k
            yield from walk_keys(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_keys(v, f"{path}[{i}]")


def check_state(path, forbid):
    errors, warnings = [], []
    try:
        raw = open(path, encoding="utf-8").read()
        data = json.loads(raw)
    except OSError as exc:
        return [f"can't read state: {exc}"], warnings, {}
    except ValueError as exc:
        return [f"state isn't valid JSON: {exc}"], warnings, {}
    if not isinstance(data, dict):
        return ["state must be a JSON object"], warnings, {}

    errors += leaks(raw, "state", forbid)
    missing = REQUIRED_KEYS - data.keys()
    if missing:
        errors.append(f"state is missing keys: {sorted(missing)}")
    unknown = data.keys() - REQUIRED_KEYS - OPTIONAL_KEYS
    if unknown:
        warnings.append(f"state has extra keys (fine, but check they hold no personal data): {sorted(unknown)}")
    for where, key in walk_keys(data):
        if key.lower() in FORBIDDEN_FIELDS:
            errors.append(f"state field '{where}' looks like email content or personal data")

    last_run = data.get("last_run")
    if last_run is not None:
        try:
            datetime.fromisoformat(str(last_run).replace("Z", "+00:00"))
        except ValueError:
            errors.append(f"last_run isn't an ISO-8601 timestamp: {last_run!r}")

    seen_ids = set()
    for i, item in enumerate(data.get("emails_seen") or []):
        if not isinstance(item, dict):
            errors.append(f"emails_seen[{i}] must be an object")
            continue
        mid = item.get("message_id")
        if not mid:
            errors.append(f"emails_seen[{i}] has no message_id")
        elif mid in seen_ids:
            errors.append(f"emails_seen has a duplicate message_id: {mid}")
        seen_ids.add(mid)
        if item.get("verdict") not in VERDICTS:
            errors.append(f"emails_seen[{i}] verdict {item.get('verdict')!r} isn't one of {sorted(VERDICTS)}")

    for i, fact in enumerate(data.get("official_facts") or []):
        if not isinstance(fact, dict) or not {"date", "source", "fact"} <= fact.keys():
            errors.append(f"official_facts[{i}] needs date, source and fact")

    if not isinstance(data.get("notice_received", False), bool):
        errors.append("notice_received must be true or false")
    done = data.get("user_actions_done") or []
    odd = [a for a in done if a not in ACTION_SLUGS]
    if odd:
        warnings.append(f"user_actions_done has non-standard entries {odd}; known slugs: {sorted(ACTION_SLUGS)}")

    summary = {
        "last_run": last_run,
        "emails_seen": len(seen_ids),
        "official_facts": len(data.get("official_facts") or []),
        "notice_received": data.get("notice_received"),
        "actions_not_done": sorted(ACTION_SLUGS - set(done)),
    }
    return errors, warnings, summary


def check_report(path, forbid):
    errors, warnings = [], []
    try:
        text = open(path, encoding="utf-8").read()
    except OSError as exc:
        return [f"can't read report: {exc}"], warnings
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return ["report is empty"], warnings
    errors += leaks(text, "report", forbid)
    if not lines[0].startswith("Breach watch:"):
        errors.append("first line must be 'Breach watch: [company], [date]'")
    if len(lines) < 2 or not STATUS_RE.match(lines[1]):
        errors.append("second line must be 'Status: ALERT', 'Update', 'Nothing new' or 'Nothing new (partial check)'")
    words = len(text.split())
    if words > MAX_WORDS:
        errors.append(f"report is {words} words; the limit is {MAX_WORDS} (aim for about 150)")
    if re.search(r"https?://", text):
        warnings.append("report contains http(s):// links; write official addresses without a scheme and defang suspicious ones")
    return errors, warnings


def init_state(path, domains):
    if os.path.exists(path):
        print(json.dumps({"ok": False, "errors": [f"{path} already exists; not overwriting"]}))
        return 1
    state = {
        "schema_version": 3,
        "last_run": None,
        "confirmed_company_domains": domains,
        "confirmed_notice_senders": [],
        "official_facts": [],
        "sources_unreachable": [],
        "emails_seen": [],
        "eob_claims_flagged": [],
        "notice_received": False,
        "deadline_note_given": False,
        "known_providers": [],
        "user_actions_done": [],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
        f.write("\n")
    print(json.dumps({"ok": True, "created": path}))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--state", required=True, metavar="FILE")
    ap.add_argument("--report", metavar="FILE")
    ap.add_argument("--forbid", nargs="*", default=[], metavar="S",
                    help="strings that must not appear in either file (case-insensitive)")
    ap.add_argument("--init", action="store_true", help="write an empty first-run state and exit")
    ap.add_argument("--domain", nargs="*", default=["questdiagnostics.com"],
                    help="confirmed company domains for --init")
    args = ap.parse_args()

    if args.init:
        return init_state(args.state, args.domain)

    errors, warnings, summary = check_state(args.state, args.forbid)
    if args.report:
        r_errors, r_warnings = check_report(args.report, args.forbid)
        errors += r_errors
        warnings += r_warnings
    print(json.dumps({"ok": not errors, "errors": errors, "warnings": warnings, "summary": summary}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
