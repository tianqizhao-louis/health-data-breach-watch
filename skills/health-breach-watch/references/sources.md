# Official sources

Read this in step 2. Sources are listed in order of authority: when two disagree, the higher one wins, and a news report never overrides a filing. Give each source one outcome per run: **new fact**, **no change** or **couldn't check** (with the reason).

## Contents

1. SEC EDGAR
2. Company newsroom
3. HHS OCR breach portal
4. State attorney general lists
5. News outlets
6. What counts as confirming a vendor

## 1. SEC EDGAR

- Filing list: `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001022079&type=8-K&count=40`
- Machine-readable: `https://data.sec.gov/submissions/CIK0001022079.json` (look at `filings.recent`)
- Fallback: a web search for `site:sec.gov Quest Diagnostics 8-K Quanum`

Look for an **8-K/A** amending the October 22, 2026 filing. Amendments usually add the affected count, data types and financial impact. Later 10-Q or 10-K filings may add legal proceedings or regulatory inquiries.

Quirk: SEC blocks requests without a descriptive User-Agent (one with a contact email). A 403, a captcha page or an empty list means **couldn't check**. If a fallback search shows only filings already in state, say that, but still report SEC as couldn't check.

## 2. Company newsroom

- `newsroom.questdiagnostics.com` and any incident page on `questdiagnostics.com`

Extract: the systems affected, the dedicated call-center number, the named notice or monitoring vendor, its sending domain, the enrollment site, how long monitoring lasts, and whether notices go by mail, email or both. Each of these goes into `confirmed_notice_senders` once published.

Quirk: incident pages are often edited in place. Compare against the facts in state, not against the page's own "updated" date.

## 3. HHS OCR breach portal

- `https://ocrportal.hhs.gov/ocr/breach/breach_report.jsf`
- Search the covered entity name. Also check business-associate entries: Quest may be listed under a client health system.

A covered entity must report a breach affecting 500 or more people within 60 days of discovery (45 CFR 164.408). Law enforcement can lawfully delay notice (45 CFR 164.412), and Quest told the SEC it had notified federal law enforcement. Postings often appear weeks after letters go out, so an empty result means **not posted yet**, never "not a breach".

## 4. State attorney general lists

Several states post the **sample notice letter**, which shows the exact data types and the real vendor, enrollment site and phone number. That makes them the best way to confirm a vendor.

| State | Where | What it adds |
|---|---|---|
| California | `oag.ca.gov/privacy/databreach/list` | Sample letter PDF (500+ CA residents) |
| Maine | `maine.gov/agviewer/content/ag/985235c7-cb95-4be2-8792-a1252b4f8318/list.html` | Total affected, state count, breach dates, sample letter |
| Massachusetts | mass.gov "data breach notification reports" | Whether SSNs or financial data were involved |
| Texas | `oag.texas.gov` data security breach reports | Data categories, Texas count |
| Washington | `atg.wa.gov/data-breach-notifications` | Sample letter, data types |
| Vermont, Oregon, Indiana | Each AG's site, "security breach notices" | Sample letters |

Check the user's own state first if it publishes a list (Ohio, for example, doesn't). If a URL has moved, search for "[state] attorney general data breach list".

## 5. News outlets

Use AP, Reuters, the Wall Street Journal, the New York Times, Bloomberg, HIPAA Journal, BleepingComputer, DataBreaches.net, SC Media and Fierce Healthcare. A summary that repeats a filing isn't a new fact; cite the filing.

- **Leak claims:** if an outlet reports that an extortion group claims the data or posted samples, record what the outlet says, including whether it verified the samples. Never follow its link to the leak site.
- **Unsourced numbers:** forum posts and social media ("tens of millions") aren't facts. Mention one only to say it's unverified.
- **Recycled numbers:** recaps often quote the 2019 AMCA breach (about 11.9M Quest patients). Check that a figure belongs to the 2026 Quanum incident before using it.

## 6. What counts as confirming a vendor

A vendor, sending domain, enrollment site or phone number is confirmed only when one of sources 1 to 4 names it for this incident. An email naming its own vendor confirms nothing. Until then, a monitoring email with no other red flags is **unverified**. If it names a different vendor, site or number than the official one, it is **suspicious**.
