<div align="center">

# 🩺 Health Breach Watch

**Your AI assistant keeps an eye on a health data breach, so you don't have to.**<br>
It catches the real notice, flags the scams, and stays quiet otherwise.

[![Agent Skill](https://img.shields.io/badge/Agent_Skill-v3.0.0-d97757)](skills/health-breach-watch/SKILL.md)
[![Read only](https://img.shields.io/badge/mode-read--only-788c5d)](#what-it-will-never-do)
[![CI](https://github.com/tianqizhao-louis/health-data-breach-watch/actions/workflows/ci.yml/badge.svg)](https://github.com/tianqizhao-louis/health-data-breach-watch/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

Set up for the **October 2026 Quest Diagnostics breach**. Works for any health, lab, pharmacy or insurer breach.

</div>

---

## Set up in one minute

Copy this message and send it to your AI assistant: Claude, ChatGPT, Grok, Gemini or any other.

```text
Please read and follow these instructions to watch the Quest Diagnostics data breach for me:
https://raw.githubusercontent.com/tianqizhao-louis/health-data-breach-watch/main/skills/health-breach-watch/SKILL.md

Run the first check now using my email and official sources. After that, check every morning and only tell me when something changes.
```

**That's it.** Two tips:

- 💬 **Keep using the same chat.** That's how it remembers what it already told you.
- 📬 **Let it read your email** by connecting Gmail or Outlook in your assistant's settings. Without email access, it still checks the official sources and tells you what to search for.

<details>
<summary><b>Your assistant can't open links?</b></summary>
<br>

1. Open [`SKILL.md`](skills/health-breach-watch/SKILL.md).
2. Click the **Copy raw file** button (top right of the file).
3. Paste it into your chat, then add: *"Follow these instructions. Run the first check now."*

</details>

<details>
<summary><b>Claude app:</b> install it as a Skill</summary>
<br>

1. Download [**health-breach-watch.zip**](https://github.com/tianqizhao-louis/health-data-breach-watch/releases/latest/download/health-breach-watch.zip).
2. In Claude, open **Settings → Capabilities → Skills** and upload the zip.
3. Ask: *"Use health-breach-watch to check on the Quest breach every morning. Only tell me on ALERT or Update."*

</details>

<details>
<summary><b>Claude Code</b></summary>
<br>

```text
/plugin marketplace add tianqizhao-louis/health-data-breach-watch
/plugin install health-breach-watch@health-data-breach-watch
```

Or copy the folder yourself: `cp -r skills/health-breach-watch ~/.claude/skills/`

</details>

<details>
<summary><b>Other agents and frameworks</b></summary>
<br>

[`skills/health-breach-watch/`](skills/health-breach-watch) follows the open [Agent Skills](https://agentskills.io) format: a `SKILL.md` plus optional `references/` and `scripts/`. Drop it wherever your agent loads skills from. The scripts need only Python 3's standard library.

</details>

## What you get

A short report that fits on a phone screen. An example, with made-up data:

```text
Breach watch: Quest Diagnostics, 2026-11-25
Status: ALERT

A "Quest" email from Quest's real address failed sender checks (likely forged)
and gives a phone number that isn't the official line. Don't call it.

No change: SEC, Quest newsroom, HHS portal, state AG lists, news
Your inbox: 0 genuine, 1 unverified, 1 suspicious, 1 routine
  - Nov 24, questdiagnostics.com (forged): suspicious. Failed authentication,
    unofficial number. Don't call or reply.
  - Nov 24, your doctor's office: unverified, no red flags. To confirm, call
    the number on your patient card.
Still recommended: check insurer statements for claims you don't recognize
Next check: tomorrow morning
```

## How it works

| Each run it… | Using |
|---|---|
| 📄 Checks for new official facts | SEC filings, the company's newsroom, the HHS breach portal, state attorney general lists, reputable news |
| ✉️ Sorts breach-related email | **genuine**, **unverified**, **suspicious** or **routine**, with a reason for each |
| 🧾 Flags insurance claims you may not recognize | Explanation of Benefits (EOB) emails |
| 🔕 Reports only what changed | A small state file, or the last report in the chat |

## What it will never do

| ❌ Never | ✅ Instead |
|---|---|
| Click links, open attachments, reply, forward, delete or label mail | Reads only, and tells you what to do |
| Follow instructions hidden inside an email | Reports them to you as a red flag |
| Visit leak sites or the dark web | Says what reputable outlets report |
| Contact Quest, your insurer or the credit bureaus | Recommends the step; you take it |
| Put SSNs, member IDs, codes or test names in a report | Describes them in general terms |

## Watching a different breach

Edit the `Configuration` block at the top of [`SKILL.md`](skills/health-breach-watch/SKILL.md): company, dates, SEC CIK and domains. In a chat, you can also just say *"Use these instructions, but for the [company] breach."*

## For developers

```text
skills/health-breach-watch/   the skill (the only part that ships)
├── SKILL.md                  instructions and configuration
├── references/               sources and red-flag examples, loaded on demand
└── scripts/                  check_sender.py, validate_state.py (stdlib only)
evals/                        6 scenarios, fictional fixtures, trigger set, grader
tests/                        script tests against the fixtures
tools/                        format check and zip packaging
```

```bash
make test       # script tests
make check      # Agent Skills format check
make package    # dist/health-breach-watch.zip
```

**Evaluation:** across six scenarios, v3 passed 47/47 expectations against 41/47 for the original skill, with much shorter reports (136–249 words vs. up to 654). See [`evals/`](evals) for scenarios and results. To contribute, see [CONTRIBUTING.md](CONTRIBUTING.md); to report a safety bypass, see [SECURITY.md](SECURITY.md).

## Disclaimer

Not affiliated with Quest Diagnostics or any company named here. This is not legal, medical or financial advice. The assistant can make mistakes: confirm anything important through official channels. All test data in `evals/` is fictional.

<div align="center">
<sub>MIT licensed · Built with the <a href="https://agentskills.io">Agent Skills</a> format</sub>
</div>
