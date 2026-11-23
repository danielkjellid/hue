"""
The select-only combobox as parts.

    SelectRoot().name("plan").label("Plan").content(
        SelectTrigger().content(SelectValue()),
        SelectListbox().content(
            SelectOption().value("free").label("Free"),
            SelectOption().value("pro").label("Pro"),
        ),
    )

The root holds the name, the value, the Alpine scope and the hidden field that
is submitted. Every other part reads the root's state from the context, so
its ids come from the root's id and its x-ref registers on the root's scope.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Iterator
from dataclasses import dataclass

from htmy import Context, html
from typing_extensions import Self

from hue.base import AlpineModelMixin, ChainableComponent, FormElementMixin
from hue.headless._overlay import anchor
from hue.headless.part import Part
from hue.js import call
from hue.types.core import Component, ComponentType

_GROUP_SCOPE = "hue-select-group"


@dataclass(frozen=True, slots=True)
class SelectState:
    """
    What a select's parts need to know about the select they are in.

    An option needs only the first two, which is all a Combobox offers the
    options it borrows.
    """

    control_id: str
    values: frozenset[str]
    label: str = ""
    placeholder: str = ""
    # The chosen option's label, where the root could find the option.
    chosen: str | None = None
    disabled: bool = False
    required: bool = False
    invalid: bool = False

    @property
    def listbox_id(self) -> str:
        return f"{self.control_id}-listbox"

    def option_id(self, value: str) -> str:
        # A digest rather than a slug of the value: a slug folds "a b" and
        # "a-b", and every value written in another script, into one id, and
        # the keys find the active option by its id. It stays the same across
        # renders, so a Combobox that redraws its options keeps its place.
        digest = hashlib.blake2s(value.encode(), digest_size=4).hexdigest()
        return f"{self.control_id}-option-{digest}"


class SelectRoot(AlpineModelMixin, FormElementMixin, Part):
    """
    The scope a select's parts share, and the hidden field that submits its
    value under name.

    id() names the control, so it lands on the trigger, where a label's for
    points. x_model() and form() belong to what is submitted, so they land on
    the hidden field.
    """

    def name(self, value: str) -> Self:
        self._props["name"] = value
        return self

    def label(self, value: str) -> Self:
        """
        What the list of options is called. The name, when not given.
        """
        self._props["label"] = value
        return self

    def value(self, value: str) -> Self:
        """
        Which option starts selected.
        """
        self._props["value"] = value
        return self

    def placeholder(self, value: str) -> Self:
        """
        What SelectValue says while nothing is chosen.
        """
        self._props["placeholder"] = value
        return self

    def disabled(self, value: bool = True) -> Self:
        self._props["disabled"] = value
        return self

    def required(self, value: bool = True) -> Self:
        self._props["required"] = value
        return self

    def invalid(self, value: bool = True) -> Self:
        self._props["invalid"] = value
        return self

    def _name(self) -> str:
        name: str | None = self._get_prop("name")
        if name is None:
            raise ValueError("SelectRoot requires a name; call .name().")
        return name

    def htmy_context(self) -> Context:
        name = self._name()
        value: str | None = self._get_prop("value")
        chosen = next(
            (o for o in options(self._children) if o.option_value == value), None
        )
        return {
            SelectState: SelectState(
                control_id=self._attrs.get("id") or name,
                values=frozenset() if value is None else frozenset([value]),
                label=self._get_prop("label") or name,
                placeholder=self._get_prop("placeholder", ""),
                chosen=None if chosen is None else chosen.option_label,
                disabled=self._get_prop("disabled", False),
                required=self._get_prop("required", False),
                invalid=self._get_prop("invalid", False),
            )
        }

    def _render(self, context: Context) -> Component:
        self._refuse_x_data()
        value: str = self._get_prop("value") or ""
        attrs = self._wired(
            context,
            **{
                "x-data": call("hueSelect", value, self._get_prop("placeholder", "")),
                # Focus leaving closes the list too, so tabbing away or
                # clicking into another document does not leave it open.
                "x-on:click.outside": "hide()",
                "x-on:focusout": "leave($event)",
            },
        )
        attrs.pop("id", None)
        submitted = {key: attrs.pop(key) for key in ("x-model", "form") if key in attrs}
        return html.div(
            html.input_(
                type="hidden",
                name=self._name(),
                value=value,
                # A disabled field is left out of what the form submits.
                disabled=self._get_prop("disabled", False) or None,
                **{"x-ref": "input", "x-bind:value": "value", **submitted},
            ),
            *self._content(),
            **attrs,
        )


class SelectTrigger(Part):
    """
    The button that opens the list and keeps focus while the keys move
    through it. This is the control: it carries the root's id.
    """

    def _render(self, context: Context) -> Component:
        state = self._state(context, SelectState)
        return html.button(
            *self._content(),
            **self._wired(
                context,
                type="button",
                id=state.control_id,
                role="combobox",
                aria_haspopup="listbox",
                aria_controls=state.listbox_id,
                aria_expanded="false",
                aria_required="true" if state.required else None,
                aria_invalid="true" if state.invalid else None,
                disabled=state.disabled or None,
                **{
                    "x-ref": "trigger",
                    "x-bind:aria-expanded": "open",
                    "x-bind:aria-activedescendant": "active",
                    "x-on:click": "open ? hide() : show()",
                    "x-on:keydown": "key($event)",
                },
            ),
        )


class SelectValue(Part):
    """
    The chosen option's label, or the placeholder while nothing is chosen.
    It carries data-placeholder for as long as it shows the placeholder.
    """

    def _render(self, context: Context) -> Component:
        state = self._state(context, SelectState)
        return html.span(
            state.placeholder if state.chosen is None else state.chosen,
            **self._wired(
                context,
                **{
                    "data-placeholder": "" if state.chosen is None else None,
                    "x-text": "label || placeholder",
                    "x-bind:data-placeholder": "label ? null : ''",
                },
            ),
        )


class SelectListbox(Part):
    """
    The list of options, shown under the trigger while the select is open.
    """

    def _render(self, context: Context) -> Component:
        state = self._state(context, SelectState)
        return html.div(
            *self._content(),
            **self._wired(
                context,
                id=state.listbox_id,
                role="listbox",
                aria_label=state.label,
                **{
                    "x-ref": "listbox",
                    # The keys are handled on the trigger, so a press on a group
                    # label, the padding or the scrollbar must not take focus.
                    "x-on:mousedown.prevent": "",
                    "x-show": "open",
                    "x-cloak": True,
                    **anchor("bottom-start", "$refs.trigger"),
                },
            ),
        )


class SelectGroup(Part):
    """
    A run of options named by the SelectGroupLabel inside it.
    """

    def _render(self, context: Context) -> Component:
        self._state(context, SelectState)
        return html.div(
            *self._content(),
            **self._wired(
                context,
                role="group",
                **{
                    # Two groups may share a label, so the label's id comes
                    # from Alpine's $id in a scope of the group's own.
                    "x-id": f"['{_GROUP_SCOPE}']",
                    "x-bind:aria-labelledby": f"$id('{_GROUP_SCOPE}')",
                },
            ),
        )


class SelectGroupLabel(Part):
    """
    The heading of the SelectGroup it sits in.
    """

    def _render(self, context: Context) -> Component:
        self._state(context, SelectState)
        return html.div(
            *self._content(),
            **self._wired(context, **{"x-bind:id": f"$id('{_GROUP_SCOPE}')"}),
        )


class SelectOption(Part):
    """
    One choice: its value and what it is called. Its content is the label
    unless content() gives it something else to draw.
    """

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
        What the option is called, in the list and in SelectValue once it is
        chosen. The value, when not given.
        """
        self._props["label"] = value
        return self

    def disabled(self, value: bool = True) -> Self:
        self._props["disabled"] = value
        return self

    def _content(self) -> tuple[ComponentType, ...]:
        return self._children or (self.option_label,)

    def _render(self, context: Context) -> Component:
        state = self._state(context, SelectState)
        value = self.option_value
        option_id = state.option_id(value)
        return html.div(
            *self._content(),
            **self._wired(
                context,
                id=option_id,
                role="option",
                aria_selected="true" if value in state.values else "false",
                aria_disabled="true" if self._get_prop("disabled", False) else None,
                **{
                    "data-value": value,
                    "data-label": self.option_label,
                    "x-bind:aria-selected": f"chosen({json.dumps(value)})",
                    "x-bind:data-active": f"active === {json.dumps(option_id)} || null",
                    "x-on:click": "choose($el)",
                    "x-on:mousemove": "activate($el)",
                },
            ),
        )


def options(children: Iterable[ComponentType]) -> Iterator[SelectOption]:
    """
    Every option among children, however deep in groups or other markup.
    """
    for child in children:
        if isinstance(child, SelectOption):
            yield child
        elif isinstance(child, ChainableComponent):
            yield from options(child._children)
