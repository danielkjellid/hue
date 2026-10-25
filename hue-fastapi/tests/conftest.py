from collections.abc import Callable

import httpx
import pytest
from fastapi import FastAPI

from hue_fastapi import assets as assets_module
from hue_fastapi.config import configure_hue
from hue_fastapi.csrf import CsrfConfig

AJAX_HEADERS = {"X-Requested-With": "XMLHttpRequest"}
ALPINE_AJAX_HEADERS = {"X-Alpine-Request": "true"}

STUB_CSS = "/* stub stylesheet */"
STUB_JS = "// stub bundle"


@pytest.fixture(autouse=True)
def stub_assets(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Serve fixed asset bodies, so tests do not need hue's CSS to be built.
    """
    monkeypatch.setattr(
        assets_module,
        "_ASSET_ROUTES",
        {
            assets_module.CSS_URL: (lambda: STUB_CSS, "text/css; charset=utf-8"),
            assets_module.JS_URL: (
                lambda: STUB_JS,
                "text/javascript; charset=utf-8",
            ),
            assets_module.CHART_JS_URL: (
                lambda: STUB_JS,
                "text/javascript; charset=utf-8",
            ),
        },
    )
    monkeypatch.setattr(assets_module, "_cache", {})


def make_app(
    *views: tuple[str, type],
    csrf: CsrfConfig | None = None,
    **config: object,
) -> FastAPI:
    """
    A throwaway app with hue configured and the given views mounted.
    """
    app = FastAPI()
    configure_hue(app, csrf=csrf, **config)  # type: ignore[arg-type]
    for prefix, view in views:
        app.include_router(view.api_router, prefix=prefix)  # type: ignore[attr-defined]
    return app


@pytest.fixture
def client_for() -> Callable[..., httpx.AsyncClient]:
    def _client(app: FastAPI, **kwargs: object) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
            **kwargs,  # type: ignore[arg-type]
        )

    return _client
