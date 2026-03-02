import re
from typing import Any

import pytest

from hue.context import HueContextArgs
from hue.router import PathParseResult, Router


class MockRequest:
    def __init__(
        self,
        headers: dict[str, str] | None = None,
        body: str | None = None,
        content_type: str = "application/json",
        form_data: dict[str, Any] | None = None,
    ):
        self.headers = headers or {}
        self.body = body or ""
        self.content_type = content_type
        self.form_data = form_data or {}


class MockRouter(Router[MockRequest]):
    """Concrete router implementation for testing."""

    def _parse_path_params(self, path: str) -> PathParseResult:
        """Simple path parser that extracts {param} patterns."""

        # Find all {param} patterns
        param_pattern = r"\{(\w+)\}"
        matches = re.findall(param_pattern, path)
        param_names = list(matches)

        # Convert to simple path format (remove braces for testing)
        final_path = re.sub(r"\{(\w+)\}", r"<\1>", path)

        return PathParseResult(path=final_path, param_names=param_names)

    def _get_context_args(self, request: MockRequest) -> HueContextArgs[MockRequest]:
        """Return mock context args."""
        return HueContextArgs[MockRequest](
            request=request,
            csrf_token="test-csrf-token",
        )

    def _get_request_body(self, request: MockRequest) -> str:
        """Return the mock request body."""
        return request.body

    def _get_request_content_type(self, request: MockRequest) -> str:
        """Return the mock request content type."""
        return request.content_type

    def _get_form_data(self, request: MockRequest) -> dict[str, Any]:
        """Return the mock form data."""
        return request.form_data


@pytest.fixture
def router() -> MockRouter:
    return MockRouter()


@pytest.fixture
def mock_request() -> MockRequest:
    def _mock_request(
        headers: dict[str, str] | None = None,
        body: str | None = None,
        content_type: str = "application/json",
        form_data: dict[str, Any] | None = None,
    ) -> MockRequest:
        return MockRequest(
            headers=headers, body=body, content_type=content_type, form_data=form_data
        )

    return _mock_request
