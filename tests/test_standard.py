"""LangChain's own conformance suite, run against all three tools.

These are not our tests: they are `langchain-tests`, the suite LangChain
publishes so anyone can check an integration against langchain-core's
interfaces. Every tool runs both the unit and the integration suite.

The integration suite invokes the tools for real against the live, keyless
API, so this passes in CI with no secret configured.
"""
from typing import Type

from langchain_core.tools import BaseTool
from langchain_tests.integration_tests import ToolsIntegrationTests
from langchain_tests.unit_tests import ToolsUnitTests

from langchain_graciousquotes import QuoteAttributionCheck, QuoteCitation, QuoteSearch

STRODE_ID = 588  # "Do not follow where the path may lead..." re-credited from Emerson to Muriel Strode


class _Check:
    @property
    def tool_constructor(self) -> Type[BaseTool]:
        return QuoteAttributionCheck

    @property
    def tool_constructor_params(self) -> dict:
        return {}

    @property
    def tool_invoke_params_example(self) -> dict:
        return {"quote": "Be the change you wish to see in the world"}


class TestCheckUnit(_Check, ToolsUnitTests): ...
class TestCheckIntegration(_Check, ToolsIntegrationTests): ...


class _Search:
    @property
    def tool_constructor(self) -> Type[BaseTool]:
        return QuoteSearch

    @property
    def tool_constructor_params(self) -> dict:
        return {}

    @property
    def tool_invoke_params_example(self) -> dict:
        return {"author": "William Shakespeare", "status": "verified", "limit": 3}


class TestSearchUnit(_Search, ToolsUnitTests): ...
class TestSearchIntegration(_Search, ToolsIntegrationTests): ...


class _Cite:
    @property
    def tool_constructor(self) -> Type[BaseTool]:
        return QuoteCitation

    @property
    def tool_constructor_params(self) -> dict:
        return {}

    @property
    def tool_invoke_params_example(self) -> dict:
        return {"quote_id": STRODE_ID, "style": "mla"}


class TestCiteUnit(_Cite, ToolsUnitTests): ...
class TestCiteIntegration(_Cite, ToolsIntegrationTests): ...
