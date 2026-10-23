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

Last full model run: v2.1 against the v1 baseline, scenarios 1 to 4, one run each.

| | v2.1 | v1 baseline |
|---|---|---|
| Expectations passed | **36 / 36** | 33 / 36 |
| Report length | 125–245 words | 238–636 words |
| Mean time per run | 71 s | 81 s |
| Mean tokens per run | ~70k | ~65k |

v1's misses: claim details (item and dollar amounts) in a lock-screen report, and two reports over the word limit.

Triggering (v2.1 description): fired on about 3 of 9 clear requests with no false triggers on 10 near misses. Name the skill explicitly in scheduled tasks.

**Not yet re-run on v3.0:** scenarios 5 and 6 are new, and v3.0's merged changes have been checked by `tests/` and `grade.py` only, not by a full model run.
