"""
A view whose request and context types are imported for the type checker
only, as a module under from __future__ import annotations often does.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from hue import html

from hue_fastapi import HueFragmentsView, Router

if TYPE_CHECKING:
    from hue.context import HueContext
    from starlette.requests import Request


class TypingOnly(HueFragmentsView):
    router = Router()

    @router.fragment_get("items/{item}/")
    async def item(self, request: Request, context: HueContext, item: int):
        return html.div(f"item {item + 1}")
