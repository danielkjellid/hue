from collections.abc import Callable

from htmy import Context
from hue.context import HueContext
from hue.pages import BasePage
from hue.types.core import Component

from hue_fastapi.assets import CSS_URL, JS_URL, versioned_url
from hue_fastapi.config import HueConfig, get_config


class Page(BasePage):
    """
    The FastAPI page shell, wired to the asset routes configure_hue adds.

    Asset URLs and the title format are read when the page renders rather than
    bound when the class is defined, because the application they belong to is
    only known from the request.
    """

    _config: HueConfig
    _debug: bool

    @property
    def css_url(self) -> str:  # type: ignore[override]
        return self._config.css_url or versioned_url(CSS_URL, self._debug)

    @property
    def js_url(self) -> str:  # type: ignore[override]
        return self._config.js_url or versioned_url(JS_URL, self._debug)

    @property
    def extra_css_urls(self) -> list[str]:  # type: ignore[override]
        return list(self._config.extra_css_urls)

    def html_title_factory(self) -> Callable[[str], str]:
        return self._config.html_title_factory

    def htmy(self, context: Context) -> Component:
        app = HueContext.from_context(context).request.app
        self._config = get_config(app)
        self._debug = app.debug
        return super().htmy(context)
