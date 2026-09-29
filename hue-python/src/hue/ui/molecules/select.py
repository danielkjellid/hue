from __future__ import annotations

import json
import re
from collections.abc import Iterator
from dataclasses import dataclass
from typing import ClassVar

from htmy import Context, html
from typing_extensions import Self

from hue.js import call
from hue.types.core import Component, ComponentType
from hue.ui._styles import CONTROL_SIZES, FIELD_SHELL, ControlSize
from hue.ui.atoms.icon import HueIcon
from hue.ui.base import ChainableComponent
from hue.ui.form import FieldControl
from hue.utils import classes_if, classnames, render_if

_OFFSET = 6

# The field's own shell, laid out as a row: the value takes the space and
# truncates, the chevron keeps its place at the end.
_TRIGGER = classnames(
    FIELD_SHELL,
    "flex cursor-pointer items-center justify-between gap-2 text-start",
    # Open reads like focused: the listbox belongs to the trigger, and the
    # halo says which control it came from.
    "aria-expanded:border-accent aria-expanded:ring-3 aria-expanded:ring-accent-subtle",
)

_LISTBOX = (
    "z-70 max-h-70 max-w-[calc(100vw-2rem)] overflow-y-auto rounded-lg border "
    "border-border bg-surface-raised p-1 shadow-raised"
)

# Active is where the keys are; selected is the value. Both can be true of
# one option, and selected wins the colour, so the value is always findable.
_OPTION = (
    "flex cursor-pointer select-none items-center gap-2 rounded-sm px-2 py-[7px] "
    "text-base text-fg "
    "data-active:bg-surface-hover "
    "aria-selected:bg-accent-subtle aria-selected:font-medium "
    "aria-selected:text-accent-text "
    "aria-disabled:cursor-not-allowed aria-disabled:text-fg-disabled "
    "aria-disabled:data-active:bg-transparent"
)

_GROUP_LABEL = (
    "px-2 pb-1 pt-1.5 font-ui text-2xs font-bold uppercase tracking-[0.04em] "
    "text-fg-subtle"
)


def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-") or "option"


@dataclass(frozen=True, slots=True)
class SelectState:
    """
    Which select an option is in and what it holds, offered to every option
    and group inside it, so they draw themselves without being handed either.
    """

    control_id: str
    value: str | None

    def option_id(self, value: str) -> str:
        return f"{self.control_id}-option-{_slug(value)}"

    @classmethod
    def from_context(cls, context: Context) -> SelectState:
        found = context.get(cls)
        if isinstance(found, cls):
            return found
        raise ValueError(
            "A SelectOption only means something inside a Select, which is "
            "what holds the value it may be."
        )


class Select(FieldControl):
    """
    A select with room in its options for more than a line of text: a
    description, an icon, trailing metadata, and groups.

    Follows the ARIA select-only combobox pattern. The trigger keeps focus
    while the arrow keys, Home and End, and typing a letter move through the
    options, and Enter picks one. The value is submitted by a hidden field
    under name. Reach for NativeSelect for a plain list, which the platform
    already does well on every device.
    """

    category = "Inputs"

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .name("plan")
            .label("Plan")
            .placeholder("Choose a plan")
            .content(
                SelectOption().value("free").label("Free").meta("$0"),
                SelectOption().value("pro").label("Pro").meta("$49"),
                SelectOption().value("scale").label("Scale").meta("$199"),
            )
        )

    def value(self, value: str) -> Self:
        """
        Which option starts selected.
        """
        self._props["value"] = value
        return self

    def placeholder(self, value: str) -> Self:
        """
        What the trigger says while nothing is chosen.
        """
        self._props["placeholder"] = value
        return self

    def size(self, value: ControlSize) -> Self:
        self._props["size"] = value
        return self

    def hidden_label(self, value: bool = True) -> Self:
        self._props["hidden_label"] = value
        return self

    def horizontal(self, value: bool = True) -> Self:
        """
        Put the label beside the control rather than above it.
        """
        self._props["horizontal"] = value
        return self

    def htmy_context(self) -> Context:
        return {SelectState: SelectState(self._input_id(), self._get_prop("value"))}

    def _render(self, context: Context) -> Component:
        name = self._require_name()
        control_id = self._input_id()
        size: ControlSize = self._get_prop("size", "md")
        disabled: bool = self._get_prop("disabled", False)
        error: str | None = self._error(context)
        value: str | None = self._get_prop("value")
        placeholder: str = self._get_prop("placeholder", "")
        options = list(_options(self._children))
        chosen = next((o for o in options if o.option_value == value), None)
        listbox_id = f"{control_id}-listbox"

        attrs = self._control_attrs(
            context,
            type="button",
            id=control_id,
            role="combobox",
            aria_haspopup="listbox",
            aria_controls=listbox_id,
            aria_expanded="false",
            aria_required="true" if self._get_prop("required", False) else None,
            aria_invalid="true" if error is not None else None,
            aria_describedby=self._describedby(context),
            disabled=disabled or None,
            class_=classnames(_TRIGGER, CONTROL_SIZES[size], self._get_prop("class_")),
            **{
                "x-ref": "trigger",
                ":aria-expanded": "open",
                ":aria-activedescendant": "active",
                "x-on:click": "open ? hide() : show()",
                "x-on:keydown": "key($event)",
            },
        )
        # A two-way binding and the form it belongs to go on the field that is
        # submitted, which is the hidden input, not the button standing in for it.
        moved = {key: attrs.pop(key) for key in ("x-model", "form") if attrs.get(key)}

        trigger = html.button(
            # Every label sits in the same grid cell, only the chosen one
            # visible, so the trigger is as wide as its longest option the way
            # a native select is, and choosing does not resize it.
            html.span(
                html.span(
                    chosen.option_label if chosen is not None else placeholder,
                    class_=classnames(
                        "truncate [grid-area:1/1]",
                        classes_if(chosen is None, ["text-fg-subtle"]),
                    ),
                    **{
                        "x-text": "label || placeholder",
                        # An object, since a string could not take away the
                        # class the server drew the placeholder with.
                        ":class": "{ 'text-fg-subtle': !label }",
                    },
                ),
                *(
                    html.span(text, class_="invisible truncate [grid-area:1/1]")
                    for text in [placeholder, *(o.option_label for o in options)]
                ),
                class_="grid min-w-0 flex-1",
            ),
            HueIcon("chevron-down").class_(
                "size-4 flex-none text-fg-subtle transition-transform duration-150 "
                "in-aria-expanded:rotate-180"
            ),
            **attrs,
        )
        listbox = html.div(
            *self._children,
            id=listbox_id,
            role="listbox",
            aria_label=self._get_prop("label") or name,
            tabindex="-1",
            class_=_LISTBOX,
            **{
                "x-ref": "listbox",
                "x-show": "open",
                "x-cloak": True,
                "x-transition.opacity": "",
                f"x-anchor.bottom-start.offset.{_OFFSET}": "$refs.trigger",
            },
        )
        hidden = html.input_(
            type="hidden",
            name=name,
            value=value or "",
            **{
                "x-ref": "input",
                ":value": "value",
                **moved,
            },
        )
        return self._field(
            context,
            html.div(
                hidden,
                trigger,
                listbox,
                class_="relative w-full",
                **{
                    "x-data": call("hueSelect", value or "", placeholder),
                    "x-on:click.outside": "hide()",
                },
            ),
        )


def _options(children: tuple[ComponentType, ...]) -> Iterator[SelectOption]:
    """
    Every option among children, including those inside groups.
    """
    for child in children:
        if isinstance(child, SelectOption):
            yield child
        elif isinstance(child, SelectGroup):
            yield from _options(child._children)


class SelectGroup(ChainableComponent):
    """
    A labelled run of options inside a Select.
    """

    category: ClassVar[str | None] = None

    def label(self, value: str) -> Self:
        self._props["label"] = value
        return self

    def _render(self, context: Context) -> Component:
        state = SelectState.from_context(context)
        label: str = self._get_prop("label", "")
        label_id = f"{state.control_id}-group-{_slug(label)}"
        return html.div(
            html.div(label, id=label_id, class_=_GROUP_LABEL),
            *self._children,
            role="group",
            aria_labelledby=label_id,
            **self._get_base_html_attrs(),
        )


class SelectOption(ChainableComponent):
    """
    One choice in a Select: its value, what it is called, and optionally a
    description under the label, an icon before it and metadata after it.
    """

    category: ClassVar[str | None] = None

    @property
    def option_value(self) -> str:
        return str(self._get_prop("value", ""))

    @property
    def option_label(self) -> str:
        return str(self._get_prop("label", self.option_value))

    def value(self, value: str) -> Self:
        self._props["value"] = value
        return self

    def label(self, value: str) -> Self:
        """
        What the option is called, shown in the list and in the trigger once
        it is chosen.
        """
        self._props["label"] = value
        return self

    def description(self, value: str) -> Self:
        self._props["description"] = value
        return self

    def meta(self, value: str) -> Self:
        """
        A short note at the end of the row, such as a price or a code.
        """
        self._props["meta"] = value
        return self

    def icon(self, value: ComponentType) -> Self:
        self._props["icon"] = value
        return self

    def disabled(self, value: bool = True) -> Self:
        self._props["disabled"] = value
        return self

    def _render(self, context: Context) -> Component:
        state = SelectState.from_context(context)
        value = self.option_value
        disabled: bool = self._get_prop("disabled", False)
        description: str | None = self._get_prop("description")
        option_id = state.option_id(value)
        return html.div(
            render_if(self._get_prop("icon"), lambda icon: icon),
            html.span(
                html.span(self.option_label, class_="block truncate"),
                render_if(
                    description,
                    lambda text: html.span(
                        text, class_="block truncate text-sm font-normal text-fg-muted"
                    ),
                ),
                class_="min-w-0 flex-1",
            ),
            render_if(
                self._get_prop("meta"),
                lambda text: html.span(text, class_="flex-none text-xs text-fg-subtle"),
            ),
            id=option_id,
            role="option",
            aria_selected="true" if value == state.value else "false",
            aria_disabled="true" if disabled else None,
            class_=classnames(_OPTION, self._get_prop("class_")),
            **{
                "data-value": value,
                "data-label": self.option_label,
                ":aria-selected": f"value === {json.dumps(value)}",
                ":data-active": f"active === {json.dumps(option_id)} || null",
                "x-on:click": "choose($el)",
                "x-on:mousemove": "activate($el)",
            },
            **self._get_base_html_attrs(),
        )
