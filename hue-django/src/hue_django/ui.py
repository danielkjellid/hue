# Re-export all UI components from hue.ui to provide a unified API
# This prevents users from needing to import from transitive dependencies
from dataclasses import dataclass
from typing import Any

from htmy import Context, html
from hue.context import HueContext
from hue.ui import (
    Button,
    EmailInput,
    Icon,
    Label,
    NumberInput,
    PasswordInput,
    Stack,
    Text,
    TextInput,
    create_icon_base,
)


@dataclass(frozen=True, slots=True, kw_only=False)
class CsrfTokenInput:
    """
    A hidden input field that contains the CSRF token. This replecates
    the node created by the {% csrf_token %} template tag, and is required
    whenever having a form that has method="post".
    """

    def htmy(self, context: Context, **kwargs: Any) -> html.input_:
        ctx = HueContext.from_context(context)
        return html.input_(
            type="hidden",
            name="csrfmiddlewaretoken",
            value=ctx.csrf_token,
        )


__all__ = [
    "Button",
    "CsrfTokenInput",
    "EmailInput",
    "Icon",
    "Label",
    "NumberInput",
    "PasswordInput",
    "Stack",
    "Text",
    "TextInput",
    "create_icon_base",
]
