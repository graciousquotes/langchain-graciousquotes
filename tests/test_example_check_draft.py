"""examples/check_draft.py is documented on the guide, so it is tested like the package.

Most tests are offline (finding quotes, reading the credited name, labelling). The last one runs the
sample draft against the live API, which keeps a published example from silently breaking.
"""
import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("check_draft", ROOT / "examples" / "check_draft.py")
cd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cd)


def answer(status, verdict="", credit="", source="", match="exact wording"):
    return "\n".join([f"Match: {match}", f"Verdict: {verdict}", f"Status: {status}", f"Credit it as: {credit}",
                      f"Traced to: {source}", "Record: https://graciousquotes.com/x"])


def quote(credited=None, hedged=False):
    return {"quote": "a quote of more than five words", "pos": 0, "credited": credited, "hedged": hedged}


def test_finds_curly_straight_and_blockquotes_with_their_names():
    text = ('Emerson told us: “Do not follow where the path may lead.”\n\n'
            '> Every new beginning comes from some other beginning’s end.\n> — Seneca\n\n'
            'He said "too short here".')
    found = cd.find_quotes(text)
    assert [(f["quote"][:12], f["credited"]) for f in found] == [("Do not follo", "Emerson"), ("Every new be", "Seneca")]


def test_reads_hedges():
    f = cd.find_quotes('Einstein supposedly said that "insanity is doing the same thing over and over."')[0]
    assert f["credited"] == "Einstein" and f["hedged"] is True


def test_wrong_name_on_a_verified_quote_is_flagged():
    r = cd.assess(quote("Mark Twain"), answer("Verified", credit="President Franklin D. Roosevelt, First Inaugural Address (1933)"))
    assert r["label"] == "FIX" and r["fix"].startswith("Credit President Franklin D. Roosevelt instead of Mark Twain.")


def test_right_name_or_the_work_passes():
    assert cd.assess(quote("Roosevelt"), answer("Verified", credit="President Franklin D. Roosevelt"))["label"] == "OK"
    assert cd.assess(quote("Hamlet"), answer("Verified", credit="William Shakespeare", source="Hamlet (c. 1600)"))["label"] == "OK"


def test_recredited_and_disputed():
    assert cd.assess(quote("Emerson"), answer("Re-credited", credit="Muriel Strode"))["label"] == "FIX"
    assert cd.assess(quote("Muriel Strode"), answer("Re-credited", credit="Muriel Strode"))["label"] == "OK"
    assert cd.assess(quote(None), answer("Re-credited", credit="Muriel Strode"))["label"] == "OK"
    plain = cd.assess(quote("Peter Drucker"), answer("Disputed", credit="Often attributed to Peter Drucker"))
    hedged = cd.assess(quote("Peter Drucker", hedged=True), answer("Disputed", credit="Often attributed to Peter Drucker"))
    assert plain["label"] == "FIX" and "often attributed to Peter Drucker" in plain["fix"]
    assert hedged["label"] == "OK"


def test_partial_and_missing_records_are_never_firm_verdicts():
    assert cd.assess(quote("Emerson"), answer("Re-credited", credit="Muriel Strode", match="weak match"))["label"] == "CHECK"
    assert cd.assess(quote("Someone"), "Gracious Quotes has no checked record matching this wording.")["label"] == "UNVERIFIED"
    assert cd.assess(quote("Confucius"), answer("unreviewed", verdict="We have it credited to Confucius, but we have not checked it yet."))["label"] == "UNVERIFIED"


def test_report_puts_problems_first_and_exit_code_follows_strict(monkeypatch):
    rows = [dict(quote(), label=l, status="", verdict="", fix="", record="", credited=None, hedged=False, pos=i)
            for i, l in enumerate(["OK", "UNVERIFIED", "FIX"])]
    out = cd.report(rows)
    assert out.splitlines()[0] == "1 to fix · 1 unverified · 1 OK"
    assert out.splitlines()[2].startswith("FIX")
    monkeypatch.setattr(cd, "check_draft", lambda text: rows[:2])
    monkeypatch.setattr(cd, "load", lambda src: "")
    assert cd.main(["x.md"]) == 0 and cd.main(["x.md", "--strict"]) == 1


def test_sample_draft_against_the_live_api():
    results = cd.check_draft((ROOT / "examples" / "sample_draft.md").read_text(encoding="utf-8"))
    label = {r["quote"][:15]: r["label"] for r in results}
    assert label["Do not follow w"] == "FIX"      # Emerson -> Muriel Strode
    assert label["The only thing "] == "FIX"      # Mark Twain -> Franklin D. Roosevelt
    assert label["The best way to"] == "FIX"      # Drucker, disputed, not hedged
    assert label["insanity is doi"] == "OK"       # Einstein, disputed, hedged
    assert label["To be, or not t"] == "OK"       # Hamlet, verified
    assert label["The quiet hours"] == "UNVERIFIED"
