"""Check every quote in a draft before you publish it. No AI model and no API key needed.

    python examples/check_draft.py my-post.md
    python examples/check_draft.py https://example.com/some-article/
    cat my-post.md | python examples/check_draft.py -
    python examples/check_draft.py my-post.md --json

It finds the quotes in the text (anything in “curly” or "straight" double quotes, five words or
longer, plus Markdown blockquotes), notes the name the draft gives each one ("As Emerson said",
"— Gandhi"), checks the words with the same tool an agent would use, and reports:

    FIX         the quote is wrongly credited, or credited without a hedge when nobody reliable said it
    CHECK       only part of the wording matches a checked quote: confirm it is the same line
    UNVERIFIED  no checked record either way: don't present the attribution as confirmed
    OK          the record backs the quote and the name the draft gives it

Each problem comes with a suggested fix and a link to the evidence.
Exit code: 1 if anything is FIX (use --strict to fail on CHECK and UNVERIFIED too), so it can gate
a publish step, e.g. in a GitHub Action.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import time
import urllib.request
from typing import Dict, List, Optional

from langchain_graciousquotes import QuoteAttributionCheck

MIN_WORDS = 5
QUOTED = re.compile(r"[“\"]([^”\"]{20,600})[”\"]")
BLOCKQUOTE = re.compile(r"(?m)((?:^>[^\n]*\n?)+)")
DASH_NAME = re.compile(r"^\s*[—–-]{1,2}\s*([^\n,(]{2,60})")
NAME = re.compile(r"\b([A-Z][a-zA-Z.'’-]+(?:\s+(?:[A-Z][a-zA-Z.'’-]+|de|da|van|von|du|le|la|of))*)")
HEDGES = ("attributed", "supposedly", "reportedly", "credited", "is said to", "allegedly", "apocryphal")
NOT_NAMES = {
    "A", "An", "And", "As", "At", "But", "By", "Finally", "For", "He", "Her", "His", "I", "If", "In", "It",
    "My", "Not", "Of", "On", "One", "Or", "Our", "She", "So", "That", "The", "Then", "There", "They", "This",
    "To", "We", "When", "Why", "You", "Yet", "Once", "Here", "Some", "Even", "Also", "Still", "Today",
}
OK_STATUSES = ("Verified", "Plausible", "Traditional saying")
ORDER = {"FIX": 0, "CHECK": 1, "UNVERIFIED": 2, "OK": 3}


# --------------------------------------------------------------------------- reading the draft
def load(source: str) -> str:
    if source == "-":
        return sys.stdin.read()
    if source.startswith(("http://", "https://")):
        req = urllib.request.Request(source, headers={"User-Agent": "langchain-graciousquotes example"})
        page = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "replace")
        page = re.sub(r"(?is)<(script|style|nav|footer|header)[^>]*>.*?</\1>", " ", page)
        page = re.sub(r"(?i)<blockquote[^>]*>", "\n> ", page)
        page = re.sub(r"(?i)</(p|div|li|h[1-6]|blockquote)>|<br\s*/?>", "\n", page)
        return html.unescape(re.sub(r"<[^>]+>", " ", page))
    with open(source, encoding="utf-8") as f:
        return f.read()


def credited_name(before: str, after: str) -> Optional[str]:
    """The name the draft gives a quote: '— Name' after it, or the last name in the same sentence before it."""
    m = DASH_NAME.match(after)
    if m:
        return m.group(1).strip().rstrip(".")
    sentence = re.split(r"(?<=[.!?])\s+|\n\n", before)[-1]
    names = [n for n in NAME.findall(sentence) if n.split()[0] not in NOT_NAMES or len(n.split()) > 1]
    names = [" ".join(w for w in n.split() if w not in NOT_NAMES) for n in names]
    return names[-1] if names and names[-1] else None


def find_quotes(text: str) -> List[Dict[str, object]]:
    """Each quote of five words or more, with the name the draft credits and whether it hedges."""
    found, seen = [], set()

    def add(quote: str, start: int, end: int, name_after: str = "") -> None:
        q = " ".join(quote.split()).strip(" “”\"")
        if len(q.split()) < MIN_WORDS or q.lower() in seen:
            return
        seen.add(q.lower())
        before = text[max(0, start - 200):start]
        after = name_after or text[end:end + 80]
        found.append({"quote": q, "pos": start, "credited": credited_name(before, after),
                      "hedged": any(h in before.lower()[-120:] for h in HEDGES)})

    for m in BLOCKQUOTE.finditer(text):
        lines = [ln.lstrip(">").strip() for ln in m.group(1).splitlines()]
        name = ""
        if lines and DASH_NAME.match(lines[-1]):
            name, lines = lines[-1], lines[:-1]
        add(" ".join(lines), m.start(), m.end(), name or text[m.end():m.end() + 80])
    for m in QUOTED.finditer(text):
        if not any(abs(m.start() - f["pos"]) < 5 for f in found):
            add(m.group(1), m.start(), m.end())
    return sorted(found, key=lambda f: f["pos"])


# --------------------------------------------------------------------------- checking
def field(answer: str, name: str) -> str:
    for line in answer.splitlines():
        if line.startswith(name + ": "):
            return line[len(name) + 2:]
    return ""


def surname_in(name: Optional[str], *texts: str) -> bool:
    if not name:
        return False
    words = [w.strip(".'’").lower() for w in name.split() if len(w.strip(".'’")) > 2]
    hay = " ".join(texts).lower()
    return bool(words) and words[-1] in hay


def assess(q: Dict[str, object], answer: str) -> Dict[str, object]:
    r = dict(q)
    r.update(status=field(answer, "Status") or "No record", verdict=field(answer, "Verdict"),
             credit=field(answer, "Credit it as"), source=field(answer, "Traced to"),
             record=field(answer, "Record"), match=field(answer, "Match") or "none")
    who, status, credit = r["credited"], r["status"], r["credit"]
    real = credit.replace("Often attributed to ", "")
    name, _, work = real.partition(", ")  # "President Franklin D. Roosevelt, First Inaugural Address (1933)"
    if r["match"] == "none" or status not in OK_STATUSES + ("Disputed", "Re-credited"):
        r["label"] = "UNVERIFIED"
        r["fix"] = "No checked record. Keep the quote only if you can cite where it first appeared."
        if r["verdict"]:
            r["fix"] = r["verdict"] + " " + r["fix"]
    elif not r["match"].startswith("exact"):
        r["label"] = "CHECK"
        r["fix"] = "Only part of the wording matches. If it is the same line, follow the record above."
    elif status == "Re-credited":
        ok = who is None or surname_in(who, real)
        r["label"] = "OK" if ok else "FIX"
        r["fix"] = "" if ok else f"Credit {real} instead of {who}."
        if who is None:
            r["note"] = f"Your draft names no one. If you add a name, credit {real}; it is often wrongly credited elsewhere."
    elif status == "Disputed":
        ok = bool(r["hedged"]) or not who
        r["label"] = "OK" if ok else "FIX"
        r["fix"] = "" if ok else f"No reliable source shows {who} said it. Write “often attributed to {real}”, or cut it."
        if ok and r["hedged"]:
            r["note"] = "Fine as written: you already present it as an attribution, which matches the record."
    else:
        ok = who is None or surname_in(who, real, r["source"])
        r["label"] = "OK" if ok else "FIX"
        if who is None:
            r["note"] = f"Your draft names no one. If you add a name, credit {name}."
        r["fix"] = "" if ok else f"Credit {name} instead of {who}." + (f" Source: {work}." if work else "")
    return r


def check_draft(text: str, pause: float = 0.3) -> List[Dict[str, object]]:
    tool = QuoteAttributionCheck()
    results = []
    for q in find_quotes(text):
        results.append(assess(q, tool.invoke({"quote": q["quote"]})))
        time.sleep(pause)  # stay well inside the API's 40 requests per 10 seconds
    return results


# --------------------------------------------------------------------------- reporting
COLOURS = {"FIX": "31", "CHECK": "33", "UNVERIFIED": "33", "OK": "32"}


def report(results: List[Dict[str, object]], colour: bool = False) -> str:
    if not results:
        return "No quotes of five words or more found."
    paint = (lambda s, c: f"\033[{c}m{s}\033[0m") if colour else (lambda s, c: s)
    counts = {k: sum(r["label"] == k for r in results) for k in ORDER}
    words = {"FIX": "to fix", "CHECK": "to check", "UNVERIFIED": "unverified", "OK": "OK"}
    lines = [" · ".join(f"{n} {words[k]}" for k, n in counts.items() if n), ""]
    for r in sorted(results, key=lambda r: (ORDER[r["label"]], r["pos"])):
        lines.append(f"{paint(r['label'], COLOURS[r['label']]):<10} “{r['quote']}”")
        if r["credited"]:
            lines.append(f"           Your draft credits: {r['credited']}" + (" (hedged)" if r["hedged"] else ""))
        if r["verdict"] and r["label"] != "UNVERIFIED":
            lines.append(f"           Record: {r['status']}. {r['verdict']}")
        if r["fix"]:
            lines.append(f"           Fix: {r['fix']}")
        if r.get("note"):
            lines.append(f"           Note: {r['note']}")
        if r["record"]:
            lines.append(f"           Evidence: {r['record']}")
        lines.append("")
    lines.append("Source: Gracious Quotes (graciousquotes.com).")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Check every quote in a draft against Gracious Quotes' records.")
    ap.add_argument("source", help="a file, a URL, or - for standard input")
    ap.add_argument("--json", action="store_true", help="print the results as JSON")
    ap.add_argument("--strict", action="store_true", help="also fail (exit 1) on CHECK and UNVERIFIED")
    a = ap.parse_args(argv)
    results = check_draft(load(a.source))
    if a.json:
        print(json.dumps([{k: v for k, v in r.items() if k != "pos"} for r in results], ensure_ascii=False, indent=2))
    else:
        print(report(results, colour=sys.stdout.isatty() and "NO_COLOR" not in os.environ))
    failing = {"FIX", "CHECK", "UNVERIFIED"} if a.strict else {"FIX"}
    return 1 if any(r["label"] in failing for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
