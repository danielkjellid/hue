"""
Render hue components to HTML in a static (request-less) build.

render_tree expects a request and CSRF token because hue is built for live,
AJAX-first apps. A static docs build has neither, so a stub request and a
placeholder token are passed. Components only stash these on the context and
the showcased components never read the request, so this is safe.
"""

from __future__ import annotations

import asyncio

from htmy import SafeStr
from hue import html
from hue.context import HueContextArgs
from hue.renderer import render_tree
from hue.types.core import ComponentType

# Static pages have no real CSRF protection; the token only flows into Alpine's
# config and never guards a real request here.
PLACEHOLDER_CSRF = "static-docs"


class _StubRequest:
    """
    Minimal stand-in for a framework request object.
    """


async def render_html(*components: ComponentType) -> str:
    return await render_tree(
        *components,
        context_args=HueContextArgs(
            request=_StubRequest(),
            csrf_token=PLACEHOLDER_CSRF,
        ),
    )


def render_html_sync(*components: ComponentType) -> str:
    return asyncio.run(render_html(*components))


def preview(component: ComponentType) -> ComponentType:
    """
    A component pre-rendered for embedding in a page, or an inline error so one
    bad example cannot fail the whole build.
    """
    try:
        return SafeStr(render_html_sync(component))
    except Exception as exc:
        return html.p(f"Could not render: {exc}").class_("text-sm text-destructive")
