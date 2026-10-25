"""
Rendering inside a request, the way a live FastAPI page renders.
"""

from __future__ import annotations

from htmy import SafeStr
from hue import html
from hue.context import HueContextArgs
from hue.renderer import render_tree
from hue.shortcuts import ShortcutRegistry
from hue.types.core import ComponentType

from hue_docs_v2.model import Example


async def render_html(
    *components: ComponentType,
    request: object,
    shortcuts: type[ShortcutRegistry] | None = None,
) -> str:
    # No CSRF token: the pages are frozen to static files, and the demo routes
    # they post to change nothing, so the Worker runs without CSRF.
    return await render_tree(
        *components,
        context_args=HueContextArgs(
            request=request, csrf_token="", shortcuts=shortcuts
        ),
    )


async def preview(example: Example, request: object) -> ComponentType:
    """
    One example rendered on its own, or a note saying why not, so one broken
    example costs its own cell rather than the whole page.
    """
    try:
        return SafeStr(await render_html(example(), request=request))
    except Exception as exc:
        return html.p(f"Could not render: {exc}").class_("text-sm text-danger-text")
