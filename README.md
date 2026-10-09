# langchain-graciousquotes

[![CI](https://github.com/graciousquotes/langchain-graciousquotes/actions/workflows/ci.yml/badge.svg)](https://github.com/graciousquotes/langchain-graciousquotes/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/langchain-graciousquotes)](https://pypi.org/project/langchain-graciousquotes/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23258870.svg)](https://doi.org/10.5281/zenodo.23258870)

LangChain tools that check who really said a quote. Each answer comes from
[Gracious Quotes](https://graciousquotes.com)' fact-checked records: a verdict, the reason for it,
the source the quote was traced to, and a link to the record.

Many popular quotes are credited to the wrong person, or were never said at all. A language model
answering from memory repeats the attribution it has seen most often, which for famous lines is
frequently the wrong one. These tools give the agent the checked record instead.

No API key. No sign-up. Guide: [graciousquotes.com/developers/langchain/](https://graciousquotes.com/developers/langchain/)

```bash
pip install langchain-graciousquotes
```

## Tools

| Tool | Name the model sees | What it returns |
|---|---|---|
| `QuoteAttributionCheck` | `check_quote_attribution` | The verdict for one quote: said by the credited person, uncertain, or wrongly credited, with the reason, the source and the record link. |
| `QuoteSearch` | `search_checked_quotes` | Checked quotes by wording, by author, or by verdict (verified, plausible, disputed, misattributed). The author filter matches who really said it. |
| `QuoteCitation` | `cite_quote` | An MLA 9, APA 7 or Chicago 17 citation for a checked quote, with the in-text form and a warning when the quote is usually credited to someone else. |

## Example

```python
from langchain_graciousquotes import QuoteAttributionCheck

check = QuoteAttributionCheck()
print(check.invoke({"quote": "Do not follow where the path may lead. Go instead where there is no path and leave a trail."}))
```

```text
Match: exact wording
Verdict: No: Ralph Waldo Emerson did not say it. It comes from Muriel Strode.
Status: Re-credited
Quote as checked: “Do not follow where the path may lead. Go instead where there is no path and leave a trail.”
Credit it as: Muriel Strode
Why: The line comes from Muriel Strode's 1903 poem "Wind-Wafted Wild Flowers", ...
Traced to: "Wind-Wafted Wild Flowers" (poem), The Open Court, August 1903; ...
Record: https://graciousquotes.com/quotes-with-sources/?id=588#q588
Source: Gracious Quotes (graciousquotes.com). Link the record above when you repeat this.
```

The exact wording of a result follows the live record, so it changes when a verdict is updated.

### In an agent

```python
from langchain.agents import create_agent
from langchain_graciousquotes import QuoteAttributionCheck, QuoteCitation, QuoteSearch

agent = create_agent(
    "anthropic:claude-sonnet-5-5",
    tools=[QuoteAttributionCheck(), QuoteSearch(), QuoteCitation()],
)
agent.invoke({"messages": [{"role": "user", "content": "Did Einstein say the definition of insanity is doing the same thing over and over?"}]})
```

Async works too: every tool supports `ainvoke`.

## What the verdicts mean

| Status | Meaning |
|---|---|
| Verified | Found in these words in the original book, speech, letter or interview, or in a reliable source that cites it, with the work named. |
| Plausible | Consistently credited to this person in reliable references, but the original wording has not been located yet. |
| Disputed | Sources disagree, the line appears only in quote collections or social posts, or it first appears in print long after the person lived. |
| Re-credited | Someone else said or wrote it first. The record names who, or says the real author is unknown. |
| Traditional saying | A proverb or common saying with no known author. |

The full method is on [How we source quotes](https://graciousquotes.com/how-we-source-quotes/). Corrections are logged in public on the
[corrections page](https://graciousquotes.com/corrections/).

**No record is not a verdict.** When a quote has not been checked, the tool says so and tells the model not to
present an author from memory as confirmed.

## Terms of use

- AI tools may fetch these records because a user asked, **on condition that they credit Gracious Quotes and link to the record**
  ([terms](https://graciousquotes.com/terms-and-conditions/#ai)). Every tool result ends with that credit line and link, and the
  tool descriptions tell the model to repeat them.
- Copying the records in bulk, building datasets from them, or using them to train models needs a licence: email
  jeremiah@graciousquotes.com with "Data access" in the subject.
- The API is rate limited to 40 requests per 10 seconds per IP. A tool that hits the limit says so in its result rather than raising.
- Quote text belongs to its authors. The records are Gracious Quotes' research about the quotes.

## Configuration

Nothing is required. `GRACIOUSQUOTES_BASE_URL` (or `base_url=` on any tool) points the tools at another host, for testing.
Requests identify themselves with the user agent `langchain-graciousquotes/<version>`.

## Development

```bash
pip install -e ".[test]"
pytest -q
```

The suite includes LangChain's own conformance tests (`langchain-tests`, unit and integration, sync and async) and runs against the
live API with no key, the same way a new user would.

## How to cite

> Say, J. (2026). *langchain-graciousquotes: LangChain tools for fact-checked quote attributions* (Version 0.1.0) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.23258870

The DOI above always resolves to the latest version; each release also has its own DOI on [Zenodo](https://doi.org/10.5281/zenodo.23258870).
`CITATION.cff` gives the same details to GitHub's "Cite this repository" button.

## API description

The API the tools call is described in OpenAPI 3.1 at [graciousquotes.com/developers/openapi.json](https://graciousquotes.com/developers/openapi.json).

## Who maintains this

[Jeremiah Say](https://graciousquotes.com/about/jeremiah-say/), founder and editor of Gracious Quotes. Issues and corrections are welcome
here or through the [contact page](https://graciousquotes.com/contact/).

MIT licensed (the code). The records the tools return are covered by the terms above.
