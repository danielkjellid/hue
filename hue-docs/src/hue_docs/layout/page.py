"""The overall docs page shell: top bar + sidebar + content."""

from __future__ import annotations

from hue import html
from hue.pages import BasePage, create_page_base
from hue.types.core import ComponentType

from hue_docs.layout.sidebar import sidebar
from hue_docs.models import NavGroup
from hue_docs.site import url

_Page = create_page_base(
    css_url=url("/styles/tailwind.css"),
    js_url=url("/js/alpine-bundle.js"),
    html_title_factory=lambda title: f"{title} · Hue",
    extra_css_urls=[url("/styles/highlight.css")],
)


def _theme_toggle() -> ComponentType:
    return (
        html.button()
        .class_(
            "rounded-md border border-surface-200 px-2.5 py-1.5 text-sm "
            "text-surface-600 transition-colors hover:text-surface-900"
        )
        .aria_label("Toggle colour theme")
        .x_on("click", "theme = theme === 'dark' ? 'light' : 'dark'")
        .x_text("theme === 'dark' ? 'Light' : 'Dark'")
    )


def _menu_button() -> ComponentType:
    return (
        html.button("Menu")
        .class_(
            "rounded-md border border-surface-200 px-2.5 py-1.5 text-sm "
            "text-surface-600 lg:hidden"
        )
        .aria_label("Toggle navigation")
        .x_on("click", "navOpen = !navOpen")
    )


def _topbar() -> ComponentType:
    return html.header(
        html.div(
            html.a("Hue").href(url("/")).class_("text-lg font-bold text-surface-900"),
            html.div(_theme_toggle(), _menu_button()).class_("flex items-center gap-2"),
        ).class_(
            "mx-auto flex h-14 w-full max-w-7xl items-center justify-between "
            "px-6 lg:pr-10 lg:pl-6.5"
        ),
    ).class_(
        "sticky top-0 z-20 border-b border-surface-200 bg-background/80 backdrop-blur"
    )


def build_page(
    *,
    title: str,
    nav: list[NavGroup],
    active_href: str,
    main: ComponentType,
) -> BasePage:
    body = (
        html.div()
        .class_("min-h-screen")
        .x_data("{ navOpen: false }")
        .content(
            _topbar(),
            html.div(
                sidebar(nav, active_href),
                html.main(main).class_("min-w-0 flex-1 px-6 py-10 lg:px-10"),
            ).class_("mx-auto flex w-full max-w-7xl"),
        )
    )
    return _Page(title=title, body=body)
