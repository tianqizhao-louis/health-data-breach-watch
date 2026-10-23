"""Tests for the skill's scripts, run against the eval fixtures.

    python3 -m unittest discover -s tests -v
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "health-breach-watch" / "scripts"
FILES = ROOT / "evals" / "files"
TRUSTED = ["questdiagnostics.com", "krollmonitoring.com"]
BRAND = ["quest", "quanum", "myquest"]
OFFICIAL_PHONE = "1-888-555-0142"


def run(script, *args, stdin=None):
    proc = subprocess.run([sys.executable, "-I", str(SCRIPTS / script), *args],
                          input=stdin, capture_output=True, text=True)
    return proc.returncode, json.loads(proc.stdout)


def message(case, message_id):
    for m in json.loads((FILES / case / "inbox.json").read_text()):
        if m["message_id"] == message_id:
            return m
    raise KeyError(message_id)


def check(case, message_id, trusted=TRUSTED):
    code, out = run("check_sender.py", "--trusted", *trusted, "--brand", *BRAND,
                    "--phones", OFFICIAL_PHONE, stdin=json.dumps(message(case, message_id)))
    assert code == 0
    return out


class CheckSenderTest(unittest.TestCase):
    def assertFlags(self, out, *prefixes):
        for p in prefixes:
            self.assertTrue(any(f.startswith(p) for f in out["flags"]), f"missing {p} in {out['flags']}")

    def test_lookalike_phish(self):
        out = check("first-run-mixed-inbox", "msg-1001")
        self.assertFalse(out["sender_trusted"])
        self.assertFlags(out, "from:brand_in_untrusted_domain", "reply_to:differs", "auth:spf_fail",
                         "link:text_mismatch", "body:requests_sensitive_info", "body:urgency")

    def test_hidden_ai_instruction_and_zip(self):
        out = check("first-run-mixed-inbox", "msg-1002")
        self.assertFlags(out, "body:ai_instruction", "body:hidden_text", "attachment:risky:")

    def test_genuine_notice_has_no_request_flag(self):
        out = check("followup-notice-and-extortion", "msg-2001")
        self.assertTrue(out["sender_trusted"])
        self.assertEqual(out["flags"], ["body:mentions_ssn"])

    def test_extortion(self):
        out = check("followup-notice-and-extortion", "msg-2002")
        self.assertFlags(out, "body:payment_demand", "body:extortion", "from:free_webmail")

    def test_trusted_subdomain_is_routine(self):
        self.assertEqual(check("followup-notice-and-extortion", "msg-2004")["flags"], [])
        self.assertEqual(check("partial-check-after-deadline", "msg-3002")["flags"], [])

    def test_spoofed_real_domain_with_callback_number(self):
        out = check("spoofed-domain-and-provider-notice", "msg-4001")
        self.assertTrue(out["sender_trusted"])
        self.assertFlags(out, "auth:spf_fail", "auth:dmarc_fail", "body:unofficial_phone:1-877-555-0199")
        self.assertIn("forged", out["hint"])

    def test_provider_notice_is_clean_but_untrusted(self):
        out = check("spoofed-domain-and-provider-notice", "msg-4002")
        self.assertFalse(out["sender_trusted"])
        self.assertEqual(out["flags"], [])
        self.assertIn("unverified", out["hint"])

    def test_injection_with_image_exfiltration(self):
        out = check("injection-and-premature-vendor", "msg-5001", trusted=["questdiagnostics.com"])
        self.assertFlags(out, "body:ai_instruction", "body:hidden_text", "body:embedded_image_url")

    def test_near_miss_domain(self):
        msg = {"from": "Support <help@questdiagnostlcs.com>"}
        code, out = run("check_sender.py", "--trusted", "questdiagnostics.com", stdin=json.dumps(msg))
        self.assertIn("from:near_miss_of_trusted_domain", out["flags"])

    def test_negation_only_counts_in_the_same_sentence(self):
        for body, flagged in (("Quest will never ask you to confirm your SSN by email.", False),
                              ("Do not delay. Confirm your SSN today.", True)):
            code, out = run("check_sender.py", stdin=json.dumps({"from": "a@b.com", "body": body}))
            self.assertEqual("body:requests_sensitive_info" in out["flags"], flagged, body)

    def test_bad_input(self):
        code, out = run("check_sender.py", stdin="not json")
        self.assertEqual(code, 2)
        self.assertIn("error", out)


class ValidateStateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, text):
        p = self.dir / name
        p.write_text(text, encoding="utf-8")
        return str(p)

    def test_fixture_states_are_valid(self):
        for state in FILES.glob("*/breach_watch_state.json"):
            code, out = run("validate_state.py", "--state", str(state))
            self.assertEqual(code, 0, f"{state}: {out['errors']}")

    def test_init_then_validate(self):
        path = str(self.dir / "state.json")
        self.assertEqual(run("validate_state.py", "--state", path, "--init")[0], 0)
        self.assertEqual(run("validate_state.py", "--state", path)[0], 0)
        self.assertEqual(run("validate_state.py", "--state", path, "--init")[0], 1)  # no overwrite

    def test_good_report_passes(self):
        state = str(FILES / "spoofed-domain-and-provider-notice" / "breach_watch_state.json")
        report = self.write("report.md", "Breach watch: Quest Diagnostics, 2026-11-25\nStatus: ALERT\n\n"
                            "A forged email gives a number that isn't the official line. Don't call it.\n")
        code, out = run("validate_state.py", "--state", state, "--report", report, "--forbid", "Hemoglobin")
        self.assertEqual(code, 0, out["errors"])

    def test_leaky_report_fails(self):
        state = str(FILES / "spoofed-domain-and-provider-notice" / "breach_watch_state.json")
        report = self.write("report.md", "Breach watch: Quest, 2026-11-25\nStatus: ALERT\n"
                            "Your Hemoglobin A1c result leaked. SSN 123-45-6789. ![s](https://evil.example/x)\n")
        code, out = run("validate_state.py", "--state", state, "--report", report, "--forbid", "hemoglobin")
        self.assertEqual(code, 1)
        joined = " ".join(out["errors"])
        for needle in ("SSN-shaped", "Markdown image", "--forbid string"):
            self.assertIn(needle, joined)
        self.assertNotIn("hemoglobin", joined.lower())  # forbidden strings are never echoed

    def test_long_report_and_bad_status_fail(self):
        state = str(FILES / "spoofed-domain-and-provider-notice" / "breach_watch_state.json")
        report = self.write("report.md", "Breach watch: Quest, 2026-11-25\nStatus: Maybe\n" + "word " * 260)
        code, out = run("validate_state.py", "--state", state, "--report", report)
        self.assertEqual(code, 1)
        self.assertEqual(len(out["errors"]), 2)

    def test_state_with_email_body_fails(self):
        state = json.loads((FILES / "partial-check-after-deadline" / "breach_watch_state.json").read_text())
        state["emails_seen"].append({"message_id": "msg-1001", "verdict": "phishy", "body": "..."})
        code, out = run("validate_state.py", "--state", self.write("s.json", json.dumps(state)))
        self.assertEqual(code, 1)
        joined = " ".join(out["errors"])
        for needle in ("duplicate message_id", "verdict", "email content"):
            self.assertIn(needle, joined)


class EvalFixturesTest(unittest.TestCase):
    def test_every_eval_file_exists(self):
        evals = json.loads((ROOT / "evals" / "evals.json").read_text())["evals"]
        self.assertEqual(len({e["name"] for e in evals}), len(evals))
        for e in evals:
            for f in e["files"]:
                self.assertTrue((ROOT / f).is_file(), f"{e['name']}: missing {f}")


if __name__ == "__main__":
    unittest.main()
