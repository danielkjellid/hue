from __future__ import annotations

from typing import Literal

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component
from hue.ui._styles import CONTROL_SIZES, FIELD_SHELL, ControlSize
from hue.ui.form import FormControl
from hue.ui.molecules.field import FieldLayout
from hue.utils import classnames

type Autocomplete = Literal[
    "off",
    "on",
    "name",
    "email",
    "username",
    "new-password",
    "current-password",
    "one-time-code",
    "organization",
    "street-address",
    "address-line1",
    "address-line2",
    "address-line3",
    "address-level1",
    "address-level2",
    "address-level3",
    "address-level4",
    "country",
    "country-name",
    "postal-code",
    "cc-name",
    "cc-number",
    "cc-exp",
    "cc-exp-month",
    "cc-exp-year",
    "cc-csc",
    "cc-type",
    "transaction-currency",
    "transaction-amount",
    "language",
    "bday",
    "bday-day",
    "bday-month",
    "bday-year",
    "sex",
    "tel",
    "tel-country-code",
    "tel-national",
    "tel-area-code",
    "tel-local",
    "tel-extension",
    "impp",
    "url",
    "photo",
]


class _BaseInput(FormControl):
    """
    Shared implementation of the text-like inputs. Use a concrete subclass:
    TextInput, EmailInput, NumberInput or PasswordInput.
    """

    _input_type: str = "text"

    category = "Inputs"

    @classmethod
    def example(cls) -> Self:
        return cls().name("example").label("Example").placeholder("Type here")

    def placeholder(self, value: str) -> Self:
        self._props["placeholder"] = value
        return self

    def value(self, value: str) -> Self:
        """
        What the input starts with, for a form rendered from existing data.
        """
        self._props["value"] = value
        return self

    def size(self, value: ControlSize) -> Self:
        self._props["size"] = value
        return self

    def readonly(self, value: bool = True) -> Self:
        """
        Show the value but refuse edits. Unlike a disabled input it stays
        focusable and copyable, which is what a shown-but-fixed value needs.

        On the input rather than on every control: a checkbox has no readonly
        state in HTML, only disabled.
        """
        self._props["readonly"] = value
        return self

    def hidden_label(self, value: bool = True) -> Self:
        self._props["hidden_label"] = value
        return self

    def layout(self, value: FieldLayout) -> Self:
        """
        Put the label beside the input rather than above it, for a settings
        page where every row shares one edge.
        """
        self._props["layout"] = value
        return self

    def autocomplete(self, value: Autocomplete) -> Self:
        self._props["autocomplete"] = value
        return self

    def min_length(self, value: int) -> Self:
        self._props["min_length"] = value
        return self

    def max_length(self, value: int) -> Self:
        self._props["max_length"] = value
        return self

    def _get_extra_input_attrs(self) -> dict[str, object]:
        """
        Type-specific attributes; NumberInput overrides this.
        """
        return {
            "minlength": self._get_prop("min_length"),
            "maxlength": self._get_prop("max_length"),
        }

    def _get_extra_classes(self) -> str:
        """
        Type-specific classes, kept apart from the attributes so a subclass
        adding one does not have to restate the whole shell.
        """
        return ""

    def _render(self, context: HueContext) -> Component:
        name = self._require_name()
        size: ControlSize = self._get_prop("size", "md")
        disabled: bool = self._get_prop("disabled", False)
        required: bool = self._get_prop("required", False)
        readonly: bool = self._get_prop("readonly", False)
        autocomplete: Autocomplete = self._get_prop("autocomplete", "off")
        error: str | None = self._get_prop("error")
        input_id = self._input_id()

        # The visible <label for> supplies the accessible name, so no aria-label.
        # Native disabled/required/readonly carry their own ARIA semantics;
        # aria-invalid is what the shell keys its error border off.
        input_attrs = self._control_attrs(
            type=self._input_type,
            name=name,
            id=input_id,
            class_=classnames(
                FIELD_SHELL,
                CONTROL_SIZES[size],
                self._get_extra_classes(),
                self._get_prop("class_"),
            ),
            placeholder=self._get_prop("placeholder"),
            value=self._get_prop("value"),
            autocomplete=autocomplete,
            disabled=disabled or None,
            required=required or None,
            readonly=readonly or None,
            aria_invalid="true" if error is not None else None,
            aria_describedby=self._describedby(),
            **self._get_extra_input_attrs(),
        )

        return self._field(html.input_(**input_attrs))


class TextInput(_BaseInput):
    """
    A single-line text input.

        TextInput("username").label("Username").placeholder("Enter username")
    """

    _input_type = "text"


class EmailInput(_BaseInput):
    """
    An email input, with autocomplete preset to email.

        EmailInput("email").label("Email").placeholder("you@example.com")
    """

    _input_type = "email"

    def __init__(self, name: str | None = None) -> None:
        super().__init__(name)
        self._props["autocomplete"] = "email"


class PasswordInput(_BaseInput):
    """
    A password input, with autocomplete preset to current-password.

        PasswordInput("password").label("Password")
    """

    _input_type = "password"

    def __init__(self, name: str | None = None) -> None:
        super().__init__(name)
        self._props["autocomplete"] = "current-password"


class NumberInput(_BaseInput):
    """
    A number input with min(), max() and step().

        NumberInput("quantity").label("Quantity").min(1).max(100).step(1)
    """

    _input_type = "number"

    def min(self, value: int) -> Self:
        self._props["min"] = value
        return self

    def max(self, value: int) -> Self:
        self._props["max"] = value
        return self

    def step(self, value: float | str) -> Self:
        self._props["step"] = value
        return self

    def _get_extra_input_attrs(self) -> dict[str, object]:
        return {
            "min": self._get_prop("min"),
            "max": self._get_prop("max"),
            "step": self._get_prop("step"),
            # A phone offers digits rather than a full keyboard.
            "inputmode": "numeric",
        }

    def _get_extra_classes(self) -> str:
        # Figures on shared widths, so a column of them lines up.
        return "tabular-nums"
