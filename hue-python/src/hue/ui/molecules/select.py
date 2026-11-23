from __future__ import annotations

from typing import ClassVar

from htmy import Context, html
from typing_extensions import Self

from hue.headless import select as headless
from hue.types.core import Component, ComponentType
from hue.ui._styles import CONTROL_SIZES, FIELD_SHELL, ControlSize
from hue.ui.atoms.icon import HueIcon
from hue.ui.form import FieldControl
from hue.utils import classnames, render_if

# The field's own shell, laid out as a row: the value takes the space and
# truncates, the chevron keeps its place at the end.
_TRIGGER = classnames(
    FIELD_SHELL,
    "flex cursor-pointer items-center justify-between gap-2 text-start",
    # Open reads like focused: the listbox belongs to the trigger, and the
    # halo says which control it came from. An invalid one stays red, as it
    # does when focused.
    "not-aria-invalid:aria-expanded:border-accent "
    "not-aria-invalid:aria-expanded:ring-3 "
    "not-aria-invalid:aria-expanded:ring-accent-subtle "
    "aria-invalid:aria-expanded:ring-2 aria-invalid:aria-expanded:ring-danger",
)

# The placeholder is quieter than a value. The part says which it is showing.
_VALUE = "truncate [grid-area:1/1] data-placeholder:text-fg-subtle"

_LISTBOX = (
    "z-70 max-h-70 max-w-[calc(100vw-2rem)] overflow-y-auto rounded-lg border "
    "border-border bg-surface-raised p-1 shadow-raised"
)

# Active is where the keys are; selected is the value. Both can be true of
# one option, and selected wins the colour, so the value is always findable.
_OPTION = (
    "flex cursor-pointer select-none items-center gap-2 rounded-sm px-2 py-[7px] "
    "text-base text-fg [&>svg]:size-4 [&>svg]:flex-none "
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

    def _render(self, context: Context) -> Component:
        name = self._require_name()
        size: ControlSize = self._get_prop("size", "md")
        value: str | None = self._get_prop("value")
        placeholder: str = self._get_prop("placeholder", "")
        labels = (o.option_label for o in headless.options(self._children))

        root = (
            headless.SelectRoot()
            .name(name)
            .id(self._input_id())
            .label(self._get_prop("label") or name)
            .placeholder(placeholder)
            .disabled(self._get_prop("disabled", False))
            .required(self._get_prop("required", False))
            .invalid(self._error(context) is not None)
            .class_("relative w-full")
        )
        if value is not None:
            root.value(value)
        trigger = (
            headless.SelectTrigger()
            .class_(classnames(_TRIGGER, CONTROL_SIZES[size], self._get_prop("class_")))
            .content(
                # Every label sits in the same grid cell, only the chosen one
                # visible, so the trigger is as wide as its longest option the
                # way a native select is, and choosing does not resize it.
                html.span(
                    headless.SelectValue().class_(_VALUE),
                    *(
                        html.span(text, class_="invisible truncate [grid-area:1/1]")
                        for text in _widest(placeholder, *labels)
                    ),
                    class_="grid min-w-0 flex-1",
                ),
                HueIcon("chevron-down").class_(
                    "size-4 flex-none text-fg-subtle transition-transform "
                    "duration-150 in-aria-expanded:rotate-180"
                ),
            )
        )
        listbox = headless.SelectListbox().class_(_LISTBOX).content(*self._children)
        # The fade is part of the look, so the part does not bring it.
        listbox._attrs["x-transition.opacity"] = ""

        # What the caller set on the Select describes the control, which is
        # the trigger. A two-way binding and the form it belongs to go on the
        # field that is submitted, which the root draws.
        attrs = self._control_attrs(
            context, aria_describedby=self._describedby(context)
        )
        attrs.pop("id", None)
        for key in ("x-model", "form"):
            if attrs.get(key):
                root._attrs[key] = attrs.pop(key)
        trigger._attrs.update(attrs)

        return self._field(context, root.content(trigger, listbox))


def _widest(*texts: str) -> list[str]:
    """
    The few longest of texts, which are what a field drawn as wide as its
    longest option needs to measure.

    Counted in characters, which only approximates width in a proportional
    font, so the top few are kept rather than one. Drawing every label would
    make a list of two hundred options two hundred more elements.
    """
    return sorted(filter(None, texts), key=len, reverse=True)[:3]


class SelectGroup(headless.SelectGroup):
    """
    A labelled run of options inside a Select.
    """

    def label(self, value: str) -> Self:
        self._props["label"] = value
        return self

    def _content(self) -> tuple[ComponentType, ...]:
        label = headless.SelectGroupLabel().class_(_GROUP_LABEL)
        return (label.content(self._get_prop("label", "")), *self._children)


class SelectOption(headless.SelectOption):
    """
    One choice in a Select: its value, what it is called, and optionally a
    description under the label, an icon before it and metadata after it.
    """

    default_class: ClassVar[str] = _OPTION

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

    def _content(self) -> tuple[ComponentType, ...]:
        return (
            render_if(self._get_prop("icon"), lambda icon: icon),
            html.span(
                html.span(self.option_label, class_="block truncate"),
                render_if(
                    self._get_prop("description"),
                    lambda text: html.span(
                        text, class_="block truncate text-sm font-normal text-fg-muted"
                    ),
                ),
                class_="min-w-0 flex-1",
            ),
            render_if(
                self._get_prop("meta"),
                lambda text: html.span(
                    text,
                    # Subtle fails contrast on a lit row's fill in dark.
                    class_="flex-none text-xs text-fg-subtle "
                    "in-data-active:text-fg-muted in-aria-selected:text-fg-muted",
                ),
            ),
        )
