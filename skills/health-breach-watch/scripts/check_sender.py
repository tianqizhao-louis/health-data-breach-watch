#!/usr/bin/env python3
"""Mechanical red-flag checks on one email for the health-breach-watch skill.

Reads one message as JSON (stdin, or --message FILE) and prints JSON findings.
The flags are evidence for the agent's verdict, not the verdict itself.
Standard library only; never fetches anything.

Input fields, all optional:
  from          "Display Name <user@example.com>"
  reply_to      "user@example.com"
  auth_results  "spf=pass dkim=pass dmarc=pass"
  links         [{"text": "...", "href": "..."}]
  attachments   ["file.pdf", ...]
  body          plain text or HTML

Example:
  python3 check_sender.py --trusted questdiagnostics.com krollmonitoring.com \\
      --brand quest quanum myquest --phones 1-888-555-0142 < message.json

Exit codes: 0 checked, 2 bad input.
"""
import argparse
import json
import re
import sys
from email.utils import parseaddr
from urllib.parse import urlparse

FREE_MAIL = {
    "gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "live.com",
    "yahoo.com", "aol.com", "icloud.com", "me.com", "proton.me",
    "protonmail.com", "gmx.com", "gmx.net", "mail.com", "yandex.com", "zoho.com",
}
SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "rb.gy", "cutt.ly"}
RISKY_EXT = {
    "zip", "rar", "7z", "gz", "iso", "img", "html", "htm", "shtml", "svg", "js",
    "exe", "scr", "msi", "lnk", "hta", "vbs", "bat", "cmd", "ps1", "jar", "one",
    "docm", "xlsm", "pptm", "dotm", "xlam",
}
# Second-level labels used under country codes, e.g. example.co.uk.
CC_SECOND_LEVEL = {"co", "com", "org", "net", "gov", "ac", "edu"}

SENSITIVE = (r"ssn|social security(?: number)?|password|passcode|date of birth|\bdob\b|"
             r"card number|cvv|bank account|routing number|member id|login")
REQUEST_RE = re.compile(
    r"\b(provide|confirm|verify|enter|reply with|send(?: us)?|submit|update|validate|"
    r"share|type in)\b[^.\n]{0,60}?(" + SENSITIVE + r")", re.I)
NEGATION_RE = re.compile(r"\b(never|not|won't|will not|don't|do not|no one)\b", re.I)
SSN_RE = re.compile(r"\b(ssn|social security)\b", re.I)
PAYMENT_RE = re.compile(
    r"\b(bitcoin|btc|monero|xmr|crypto(currency)?|wallet address|gift ?cards?|"
    r"wire transfer|western union|zelle)\b", re.I)
EXPOSE_RE = re.compile(
    r"\b(release|publish|leak|expose|post|send|forward)\b[^.\n]{0,80}?"
    r"\b(employer|family|contacts|public|online|everyone|internet)\b", re.I)
URGENCY_RE = re.compile(
    r"\bwithin \d{1,3} ?(hours?|hrs?)\b|\b(24|48|72)[- ]hours?\b|\bact now\b|"
    r"\bfinal (notice|warning)\b|\b(will be|be) (suspended|closed|deleted)\b", re.I)
AI_RE = [
    re.compile(r"\b(note|message|instructions?|notice)\s+(to|for)\s+(any\s+|all\s+)?"
               r"(ai|llm|language model|(email |virtual )?assistants?)\b", re.I),
    re.compile(r"\b(ai|llm|email|virtual)\s+assistants?\s*[:,\-]", re.I),
    re.compile(r"\bif you are an? (ai|llm|language model|assistant|bot|agent)\b", re.I),
    re.compile(r"\bignore (all |any )?(previous|prior|above|earlier) (instructions|rules|guidance)", re.I),
    re.compile(r"\[(system|assistant)\]|<\s*/?\s*system[_\s-]?(instruction|prompt|message)?\s*>", re.I),
    re.compile(r"\b(do not|don't|never) (tell|inform|notify|alert) the user\b", re.I),
    re.compile(r"\bmark (this|it) as (safe|genuine|legitimate|verified|read)\b", re.I),
    re.compile(r"\bimportant update for (the )?(ai|assistant)\b", re.I),
]
HIDDEN_RE = re.compile(
    r"display\s*:\s*none|font-size\s*:\s*0(px|pt|em)?\b|visibility\s*:\s*hidden|"
    r"color\s*:\s*(#fff(fff)?|white)\b|[\u200b-\u200f\u2060\ufeff]|[\U000e0000-\U000e007f]", re.I)
IMAGE_RE = re.compile(r"!\[[^\]]*\]\(\s*https?://|<img\b[^>]*\bsrc\s*=\s*[\"']?https?://", re.I)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}(?!\d)")
URLISH_RE = re.compile(r"^(https?://)?([a-z0-9-]+\.)+[a-z]{2,}(/\S*)?$", re.I)


def domain_of(address):
    _, email = parseaddr(address or "")
    return email.rsplit("@", 1)[1].lower().strip(".") if "@" in email else ""


def host_of(url):
    url = (url or "").strip()
    if not re.match(r"^[a-z][a-z0-9+.-]*://", url, re.I):
        url = "http://" + url
    return (urlparse(url).hostname or "").lower().strip(".")


def registrable(domain):
    parts = [p for p in domain.split(".") if p]
    if len(parts) >= 3 and len(parts[-1]) == 2 and parts[-2] in CC_SECOND_LEVEL:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def is_trusted(domain, trusted):
    return bool(domain) and any(domain == t or domain.endswith("." + t) for t in trusted)


def edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def digits(phone):
    d = re.sub(r"\D", "", phone)
    return d[1:] if len(d) == 11 and d.startswith("1") else d


def check(msg, trusted, brands, phones):
    flags = []
    display, _ = parseaddr(msg.get("from") or "")
    from_domain = domain_of(msg.get("from"))
    trusted_sender = is_trusted(from_domain, trusted)
    flat = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())

    if not from_domain:
        flags.append("from:missing")
    elif not trusted_sender:
        if any(b in flat(display) for b in brands):
            flags.append("from:display_name_claims_brand")
        if any(b in flat(from_domain) for b in brands):
            flags.append("from:brand_in_untrusted_domain")
        reg = registrable(from_domain)
        if any(0 < edit_distance(reg, registrable(t)) <= 2 for t in trusted):
            flags.append("from:near_miss_of_trusted_domain")
        if reg in FREE_MAIL:
            flags.append("from:free_webmail")

    reply_domain = domain_of(msg.get("reply_to"))
    if reply_domain and from_domain and registrable(reply_domain) != registrable(from_domain):
        flags.append("reply_to:differs")

    for mech, result in re.findall(r"\b(spf|dkim|dmarc)\s*=\s*(\w+)", msg.get("auth_results") or "", re.I):
        result = result.lower()
        if result in ("fail", "softfail", "permerror"):
            flags.append(f"auth:{mech.lower()}_fail")
        elif result == "none" and mech.lower() in ("dkim", "dmarc"):
            flags.append(f"auth:{mech.lower()}_missing")

    for link in msg.get("links") or []:
        text, href = (link.get("text") or "").strip(), link.get("href") or ""
        target = host_of(href)
        if not target:
            continue
        if URLISH_RE.match(text) and registrable(host_of(text)) != registrable(target):
            flags.append(f"link:text_mismatch:{target}")
        if re.fullmatch(r"[\d.]+", target) or registrable(target) in SHORTENERS:
            flags.append(f"link:ip_or_shortener:{target}")
        elif trusted and not is_trusted(target, trusted):
            flags.append(f"link:untrusted_target:{target}")

    for name in msg.get("attachments") or []:
        if name.lower().rsplit(".", 1)[-1] in RISKY_EXT:
            flags.append(f"attachment:risky:{name}")

    body = msg.get("body") or ""
    for m in REQUEST_RE.finditer(body):
        before = re.split(r"[.!?\n]", body[max(0, m.start() - 50):m.start()])[-1]
        if not NEGATION_RE.search(before + m.group(1)):
            flags.append("body:requests_sensitive_info")
            break
    if SSN_RE.search(body):
        flags.append("body:mentions_ssn")
    payment = bool(PAYMENT_RE.search(body))
    if payment:
        flags.append("body:payment_demand")
    if EXPOSE_RE.search(body) and (payment or URGENCY_RE.search(body)):
        flags.append("body:extortion")
    if URGENCY_RE.search(body):
        flags.append("body:urgency")
    if any(r.search(body) for r in AI_RE):
        flags.append("body:ai_instruction")
    if HIDDEN_RE.search(body):
        flags.append("body:hidden_text")
    if IMAGE_RE.search(body):
        flags.append("body:embedded_image_url")

    found = sorted({m.group(0).strip() for m in PHONE_RE.finditer(body)})
    official = {digits(p) for p in phones}
    if official:
        for p in found:
            if digits(p) not in official:
                flags.append(f"body:unofficial_phone:{p}")

    auth_failed = any(f.startswith("auth:") and f.endswith("_fail") for f in flags)
    if trusted_sender and auth_failed:
        hint = "Domain matches but authentication failed: treat the sender as forged (suspicious)."
    elif trusted_sender and not flags:
        hint = "Mechanical checks pass. Still read the content (step 3) before calling it genuine."
    elif trusted_sender:
        hint = "Trusted domain with flags: read each flag in context before deciding."
    elif flags:
        hint = "Untrusted sender with red flags: likely suspicious."
    else:
        hint = "No mechanical red flags, but the sender isn't confirmed: unverified unless an official source names it."

    return {
        "from_domain": from_domain,
        "sender_trusted": trusted_sender,
        "flags": flags,
        "phones_found": found,
        "hint": hint,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--trusted", nargs="*", default=[], metavar="DOMAIN",
                    help="confirmed company and notice-sender domains (subdomains count)")
    ap.add_argument("--brand", nargs="*", default=[], metavar="WORD",
                    help="brand words that shouldn't appear in untrusted senders")
    ap.add_argument("--phones", nargs="*", default=[], metavar="NUMBER",
                    help="official phone numbers; any other number in the body is flagged")
    ap.add_argument("--message", metavar="FILE", help="read the message from FILE instead of stdin")
    args = ap.parse_args()

    try:
        raw = open(args.message, encoding="utf-8").read() if args.message else sys.stdin.read()
        msg = json.loads(raw)
        if not isinstance(msg, dict):
            raise ValueError("message must be a JSON object")
    except (OSError, ValueError) as exc:
        print(json.dumps({"error": f"bad input: {exc}"}))
        return 2

    trusted = [t.lower().strip(".") for t in args.trusted]
    brands = [re.sub(r"[^a-z0-9]", "", b.lower()) for b in args.brand if b.strip()]
    print(json.dumps(check(msg, trusted, brands, args.phones), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
