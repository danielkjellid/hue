from functools import cached_property
import json
from typing import Callable
from htmy import Context
from typing_extensions import Any
from hue.types.core import Component, ComponentType
from hue.context import HueContext
from hue.formatter import HueFormatter
from htmy import html


class BasePage:
    def __init__(
        self,
        *,
        body: Component,
        x_data: dict[str, Any] | None = None,
        title: str | None = None,
    ):
        self.body = body
        self.x_data = x_data or {}
        self.title = title

    @cached_property
    def base_x_data(self) -> dict[str, Any]:
        return {"theme": "light"}

    @cached_property
    def css_url(self) -> str:
        raise NotImplementedError(
            "css_url must be implemented by constructing the class through create_base_page()"
        )

    @cached_property
    def html_title_factory(self) -> Callable[[str], str]:
        raise NotImplementedError(
            "html_title_factory must be implemented by constructing the class through create_base_page()"
        )

    def configure_alpine(self, context: HueContext) -> html.script:
        # Use separate conditions to avoid && being escaped
        script_content = f"""
        document.addEventListener('DOMContentLoaded', function() {{
            if (typeof Alpine !== 'undefined') {{
                if (typeof ajax !== 'undefined') {{
                    Alpine.plugin(ajax.configure({{
                        headers: {{"X-CSRF-Token": "{context.csrf_token}" }}
                    }}));
                    Alpine.start();
                }}
            }}
        }});
        """
        return html.script(script_content)

    def inject_x_data(self) -> str:
        """Convert x_data dictionary to Alpine.js x-data format.
        Example: '{ theme: "light", open: false }'
        """
        combined_data = {**self.base_x_data, **self.x_data}
        return json.dumps(combined_data)

    def htmy(self, context: Context) -> Component:
        # Extract HueContext from the context provided by the renderer
        # This context is populated by HueContext.htmy_context()
        ctx = HueContext.from_context(context)

        return HueFormatter().in_context(
            html.DOCTYPE.html,
            html.html(
                html.head(
                    html.title(self.html_title_factory(self.title)),
                    html.meta.charset(),
                    html.meta.viewport(),
                    html.script(
                        src="https://cdn.jsdelivr.net/npm/@imacrayon/alpine-ajax@0.12.6/dist/cdn.min.js",
                        defer=True,
                    ),
                    html.script(
                        src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js",
                        defer=True,
                    ),
                    html.link(
                        rel="stylesheet",
                        href=self.css_url,
                        type="text/css",
                    ),
                ),
                html.body(
                    self.body,
                    x_data=self.inject_x_data(),
                    x_bind_data_theme="theme",
                    class_="min-h-screen bg-background relative",
                ),
                self.configure_alpine(ctx),
            ),
        )


def create_page_base(
    css_url: str, html_title_factory: Callable[[str], str]
) -> type[BasePage]:
    class Page(BasePage):
        @cached_property
        def css_url(self) -> str:
            return css_url

        @cached_property
        def html_title_factory(self) -> Callable[[str], str]:
            return html_title_factory

    return Page
