"""
hue's UI components plus the FastAPI-specific ones, under one import.
"""

from dataclasses import dataclass

from htmy import Context, html
from hue import ui as _ui
from hue.context import HueContext
from hue.ui import *  # noqa: F403

from hue_fastapi.csrf import CSRF_FORM_FIELD


@dataclass(frozen=True, slots=True)
class CsrfTokenInput:
    """
    A hidden input carrying the CSRF token.

    Needed in forms that post without AJAX; AJAX requests send the token as a
    header instead.
    """

    def htmy(self, context: Context) -> html.input_:
        ctx = HueContext.from_context(context)
        return html.input_(type="hidden", name=CSRF_FORM_FIELD, value=ctx.csrf_token)


__all__ = [*_ui.__all__, "CsrfTokenInput"]  # noqa: PLE0604
