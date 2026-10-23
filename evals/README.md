# Evals

Every fixture here is **fictional**. Counts, vendors, phone numbers (555 numbers), codes, people and emails were invented for testing and say nothing about the real incident.

| File | What it is |
|---|---|
| `evals.json` | Six scenarios: prompt, input files, model-graded `expectations` and script-graded `checks` |
| `files/` | Simulated inboxes, source snapshots and prior state for each scenario |
| `trigger-evals.json` | 24 queries (12 should trigger, 12 near misses), split into train and validation |
| `grade.py` | Runs the script-graded `checks` on one run's outputs |
| `baseline/v1-SKILL.md` | The original skill, kept as the comparison baseline |

## Scenarios

| # | Scenario | What it tests |
|---|---|---|
| 1 | `first-run-mixed-inbox` | Baseline run: lookalike phish, hidden AI instructions, class-action ad, unfamiliar EOB claim, a recycled 2019 breach count |
| 2 | `followup-notice-and-extortion` | Genuine vendor notice, crypto extortion, off-brand monitoring offer, leak-site claim, deduping, user-reported action |
| 3 | `partial-check-after-deadline` | Unreachable SEC source, HIPAA deadline passed, report length |
| 4 | `spoofed-domain-and-provider-notice` | Forged real domain with a callback number, doctor's-office notice, "my aunt got hers" |
| 5 | `injection-and-premature-vendor` | Hidden prompt injection with an image-exfiltration payload, vendor not yet confirmed |
| 6 | `no-mail-access` | Mail connector missing: partial check, queries handed to the user |

## Running

1. Give an agent the skill (`skills/health-breach-watch/`, without this folder) plus a scenario's `prompt` and `files`.
2. Save its `report.md` and `breach_watch_state.json` to an outputs folder.
3. Grade:
   ```bash
   python3 evals/grade.py first-run-mixed-inbox path/to/outputs
   ```
4. Have a model grade the `expectations` against the report, state and transcript.

The [skill-creator](https://github.com/anthropics/skills) skill automates the with-skill vs. baseline comparison and the review viewer.

## Results

Last full model run: v3.0.0 against the v1 baseline, all six scenarios, one run each (2026-10-23).

| | v3.0 | v1 baseline |
|---|---|---|
| Expectations passed (model-graded) | **47 / 47** | 41 / 47 |
| Script checks passed (`grade.py`) | **74 / 74** | 62 / 74 |
| Report length | 136–249 words | 268–654 words |
| Mean time per run | 57 s | 56 s |
| Mean tokens per run | ~53k | ~45k |

v1's misses: claim details (item and dollar amount) in a lock-screen report; "Update" instead of ALERT for a forged callback email and for a prompt-injection email; no "partial check" status; no search queries when mail was unavailable; never telling the user that hidden AI instructions were ignored; every report over the word limit.

Both versions classify phishing, extortion and genuine notices correctly, so those expectations don't discriminate. In two v3 runs, `validate_state.py` caught a first draft over 250 words and the agent trimmed it.

Earlier run, v2.1 against v1 on scenarios 1 to 4: 36/36 vs. 33/36.

Triggering (v2.1 description): fired on about 3 of 9 clear requests with no false triggers on 10 near misses. Name the skill explicitly in scheduled tasks.
