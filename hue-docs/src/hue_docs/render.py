"""Helpers for rendering hue components to HTML in a static (request-less) build.

``render_tree`` expects a request and CSRF token because hue is built for live,
AJAX-first apps. A static docs build has neither, so we pass a tiny stub request
and a placeholder token. Components and pages only stash these on the context —
the showcased components never read the request — so this is safe.
"""

from __future__ import annotations

import asyncio

from hue.context import HueContextArgs
from hue.renderer import render_tree
from hue.types.core import ComponentType

# Static pages have no real CSRF protection; the token only flows into Alpine's
# config and is never used to guard a real request here.
PLACEHOLDER_CSRF = "static-docs"


class _StubRequest:
    """Minimal stand-in for a framework request object."""


async def render_html(*components: ComponentType) -> str:
    """Render one or more components to an HTML string."""
    return await render_tree(
        *components,
        context_args=HueContextArgs(
            request=_StubRequest(),
            csrf_token=PLACEHOLDER_CSRF,
        ),
    )


def render_html_sync(*components: ComponentType) -> str:
    """Synchronous wrapper around :func:`render_html`."""
    return asyncio.run(render_html(*components))
