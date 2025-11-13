from dataclasses import dataclass, field
from typing import Annotated, Literal

from htmy import html
from typing_extensions import Doc

from hue.types.core import BaseComponent
from hue.ui.atoms.stack import Stack
from hue.ui.atoms.text import Label, Text
from hue.utils import classes_if_else, classnames, render_if

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


@dataclass(slots=True, frozen=True, kw_only=True)
class _BaseInput(BaseComponent):
    name: Annotated[str, Doc("The name of the input field. Also used as id.")]

    label: Annotated[str, Doc("The label of the input field.")]

    type: Annotated[
        Literal["text", "number", "email", "password"],
        Doc("The type of the input field."),
    ]

    min_length: Annotated[
        int | None,
        Doc("The minimum length of the input field."),
    ] = None

    max_length: Annotated[
        int | None,
        Doc("The maximum length of the input field."),
    ] = None

    disabled: Annotated[
        bool,
        Doc("Whether the input field is disabled."),
    ] = False

    required: Annotated[
        bool, Doc("Whether the input field should be treated as required.")
    ] = True

    hidden_label: Annotated[
        bool,
        Doc("Whether the label should be available for screen readers only."),
    ] = False

    autocomplete: Annotated[
        Autocomplete,
        Doc("The html autocomplete attribute of the input field."),
    ] = "off"

    placeholder: Annotated[
        str | None,
        Doc("The placeholder text of the input field."),
    ] = None

    help_text: Annotated[
        str | None,
        Doc("The help text positioned bellow the input field."),
    ] = None

    error_text: Annotated[
        str | None,
        Doc("The error text positioned bellow the input field."),
    ] = None

    @property
    def aria_invalid(self) -> bool:
        return self.error_text is not None

    @property
    def error_text_id(self) -> str:
        return f"{self.name}-error"

    @property
    def description_id(self) -> str:
        return f"{self.name}-description"

    @property
    def aria_describedby(self) -> str:
        description_ids = [
            self.description_id if self.help_text else None,
            self.error_text_id if self.error_text else None,
        ]
        return " ".join([val for val in description_ids if val is not None])

    @property
    def is_number_input(self) -> bool:
        return isinstance(self, NumberInput)

    def htmy(self, *args, **kwargs) -> Stack:
        classes = (
            _get_base_input_classes(
                disabled=self.disabled,
                aria_invalid=self.aria_invalid,
                class_=self.class_,
            ),
        )

        # Some attributes are only relevant for certain input types.
        input_attrs = {}
        if self.is_number_input:
            input_attrs = {
                "min": self.min,
                "max": self.max,
                "step": self.step,
            }
        else:
            input_attrs = {
                "min_length": self.min_length,
                "max_length": self.max_length,
            }

        return Stack(
            Label(
                self.label,
                required=self.required,
                disabled=self.disabled,
                hidden_label=self.hidden_label,
                html_for=self.name,
            ),
            html.div(
                html.input_(
                    type=self.type,
                    name=self.name,
                    id=self.name,
                    class_=classes,
                    placeholder=self.placeholder,
                    autocomplete=self.autocomplete,
                    # Aria attributes
                    aria_label=self.label,
                    aria_required=self.required,
                    aria_invalid=self.aria_invalid,
                    aria_disabled=self.disabled,
                    aria_errormessage=self.error_text,
                    aria_describedby=self.aria_describedby,
                    **input_attrs,
                ),
                class_="relative flex items-center w-full",
            ),
            render_if(
                self.help_text is not None,
                Text(
                    self.help_text,  # type: ignore
                    variant="body",
                    muted=True,
                    tag=html.span,
                ),
            ),
            render_if(
                self.error_text is not None,
                Text(
                    self.error_text,  # type: ignore
                    variant="body",
                    destructive=True,
                    role="alert",
                ),
            ),
            direction="vertical",
            spacing="sm",
        )


@dataclass(slots=True, frozen=True, kw_only=True)
class EmailInput(_BaseInput):
    type: Literal["email"] = field(default="email", init=False)
    autocomplete: Literal["email"] = field(default="email", init=False)


@dataclass(slots=True, frozen=True, kw_only=True)
class TextInput(_BaseInput):
    type: Literal["text"] = field(default="text", init=False)
    autocomplete: Literal["off"] = field(default="off", init=False)


@dataclass(slots=True, frozen=True, kw_only=True)
class NumberInput(_BaseInput):
    type: Literal["number"] = field(default="number", init=False)

    min: Annotated[int | None, Doc("The minimum value of the number field.")] = None
    max: Annotated[int | None, Doc("The maximum value of the number field.")] = None
    step: Annotated[float | str | None, Doc("The step value of the number field.")] = (
        None
    )


@dataclass(slots=True, frozen=True, kw_only=True)
class PasswordInput(_BaseInput):
    type: Literal["password"] = field(default="password", init=False)
    autocomplete: Literal["current-password"] = field(
        default="current-password", init=False
    )


def _get_base_input_classes(
    disabled: bool,
    aria_invalid: bool,
    class_: str | None = None,
) -> str:
    """
    Get the base input classes.
    """
    return classnames(
        [
            "flex",
            "grow",
            "rounded-lg",
            "border",
            "px-4",
            "py-2",
            "text-sm",
            "leading-6",
            "shadow-xs",
            "transition-colors",
            "duration-100",
            "placeholder:text-surface-500",
            "outline-primary",
            "focus:outline",
            "focus:outline-2",
            "focus:-outline-offset-1",
            "w-full",
        ],
        classes_if_else(
            disabled,
            [
                "cursor-not-allowed",
                "bg-surface-50",
                "text-surface-300",
                "placeholder:text-surface-300",
                "dark:bg-white/5",
                "dark:text-surface-200",
                "dark:placeholder:text-surface-200",
            ],
            [
                "bg-background",
                "text-surface-900",
                "hover:border-surface-300",
                "dark:hover-border-surface-200",
            ],
        ),
        classes_if_else(
            aria_invalid,
            [
                "border-destructive",
                "outline-destructive",
                "hover:border-destructive",
                "dark:hover:border-destructive",
            ],
            ["border-surface-200", "dark:border-surface-100"],
        ),
        class_,
    )
