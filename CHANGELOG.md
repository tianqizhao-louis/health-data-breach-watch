# Changelog

## 3.0.0 (2026-10-23)

Merged the two v2 revisions into one skill.

- **From v2.1:** the four-way verdict (genuine, unverified, suspicious, routine), "couldn't check" outcomes and partial-check status, the overlapping search window, Gotchas, `known_providers`, the 250-word report limit, `check_sender.py`.
- **From v2.0.0:** image-exfiltration defense (no images or links from email in reports, defanged suspicious domains), reduced mode without mail access, syncing user-reported actions at the start of a run, standard action slugs, `validate_state.py` as a privacy gate before sending, worked red-flag examples, the near-miss trigger set.
- **New:** `check_sender.py` flags callback numbers that differ from the official line, near-miss domains, hidden text and embedded image URLs. `validate_state.py --forbid` checks a report for the exact sensitive strings seen that run. Prompt-injection emails now raise ALERT. Two new eval scenarios (injection with a premature vendor; no mail access). The skill now works when `SKILL.md` is pasted into a chat on its own.

## 2.1

Spec-compliant frontmatter, Gotchas, the "unverified" verdict, `check_sender.py`, `references/sources.md`. Passed 36/36 expectations against 33/36 for v1.

## 1.0

The original skill.
