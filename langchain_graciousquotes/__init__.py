"""Check who really said a quote, as LangChain tools.

Many popular quotes are credited to the wrong person, or were never said at all,
and a language model repeats the most common attribution, not the true one.
These tools answer from Gracious Quotes' fact-checked records instead: a verdict,
the reason for it, the source the quote was traced to, and a link to the record.
"""

from langchain_graciousquotes.tools import (
    QuoteAttributionCheck,
    QuoteCitation,
    QuoteSearch,
)

__version__ = "0.1.0"

__all__ = [
    "QuoteAttributionCheck",
    "QuoteCitation",
    "QuoteSearch",
    "__version__",
]
