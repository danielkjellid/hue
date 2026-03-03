from __future__ import annotations

from typing import Literal

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component
from hue.ui.atoms.input import Autocomplete, _get_base_input_classes
from hue.ui.atoms.stack import Stack
from hue.ui.atoms.text import Label, Text
from hue.ui.v2.base import _ALPINE_PREFIXES, ChainableComponent
from hue.utils import render_if


class _BaseInput(ChainableComponent):
    """
    Base class for chainable input components.

    Not intended to be used directly — use one of the concrete subclasses
    (``TextInput``, ``EmailInput``, ``NumberInput``, ``PasswordInput``).
    """

    _input_type: str = "text"

    def __init__(self) -> None:
        super().__init__()
        self._name: str | None = None

    # ------------------------------------------------------------------
    # Alpine — x-model (form control specific)
    # ------------------------------------------------------------------

    def x_model(self, value: str) -> Self:
        """Two-way bind this input to Alpine data."""
        self._props["x-model"] = value
        return self

    def name(self, value: str) -> Self:
        self._name = value
        return self

    def label(self, value: str) -> Self:
        self._props["label"] = value
        return self

    def placeholder(self, value: str) -> Self:
        self._props["placeholder"] = value
        return self

    def disabled(self, value: bool = True) -> Self:
        self._props["disabled"] = value
        return self

    def required(self, value: bool = True) -> Self:
        self._props["required"] = value
        return self

    def hidden_label(self, value: bool = True) -> Self:
        self._props["hidden_label"] = value
        return self

    def autocomplete(self, value: Autocomplete) -> Self:
        self._props["autocomplete"] = value
        return self

    def help_text(self, value: str) -> Self:
        self._props["help_text"] = value
        return self

    def error_text(self, value: str) -> Self:
        self._props["error_text"] = value
        return self

    def min_length(self, value: int) -> Self:
        self._props["min_length"] = value
        return self

    def max_length(self, value: int) -> Self:
        self._props["max_length"] = value
        return self

    # ------------------------------------------------------------------
    # Computed helpers
    # ------------------------------------------------------------------

    def _get_aria_invalid(self) -> bool:
        return self._get_prop("error_text") is not None

    def _get_aria_describedby(self) -> str | None:
        help_text = self._get_prop("help_text")
        error_text = self._get_prop("error_text")

        ids = [
            f"{self._name}-description" if help_text else None,
            f"{self._name}-error" if error_text else None,
        ]
        filtered = [v for v in ids if v is not None]
        return " ".join(filtered) if filtered else None

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _get_extra_input_attrs(self) -> dict:
        """Override in subclasses that need extra attrs (e.g. NumberInput)."""
        return {
            "min_length": self._get_prop("min_length"),
            "max_length": self._get_prop("max_length"),
        }

    def _get_alpine_attrs(self) -> dict:
        """Collect Alpine attributes (x_*, ajax__*) for the input element."""
        return {
            k: v
            for k, v in self._props.items()
            if v is not None and k.startswith(_ALPINE_PREFIXES)
        }

    def _render(self, context: HueContext) -> Component:
        if self._name is None:
            raise ValueError(
                f"{type(self).__name__} requires a name — "
                f"pass it to the constructor or call .name()."
            )

        label_text: str = self._get_prop("label", self._name)
        disabled: bool = self._get_prop("disabled", False)
        required: bool = self._get_prop("required", True)
        hidden_label: bool = self._get_prop("hidden_label", False)
        placeholder = self._get_prop("placeholder")
        autocomplete_val: Autocomplete = self._get_prop("autocomplete", "off")
        help_text_val = self._get_prop("help_text")
        error_text_val = self._get_prop("error_text")
        aria_invalid = self._get_aria_invalid()

        classes = _get_base_input_classes(
            disabled=disabled,
            aria_invalid=aria_invalid,
            class_=self._get_prop("class_"),
        )

        return Stack(
            Label(
                label_text,
                required=required,
                disabled=disabled,
                hidden_label=hidden_label,
                html_for=self._name,
            ),
            html.div(
                html.input_(
                    type=self._input_type,
                    name=self._name,
                    id=self._name,
                    class_=classes,
                    placeholder=placeholder,
                    autocomplete=autocomplete_val,
                    aria_label=label_text,
                    aria_required=required,
                    aria_invalid=aria_invalid,
                    aria_disabled=disabled,
                    aria_errormessage=error_text_val,
                    aria_describedby=self._get_aria_describedby(),
                    **self._get_extra_input_attrs(),
                    **self._get_alpine_attrs(),
                ),
                class_="relative flex items-center w-full",
            ),
            render_if(
                help_text_val,
                lambda ht: Text(ht, variant="body", muted=True, tag=html.span),
            ),
            render_if(
                error_text_val,
                lambda et: Text(et, variant="body", destructive=True, role="alert"),
            ),
            direction="vertical",
            spacing="sm",
        )


class TextInput(_BaseInput):
    """
    Chainable text input.

    Example::

        TextInput("username").label("Username").placeholder("Enter username")
    """

    _input_type: str = "text"


class EmailInput(_BaseInput):
    """
    Chainable email input.

    Example::

        EmailInput("email").label("Email").placeholder("you@example.com")
    """

    _input_type: str = "email"

    def __init__(self) -> None:
        super().__init__()
        self._props["autocomplete"] = "email"


class PasswordInput(_BaseInput):
    """
    Chainable password input.

    Example::

        PasswordInput("password").label("Password").placeholder("••••••••")
    """

    _input_type: str = "password"

    def __init__(self) -> None:
        super().__init__()
        self._props["autocomplete"] = "current-password"


class NumberInput(_BaseInput):
    """
    Chainable number input.

    Example::

        NumberInput("quantity").label("Quantity").min(1).max(100).step(1)
    """

    _input_type: str = "number"

    def min(self, value: int) -> Self:  # noqa: A003
        self._props["min"] = value
        return self

    def max(self, value: int) -> Self:  # noqa: A003
        self._props["max"] = value
        return self

    def step(self, value: float | str) -> Self:
        self._props["step"] = value
        return self

    def _get_extra_input_attrs(self) -> dict:
        return {
            "min": self._get_prop("min"),
            "max": self._get_prop("max"),
            "step": self._get_prop("step"),
        }
