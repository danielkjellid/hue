import re
import pytest
from hue.router import Router, PathParseResult
from hue.context import HueContextArgs

class MockRequest:
    def __init__(self, headers: dict[str, str] | None = None):
        self.headers = headers or {}

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

@pytest.fixture
def router() -> MockRouter:
    return MockRouter()

@pytest.fixture
def mock_request() -> MockRequest:
    def _mock_request(headers: dict[str, str] | None = None) -> MockRequest:
        return MockRequest(headers=headers)
    return _mock_request
