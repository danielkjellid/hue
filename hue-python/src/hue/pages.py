import json
from collections.abc import Callable
from functools import cached_property
from typing import Any, ClassVar

from htmy import Context, SafeStr, html

from hue import html as hue_html
from hue.context import HueContext
from hue.types.core import Component, ComponentType


class BasePage:
    """
    The HTML document shell around a page body: head, stylesheet and script
    links, the blocking theme script, and the Alpine bootstrap that carries the
    CSRF token.

    Do not subclass directly; create_page_base binds the asset URLs and returns a
    ready-to-use Page class.
    """

    #: Where the visitor's light/dark/system choice is remembered. Give it an
    #: app-specific value when one origin serves several apps that theme apart.
    theme_storage_key: ClassVar[str] = "hue-theme"

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
        return {}

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

    def theme_script(self) -> html.script:
        """
        Resolve and apply the colour theme before the first paint.

        This has to be a blocking script in the head: doing it on
        DOMContentLoaded gives every dark-mode visitor a white flash on every
        navigation. It reads the choice, resolves "system" against the OS, and
        writes only the resolved light/dark onto <html>, which is what the CSS
        matches. The store in theme.js takes over once Alpine boots.
        """
        key = json.dumps(self.theme_storage_key)
        dark_query = "'(prefers-color-scheme: dark)'"
        script_content = f"""
        (function () {{
          var choice = 'system';
          try {{
            choice = localStorage.getItem({key}) || 'system';
          }} catch (e) {{
            // Only the *remembered* choice depends on storage. Keep the OS
            // check outside the catch so a visitor with site data blocked
            // still lands on their system theme rather than on light.
          }}
          var dark = window.matchMedia({dark_query}).matches;
          var resolved = choice === 'system' ? (dark ? 'dark' : 'light') : choice;
          document.documentElement.setAttribute('data-theme', resolved);
        }})();
        """
        return html.script(SafeStr(script_content))

    def configure_alpine(self, context: HueContext) -> html.script:
        # Server-side values are emitted as JSON literals so any character in
        # them stays a valid JS string, and the script body is marked safe so
        # htmy does not HTML-escape the JavaScript.
        options = json.dumps(
            {
                "csrfToken": context.csrf_token,
                "themeStorageKey": self.theme_storage_key,
            }
        )
        script_content = f"""
        import {{ configureAlpine }} from '{self.js_url}';

        document.addEventListener('DOMContentLoaded', function() {{
          configureAlpine({options});
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
                    self.theme_script(),
                    html.script(src=self.js_url, type="module"),
                    html.link(rel="stylesheet", href=self.css_url, type="text/css"),
                    *extra_css_links,
                ),
                hue_html.body()
                .class_("min-h-screen bg-canvas relative")
                .x_data(self.inject_x_data())
                .content(self.body, self.configure_alpine(ctx)),
            ),
        )


def create_page_base(
    *,
    css_url: str,
    js_url: str,
    html_title_factory: Callable[[str], str],
    extra_css_urls: list[str] | None = None,
    theme_storage_key: str = BasePage.theme_storage_key,
) -> type[BasePage]:
    """
    Bind the asset URLs and title formatter for an app and return its Page class.
    """
    html_title_factory_func = html_title_factory
    _extra_css_urls = extra_css_urls or []
    _theme_storage_key = theme_storage_key

    class Page(BasePage):
        theme_storage_key = _theme_storage_key

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
