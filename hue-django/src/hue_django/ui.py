"""
hue's UI components plus the Django-specific ones, under one import.

Everything hue.ui exports is re-exported here so apps do not have to import
from a transitive dependency, and the list cannot drift from hue.ui.
"""

from dataclasses import dataclass

from htmy import Context, html
from hue import ui as _ui
from hue.context import HueContext
from hue.ui import *  # noqa: F403


@dataclass(frozen=True, slots=True)
class CsrfTokenInput:
    """
    A hidden input carrying the CSRF token, the equivalent of the csrf_token
    template tag. Needed in forms that post without AJAX; AJAX requests send
    the token as a header instead.
    """

    def htmy(self, context: Context) -> html.input_:
        ctx = HueContext.from_context(context)
        return html.input_(
            type="hidden",
            name="csrfmiddlewaretoken",
            value=ctx.csrf_token,
        )


__all__ = [*_ui.__all__, "CsrfTokenInput"]  # noqa: PLE0604
