from __future__ import annotations

from htmy import Context, html
from typing_extensions import Self

from hue.js import call
from hue.types.core import Component
from hue.ui._styles import FOCUS_RING, GROUP_STATES, ControlSize
from hue.ui.atoms.icon import HueIcon
from hue.ui.base import modelable
from hue.ui.form import FieldControl
from hue.ui.molecules import _overlay
from hue.ui.molecules.select import (
    SelectState,
    _options,
    _widest,
)
from hue.utils import classnames, render_when

# A minimum rather than a height: with several values chosen, the tokens wrap
# onto more lines and the field grows to hold them.
_SIZES: dict[ControlSize, str] = {
    "sm": "min-h-control-sm ps-[9px] pe-1 text-sm",
    "md": "min-h-control-md ps-[11px] pe-1.5 text-base",
    "lg": "min-h-control-lg ps-[14px] pe-2 text-md",
}

# GROUP_SHELL's frame around two things in a row: what is typed and chosen,
# and the toggle at the end.
_SHELL = (
    "flex w-full cursor-text items-center gap-1 rounded-md border "
    f"border-border-input bg-surface py-[3px] shadow-field {GROUP_STATES}"
)

# Never narrower than a few letters, so there is always room to type after
# the last token before the line wraps, unless the line itself is narrower: a
# field wider than its column would run under the chevron.
_FIELD = (
    "h-6 min-w-[min(5rem,100%)] flex-1 text-ellipsis border-none bg-transparent "
    "px-0.5 text-fg outline-none "
    "placeholder:text-fg-subtle disabled:cursor-not-allowed disabled:text-fg-disabled"
)

# The tokens and the text field flow along a line and onto the next. Contained,
# so they wrap within the width the labels behind them set rather than
# widening the field as tokens are added.
_ENTRY = "flex flex-wrap items-center gap-1 [contain:inline-size] [grid-area:1/1]"

# Height zero, so the labels give the field its width and nothing else.
_SIZER = "invisible h-0 overflow-hidden whitespace-nowrap px-0.5 [grid-area:1/1]"

_POPUP = (
    "z-70 max-w-[calc(100vw-2rem)] rounded-lg border border-border "
    "bg-surface-raised p-1 shadow-raised"
)

_TOKEN = (
    "inline-flex h-6 min-w-0 max-w-full items-center gap-0.5 rounded-sm "
    "bg-surface-active ps-[9px] pe-[3px] text-xs font-medium text-fg"
)

_TOKEN_REMOVE = classnames(
    FOCUS_RING,
    "inline-flex size-[18px] flex-none cursor-pointer items-center justify-center "
    "rounded-xs text-fg-muted hover:bg-border-hover hover:text-fg",
)


class Combobox(FieldControl):
    """
    A text field that filters a list of options as you type, for a list too
    long to scroll through.

    Follows the ARIA combobox pattern with list autocomplete: the field keeps
    focus, the arrows move through the options that match, and Enter picks
    one. Options are SelectOption and SelectGroup, the same as in a Select.
    multiple() lets several be chosen, shown in the field as tokens, and
    empty_message() is what it says when nothing matches.
    """

    category = "Inputs"

    def value(self, *values: str) -> Self:
        """
        Which options start chosen. More than one needs multiple().
        """
        self._props["value"] = values
        return self

    def multiple(self, value: bool = True) -> Self:
        self._props["multiple"] = value
        return self

    def placeholder(self, value: str) -> Self:
        self._props["placeholder"] = value
        return self

    def empty_message(self, value: str) -> Self:
        """
        What the list says when nothing matches what was typed.
        """
        self._props["empty_message"] = value
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

    def _values(self) -> tuple[str, ...]:
        values: tuple[str, ...] = self._get_prop("value", ())
        if len(values) > 1 and not self._get_prop("multiple", False):
            raise ValueError(
                "A Combobox holds one value unless it is multiple(); "
                f"it was given {len(values)}."
            )
        return values

    def htmy_context(self) -> Context:
        return {SelectState: SelectState(self._input_id(), frozenset(self._values()))}

    def _render(self, context: Context) -> Component:
        name = self._require_name()
        control_id = self._input_id()
        size: ControlSize = self._get_prop("size", "md")
        multiple: bool = self._get_prop("multiple", False)
        disabled: bool = self._get_prop("disabled", False)
        error: str | None = self._error(context)
        label: str = self._get_prop("label") or name
        listbox_id = f"{control_id}-listbox"
        placeholder: str = self._get_prop("placeholder", "")

        values = self._values()
        labels = {o.option_value: o.option_label for o in _options(self._children)}
        chosen = [{"value": v, "label": labels.get(v, v)} for v in values]

        attrs = self._control_attrs(
            context,
            type="text",
            id=control_id,
            role="combobox",
            autocomplete="off",
            aria_autocomplete="list",
            aria_controls=listbox_id,
            aria_expanded="false",
            aria_required="true" if self._get_prop("required", False) else None,
            aria_invalid="true" if error is not None else None,
            aria_describedby=self._describedby(context),
            placeholder=placeholder or None,
            disabled=disabled or None,
            # What a single combobox shows before Alpine starts is what it holds.
            value=None if multiple or not chosen else chosen[0]["label"],
            class_=_FIELD,
            **{
                "x-ref": "input",
                "x-model": "query",
                ":aria-expanded": "open",
                ":aria-activedescendant": "active",
                "x-on:focus": "focused()",
                "x-on:input": "search()",
                "x-on:keydown": "key($event)",
            },
        )
        # The caller's binding and form go on the root and the submitted
        # fields; the text field only ever holds what is being typed.
        form = attrs.pop("form", None)
        caller_model = self._attrs.get("x-model")

        submitted = html.template(
            html.input_(
                type="hidden",
                name=name,
                form=form,
                # A disabled field is left out of what the form submits.
                disabled=disabled or None,
                **{":value": "item.value"},
            ),
            **{"x-for": "item in selected", ":key": "item.value"},
        )
        tokens = html.template(
            html.span(
                html.span(**{"x-text": "item.label"}, class_="truncate"),
                html.button(
                    HueIcon("x").class_("size-3"),
                    type="button",
                    disabled=disabled or None,
                    class_=_TOKEN_REMOVE,
                    **{
                        ":aria-label": "`Remove ${item.label}`",
                        "x-on:click.stop": "remove(item.value)",
                    },
                ),
                class_=_TOKEN,
            ),
            **{"x-for": "item in selected", ":key": "item.value"},
        )
        toggle = html.button(
            HueIcon("chevron-down").class_(
                "size-4 transition-transform duration-150 in-aria-expanded:rotate-180"
            ),
            type="button",
            tabindex="-1",
            aria_label=label,
            aria_controls=listbox_id,
            aria_expanded="false",
            disabled=disabled or None,
            class_=(
                "ms-auto inline-flex size-6 flex-none cursor-pointer items-center "
                "justify-center rounded-sm text-fg-subtle hover:text-fg "
                "disabled:cursor-not-allowed"
            ),
            **{
                ":aria-expanded": "open",
                "x-on:mousedown.prevent": "",
                # Kept from the field, whose click would open what this closed.
                "x-on:click.stop": "toggle()",
            },
        )
        shell = html.div(
            # As wide as the longest option or the placeholder, the way a
            # Select is, whatever is chosen or typed. The labels are drawn
            # invisibly in the same grid cell as the entry to set that width.
            html.div(
                html.div(
                    render_when(multiple, tokens),
                    html.input_(**attrs),
                    class_=_ENTRY,
                ),
                *(
                    html.div(text, class_=_SIZER)
                    for text in _widest(placeholder, *labels.values())
                ),
                # A label is too narrow a measure for a row of tokens, so a
                # multiple field is never narrower than this - unless its
                # container is, since the column can shrink to nothing.
                render_when(multiple, html.div(class_=classnames(_SIZER, "w-64"))),
                class_="grid min-w-0 flex-1 grid-cols-[minmax(0,1fr)]",
            ),
            toggle,
            class_=classnames(_SHELL, _SIZES[size], self._get_prop("class_")),
            **{
                "x-ref": "shell",
                # The shell is a div, which a disabled attribute cannot stop.
                "x-on:click": None if disabled else "$refs.input.focus(); show()",
            },
        )
        popup = html.div(
            html.div(
                *self._children,
                id=listbox_id,
                role="listbox",
                aria_label=label,
                aria_multiselectable="true" if multiple else None,
                class_="max-h-70 overflow-y-auto",
                **{"x-ref": "listbox"},
            ),
            # Always on the page, and empty while something matches: a live
            # region only speaks when its text changes, so one that appeared
            # with its message already in it would say nothing.
            html.div(
                role="status",
                class_=(
                    "px-2 py-3.5 text-center text-base text-fg-subtle empty:hidden"
                ),
                **{"x-text": "empty ? emptyMessage : ''"},
            ),
            class_=_POPUP,
            **{
                "x-ref": "popup",
                "x-show": "open",
                "x-cloak": True,
                # Clicking an option would otherwise take focus from the field
                # and close the list before the click arrived.
                "x-on:mousedown.prevent": "",
                **_overlay.anchor("bottom-start", "$refs.shell"),
            },
        )
        root_attrs: dict[str, object] = {
            "x-data": call(
                "hueCombobox",
                chosen,
                multiple,
                self._get_prop("empty_message", "Nothing matches."),
            ),
            "x-on:focusout": "leave($event)",
        }
        if caller_model:
            root_attrs.update(
                modelable(caller_model, "values" if multiple else "value")
            )
        return self._field(
            context,
            html.div(
                submitted,
                shell,
                popup,
                class_="relative w-full",
                **root_attrs,
            ),
        )
