"""What the conformance suite does not check: that the answer handed to a model is right and carries its credit.

These call the live API with well-documented cases whose verdicts are settled in
the published record. If one of them changes, a verdict on the site changed, and
a person should look at why before the test is updated.
"""
from langchain_graciousquotes import QuoteAttributionCheck, QuoteCitation, QuoteSearch

STRODE = "Do not follow where the path may lead. Go instead where there is no path and leave a trail."


def test_recredited_quote_names_the_real_author():
    """The reason this package exists: the popular attribution (Emerson) is wrong."""
    out = QuoteAttributionCheck().invoke({"quote": STRODE})
    assert "Muriel Strode" in out
    assert "Re-credited" in out
    assert "Record: https://graciousquotes.com/" in out


def test_every_answer_carries_the_credit_and_a_link():
    """The terms allow AI tools to fetch records on condition they credit and link."""
    for out in (
        QuoteAttributionCheck().invoke({"quote": STRODE}),
        QuoteSearch().invoke({"author": "Muriel Strode"}),
        QuoteCitation().invoke({"quote_id": 588}),
    ):
        assert "Source: Gracious Quotes (graciousquotes.com)" in out
        assert "https://graciousquotes.com/" in out


def test_disputed_quote_is_not_reported_as_confirmed():
    out = QuoteAttributionCheck().invoke({"quote": "Be the change you wish to see in the world"})
    assert "Gandhi" in out
    assert "Uncertain" in out or "Disputed" in out
    assert "Yes:" not in out


def test_verified_quote_returns_its_source():
    out = QuoteAttributionCheck().invoke({"quote": "To be, or not to be, that is the question"})
    assert "Shakespeare" in out
    assert "Hamlet" in out


def test_no_record_tells_the_model_not_to_guess():
    """A miss must never read as 'nobody said it' or invite a guess from memory."""
    out = QuoteAttributionCheck().invoke({"quote": "xqzzv flobbering the marmalade quietly tonight"})
    assert "unverified" in out
    assert "Traceback" not in out


def test_too_short_asks_for_the_full_quote():
    out = QuoteAttributionCheck().invoke({"quote": "hi"})
    assert "full wording" in out


def test_search_needs_a_query_or_an_author():
    out = QuoteSearch().invoke({})
    assert "query" in out and "author" in out


def test_search_returns_ids_the_cite_tool_accepts():
    out = QuoteSearch().invoke({"author": "Muriel Strode"})
    assert "id: 588" in out
    assert "cite_quote" in out


def test_citation_warns_about_the_popular_misattribution():
    out = QuoteCitation().invoke({"quote_id": 588, "style": "apa"})
    assert "Warning:" in out and "Emerson" in out
    assert "APA 7" in out


def test_unknown_id_explains_what_to_do():
    out = QuoteCitation().invoke({"quote_id": 999999999})
    assert "search_checked_quotes" in out
    assert "Traceback" not in out


async def test_async_path_matches_sync():
    sync = QuoteAttributionCheck().invoke({"quote": STRODE})
    asynchronous = await QuoteAttributionCheck().ainvoke({"quote": STRODE})
    assert asynchronous == sync


def test_author_filter_lists_the_real_authors_quotes():
    out = QuoteSearch().invoke({"author": "William Shakespeare", "status": "verified", "limit": 2})
    assert "[Verified]" in out
    assert "Shakespeare" in out
