from __future__ import annotations

from typing import Literal, override

from htmy import Context, html
from typing_extensions import Self

from hue.js import unsafe
from hue.types.core import Component, ComponentType
from hue.ui._styles import (
    CONTROL_SIZES,
    FIELD_SHELL,
    GROUP_ACTION,
    GROUP_ADDON,
    GROUP_SHELL,
    GROUPED_CONTROL,
    ControlSize,
)
from hue.ui.atoms.button import Button
from hue.ui.atoms.icon import HueIcon
from hue.ui.base import ChainableComponent
from hue.ui.form import FieldControl
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


def _floats_inside(action: ComponentType) -> bool:
    """
    Whether an attached control sits inside the field rather than being a
    segment of it. An icon-only button does: it acts on what is in the input,
    where a labelled one is a second thing to press beside it.
    """
    return isinstance(action, ChainableComponent) and bool(
        action._get_prop("icon_only", False)
    )


class _BaseInput(FieldControl):
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

    def prefix(self, value: str) -> Self:
        """
        A word attached to the front of the input, such as a URL stem.
        """
        self._props["prefix"] = value
        return self

    def suffix(self, value: str) -> Self:
        """
        A word attached to the end of the input, such as a unit.
        """
        self._props["suffix"] = value
        return self

    def leading_icon(self, value: ComponentType) -> Self:
        """
        An icon inside the input, before the text. Decorative: the label is
        still what names the control.
        """
        self._props["leading_icon"] = value
        return self

    def action(self, value: ComponentType) -> Self:
        """
        A control attached to the end of the input, such as a Copy button.

        A labelled button becomes a segment of the control, flush with its
        end. An icon-only one floats inside the field instead, which is where
        a toggle belongs - it acts on what is in the input rather than being
        a second thing to press beside it.
        """
        self._props["action"] = value
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

    def horizontal(self, value: bool = True) -> Self:
        """
        Put the label beside the control rather than above it, for a
        settings page where every row shares one edge.
        """
        self._props["horizontal"] = value
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

    def _get_group_attrs(self) -> dict[str, object]:
        """
        Attributes for the group, rather than for the input inside it.

        Alpine state belongs here: a scope declared on the input reaches only
        the input, and everything attached to it is a sibling.
        """
        return {}

    _GROUP_PROPS = ("prefix", "suffix", "leading_icon", "action")

    def _is_grouped(self) -> bool:
        return any(self._get_prop(prop) is not None for prop in self._GROUP_PROPS)

    def _control(
        self, input_attrs: dict[str, object], size: ControlSize
    ) -> ComponentType:
        """
        The input, inside a group when anything is attached to it.
        """
        control = html.input_(**input_attrs)
        if not self._is_grouped():
            return control

        icon: ComponentType | None = self._get_prop("leading_icon")
        prefix: str | None = self._get_prop("prefix")
        suffix: str | None = self._get_prop("suffix")
        action: ComponentType | None = self._get_prop("action")

        segments: list[ComponentType] = []
        if prefix is not None:
            segments.append(
                html.span(
                    prefix,
                    class_=f"{GROUP_ADDON} rounded-s-[7px] border-e border-border",
                )
            )
        if icon is not None:
            segments.append(
                html.span(
                    icon,
                    aria_hidden="true",
                    class_="flex flex-none items-center ps-[11px] text-fg-subtle "
                    "[&_svg]:size-4",
                )
            )
        segments.append(control)
        if suffix is not None:
            segments.append(
                html.span(
                    suffix,
                    class_=f"{GROUP_ADDON} rounded-e-[7px] border-s border-border",
                )
            )
        if action is not None:
            segments.append(
                html.span(action, class_="flex items-center pe-1")
                if _floats_inside(action)
                else action
            )

        return html.div(
            *segments,
            class_=classnames(GROUP_SHELL, GROUP_ACTION),
            **self._get_group_attrs(),
        )

    def _render(self, context: Context) -> Component:
        name = self._require_name()
        size: ControlSize = self._get_prop("size", "md")
        disabled: bool = self._get_prop("disabled", False)
        required: bool = self._get_prop("required", False)
        readonly: bool = self._get_prop("readonly", False)
        autocomplete: Autocomplete = self._get_prop("autocomplete", "off")
        error: str | None = self._error(context)
        input_id = self._input_id()

        # The visible <label for> supplies the accessible name, so no aria-label.
        # Native disabled/required/readonly carry their own ARIA semantics;
        # aria-invalid is what the shell keys its error border off.
        input_attrs = self._control_attrs(
            context,
            type=self._input_type,
            name=name,
            id=input_id,
            class_=classnames(
                GROUPED_CONTROL if self._is_grouped() else FIELD_SHELL,
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
            aria_describedby=self._describedby(
                context,
            ),
            **self._get_extra_input_attrs(),
        )

        return self._field(context, self._control(input_attrs, size))


class TextInput(_BaseInput):
    """
    A single-line text input.

        TextInput().name("username").label("Username").placeholder("Enter username")
    """

    _input_type = "text"


class EmailInput(_BaseInput):
    """
    An email input, with autocomplete preset to email.

        EmailInput().name("email").label("Email").placeholder("you@example.com")
    """

    _input_type = "email"

    def __init__(self, name: str | None = None) -> None:
        super().__init__(name)
        self._props["autocomplete"] = "email"


class PasswordInput(_BaseInput):
    """
    A password input, with autocomplete preset to current-password.

        PasswordInput().name("password").label("Password").revealable()
    """

    _input_type = "password"

    def __init__(self, name: str | None = None) -> None:
        super().__init__(name)
        self._props["autocomplete"] = "current-password"

    def revealable(self, value: bool = True) -> Self:
        """
        Attach a toggle that shows the password.

        The toggle keeps one name - "Show password" - and reports its state
        through aria-pressed, rather than renaming itself to "Hide password".
        A control whose label changes under you is announced as a different
        control each time it is pressed.
        """
        self._props["revealable"] = value
        return self

    @override
    def _get_group_attrs(self) -> dict[str, object]:
        # On the group, so the input and the toggle attached to it are both
        # inside the scope. On the input it would reach only the input, and
        # the toggle is its sibling.
        if not self._get_prop("revealable", False):
            return {}
        return {"x-data": '{"shown": false}'}

    @override
    def _render(self, context: Context) -> Component:
        if self._get_prop("revealable", False):
            # The input's own type has to give way to the binding, so the
            # toggle has something to change.
            self.x_bind("type", unsafe("shown ? 'text' : 'password'"))
            self._props.setdefault(
                "action",
                Button()
                .variant("ghost")
                .size("sm")
                .icon_only("Show password")
                .aria_pressed("false")
                .x_on("click", unsafe("shown = !shown"))
                .x_bind("aria-pressed", unsafe("shown"))
                .content(
                    HueIcon("eye").x_show(unsafe("!shown")),
                    HueIcon("eye-off").x_show(unsafe("shown")).x_cloak(),
                ),
            )
        return super()._render(context)


class NumberInput(_BaseInput):
    """
    A number input with min(), max() and step().

        NumberInput().name("quantity").label("Quantity").min(1).max(100).step(1)
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
