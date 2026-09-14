from __future__ import annotations

from typing import Literal

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component
from hue.ui.atoms.stack import Stack
from hue.ui.atoms.text import Label
from hue.ui.form import FormControl
from hue.utils import classes_if_else, classnames

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


def _get_base_input_classes(*, disabled: bool, invalid: bool) -> str:
    return classnames(
        "flex grow w-full rounded-lg border px-4 py-2 text-sm leading-6 shadow-xs",
        "transition-colors duration-100 placeholder:text-surface-500",
        "outline-primary focus:outline focus:outline-2 focus:-outline-offset-1",
        classes_if_else(
            disabled,
            [
                "cursor-not-allowed bg-surface-50 text-surface-300",
                "placeholder:text-surface-300 dark:bg-white/5 dark:text-surface-200",
                "dark:placeholder:text-surface-200",
            ],
            [
                "bg-background text-surface-900 hover:border-surface-300",
                "dark:hover:border-surface-200",
            ],
        ),
        classes_if_else(
            invalid,
            [
                "border-destructive outline-destructive hover:border-destructive",
                "dark:hover:border-destructive",
            ],
            ["border-surface-200 dark:border-surface-100"],
        ),
    )


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

    def hidden_label(self, value: bool = True) -> Self:
        self._props["hidden_label"] = value
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

    def _render(self, context: HueContext) -> Component:
        name = self._require_name()
        label_text: str = self._get_prop("label") or name
        disabled: bool = self._get_prop("disabled", False)
        required: bool = self._get_prop("required", False)
        hidden_label: bool = self._get_prop("hidden_label", False)
        autocomplete: Autocomplete = self._get_prop("autocomplete", "off")
        invalid = self._get_prop("error_text") is not None
        input_id = self._input_id()

        # The visible <label for> supplies the accessible name, so no aria-label.
        # Native disabled/required carry their ARIA semantics; aria-invalid and
        # aria-errormessage point at the rendered error text.
        input_attrs = self._control_attrs(
            type=self._input_type,
            name=name,
            id=input_id,
            class_=classnames(
                _get_base_input_classes(disabled=disabled, invalid=invalid),
                self._get_prop("class_"),
            ),
            placeholder=self._get_prop("placeholder"),
            autocomplete=autocomplete,
            disabled=disabled or None,
            required=required or None,
            aria_invalid=invalid or None,
            aria_errormessage=self._error_id(),
            aria_describedby=self._describedby(),
            **self._get_extra_input_attrs(),
        )

        return (
            Stack()
            .direction("vertical")
            .spacing("sm")
            .content(
                Label(label_text)
                .required(required)
                .disabled(disabled)
                .hidden_label(hidden_label)
                .html_for(input_id),
                html.div(
                    html.input_(**input_attrs),
                    class_="relative flex items-center w-full",
                ),
                self._help_text_component(),
                self._error_text_component(),
            )
        )


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
        }
