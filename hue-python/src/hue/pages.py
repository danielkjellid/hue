import json
from collections.abc import Callable
from functools import cached_property
from typing import Any

from htmy import Context, SafeStr, html

from hue import html as hue_html
from hue.context import HueContext
from hue.types.core import Component, ComponentType


class BasePage:
    """
    The HTML document shell around a page body: head, stylesheet and script
    links, and the Alpine bootstrap that carries the CSRF token.

    Do not subclass directly; create_page_base binds the asset URLs and returns a
    ready-to-use Page class.
    """

    def __init__(
        self,
        *,
        title: str,
        body: ComponentType,
        x_data: dict[str, Any] | None = None,
    ):
        self.body = body
        self.x_data = x_data or {}
        self.title = title

    @cached_property
    def base_x_data(self) -> dict[str, Any]:
        return {"theme": "light"}

    @cached_property
    def extra_css_urls(self) -> list[str]:
        return []

    @cached_property
    def css_url(self) -> str:
        raise NotImplementedError(
            "css_url must be implemented by constructing the class through "
            "create_page_base()"
        )

    @cached_property
    def js_url(self) -> str:
        raise NotImplementedError(
            "js_url must be implemented by constructing the class through "
            "create_page_base()"
        )

    def html_title_factory(self) -> Callable[[str], str]:
        raise NotImplementedError(
            "html_title_factory must be implemented by constructing the class through "
            "create_page_base()"
        )

    def configure_alpine(self, context: HueContext) -> html.script:
        # The token is emitted as a JSON string literal so any character in it
        # stays a valid JS string, and the script body is marked safe so htmy
        # does not HTML-escape the JavaScript.
        script_content = f"""
        import {{ configureAlpine }} from '{self.js_url}';

        document.addEventListener('DOMContentLoaded', function() {{
          configureAlpine({json.dumps(context.csrf_token)});
        }});
        """
        return html.script(SafeStr(script_content), type="module")

    def inject_x_data(self) -> str:
        """
        The page-level Alpine scope as a JSON object literal.
        """
        return json.dumps({**self.base_x_data, **self.x_data})

    def htmy(self, context: Context) -> Component:
        ctx = HueContext.from_context(context)

        extra_css_links = [
            html.link(rel="stylesheet", href=url, type="text/css")
            for url in self.extra_css_urls
        ]

        return (
            html.DOCTYPE.html,
            html.html(
                html.head(
                    html.title(self.html_title_factory()(self.title)),
                    html.meta.charset(),
                    html.meta.viewport(),
                    html.script(src=self.js_url, type="module"),
                    html.link(rel="stylesheet", href=self.css_url, type="text/css"),
                    *extra_css_links,
                ),
                hue_html.body()
                .class_("min-h-screen bg-background relative")
                .x_data(self.inject_x_data())
                .x_bind("data-theme", "theme")
                .content(self.body, self.configure_alpine(ctx)),
            ),
        )


def create_page_base(
    *,
    css_url: str,
    js_url: str,
    html_title_factory: Callable[[str], str],
    extra_css_urls: list[str] | None = None,
) -> type[BasePage]:
    """
    Bind the asset URLs and title formatter for an app and return its Page class.
    """
    html_title_factory_func = html_title_factory
    _extra_css_urls = extra_css_urls or []

    class Page(BasePage):
        @cached_property
        def css_url(self) -> str:
            return css_url

        @cached_property
        def js_url(self) -> str:
            return js_url

        @cached_property
        def extra_css_urls(self) -> list[str]:
            return _extra_css_urls

        def html_title_factory(self) -> Callable[[str], str]:
            return html_title_factory_func

    return Page
