from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Literal

from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component, ComponentType
from hue.types.html import AriaAtomic, AriaLive, AriaRole
from hue.utils import classnames

# Prop key prefixes forwarded as HTML attributes. Alpine props are stored
# using their final HTML names (e.g. "x-data", "@click", ":class") so
# they bypass the formatter entirely.
_ALPINE_PREFIXES = ("x-", "@", ":")


class ChainableComponent(ABC):
    """
    A base class for SwiftUI-style chainable components.

    Props are set via chainable modifier methods that return ``self``,
    and children are provided through the ``.content()`` method.

    Example::

        Button()
            .variant("primary")
            .size("lg")
            .content(Text("Click me"))
    """

    def __init__(self) -> None:
        self._props: dict[str, Any] = {}
        self._children: tuple[ComponentType, ...] = ()

    # ------------------------------------------------------------------
    # Children
    # ------------------------------------------------------------------

    def content(self, *children: ComponentType) -> Self:
        """Set the component's children."""
        self._children = children
        return self

    # ------------------------------------------------------------------
    # Shared modifiers (class, id, ARIA)
    # ------------------------------------------------------------------

    def class_(self, value: str) -> Self:
        """Append CSS classes."""
        existing = self._props.get("class_")
        self._props["class_"] = classnames(existing, value) if existing else value
        return self

    def id(self, value: str) -> Self:
        self._props["id"] = value
        return self

    def aria_label(self, value: str) -> Self:
        self._props["aria_label"] = value
        return self

    def aria_hidden(self, value: Literal["true", "false"]) -> Self:
        self._props["aria_hidden"] = value
        return self

    def aria_expanded(self, value: str) -> Self:
        self._props["aria_expanded"] = value
        return self

    def aria_controls(self, value: str) -> Self:
        self._props["aria_controls"] = value
        return self

    def aria_live(self, value: AriaLive) -> Self:
        self._props["aria_live"] = value
        return self

    def aria_atomic(self, value: AriaAtomic) -> Self:
        self._props["aria_atomic"] = value
        return self

    def aria_describedby(self, value: str) -> Self:
        self._props["aria_describedby"] = value
        return self

    def role(self, value: AriaRole) -> Self:
        self._props["role"] = value
        return self

    # ------------------------------------------------------------------
    # Alpine — core directives (available on all elements)
    # ------------------------------------------------------------------

    def x_data(self, value: dict[str, Any] | str) -> Self:
        """Declare an Alpine component scope."""
        self._props["x-data"] = value
        return self

    def x_init(self, value: str) -> Self:
        """Run an expression when the component initialises."""
        self._props["x-init"] = value
        return self

    def x_show(self, value: str) -> Self:
        """Toggle element visibility."""
        self._props["x-show"] = value
        return self

    def x_text(self, value: str) -> Self:
        """Set the element's text content."""
        self._props["x-text"] = value
        return self

    def x_html(self, value: str) -> Self:
        """Set the element's inner HTML."""
        self._props["x-html"] = value
        return self

    def x_ref(self, value: str) -> Self:
        """Register an element reference."""
        self._props["x-ref"] = value
        return self

    def x_effect(self, value: str) -> Self:
        """Run an expression reactively when dependencies change."""
        self._props["x-effect"] = value
        return self

    def x_cloak(self) -> Self:
        """Hide the element until Alpine initialises."""
        self._props["x-cloak"] = True
        return self

    def x_ignore(self) -> Self:
        """Prevent Alpine from initialising this element tree."""
        self._props["x-ignore"] = True
        return self

    def x_id(self, value: list[str]) -> Self:
        """Scope ``$id()`` calls to the given names."""
        self._props["x-id"] = value
        return self

    def x_on(self, event: str, expression: str) -> Self:
        """Listen for a browser event (``@<event>``)."""
        self._props[f"@{event}"] = expression
        return self

    def x_bind(self, attr: str, expression: str) -> Self:
        """Dynamically bind an HTML attribute (``:attr``)."""
        self._props[f":{attr}"] = expression
        return self

    # ------------------------------------------------------------------
    # Alpine — transitions (pair with x_show)
    # ------------------------------------------------------------------

    def x_transition_enter(self, value: str) -> Self:
        self._props["x-transition:enter"] = value
        return self

    def x_transition_enter_start(self, value: str) -> Self:
        self._props["x-transition:enter.start"] = value
        return self

    def x_transition_enter_end(self, value: str) -> Self:
        self._props["x-transition:enter.end"] = value
        return self

    def x_transition_leave(self, value: str) -> Self:
        self._props["x-transition:leave"] = value
        return self

    def x_transition_leave_start(self, value: str) -> Self:
        self._props["x-transition:leave.start"] = value
        return self

    def x_transition_leave_end(self, value: str) -> Self:
        self._props["x-transition:leave.end"] = value
        return self

    # ------------------------------------------------------------------
    # Alpine AJAX — target element attributes (any element with an id
    # can be an AJAX target)
    # ------------------------------------------------------------------

    def x_merge(
        self,
        value: Literal[
            "before", "replace", "update", "prepend", "append", "after"
        ],
    ) -> Self:
        """Set the merge strategy for incoming AJAX content."""
        self._props["x-merge"] = value
        return self

    def x_autofocus(self, value: bool = True) -> Self:
        """Focus this element after an AJAX update."""
        self._props["x-autofocus"] = value
        return self

    # ------------------------------------------------------------------
    # Alpine AJAX — event handlers (events bubble, so these can be
    # placed on any ancestor element)
    # ------------------------------------------------------------------

    def ajax_before(self, value: str) -> Self:
        self._props["@ajax:before"] = value
        return self

    def ajax_send(self, value: str) -> Self:
        self._props["@ajax:send"] = value
        return self

    def ajax_redirect(self, value: str) -> Self:
        self._props["@ajax:redirect"] = value
        return self

    def ajax_success(self, value: str) -> Self:
        self._props["@ajax:success"] = value
        return self

    def ajax_error(self, value: str) -> Self:
        self._props["@ajax:error"] = value
        return self

    def ajax_sent(self, value: str) -> Self:
        self._props["@ajax:sent"] = value
        return self

    def ajax_missing(self, value: str) -> Self:
        self._props["@ajax:missing"] = value
        return self

    def ajax_merge(self, value: str) -> Self:
        self._props["@ajax:merge"] = value
        return self

    def ajax_merged(self, value: str) -> Self:
        self._props["@ajax:merged"] = value
        return self

    def ajax_after(self, value: str) -> Self:
        self._props["@ajax:after"] = value
        return self

    # ------------------------------------------------------------------
    # Prop helpers
    # ------------------------------------------------------------------

    def _get_prop(self, key: str, default: Any = None) -> Any:
        """Get a prop value, falling back to *default*."""
        return self._props.get(key, default)

    def _get_base_html_attrs(self) -> dict[str, Any]:
        """
        Collect id, ARIA, and Alpine attributes that have been set,
        suitable for splatting into an ``html.*`` call.
        """
        _STATIC_KEYS = (
            "id",
            "aria_label",
            "aria_hidden",
            "aria_expanded",
            "aria_controls",
            "aria_live",
            "aria_atomic",
            "aria_describedby",
            "role",
            "formnoajax",
        )
        attrs: dict[str, Any] = {}
        for k, v in self._props.items():
            if v is None:
                continue
            if k in _STATIC_KEYS or k.startswith(_ALPINE_PREFIXES):
                attrs[k] = v
        return attrs

    # ------------------------------------------------------------------
    # htmy integration
    # ------------------------------------------------------------------

    def htmy(self, context: HueContext, **kwargs: Any) -> Component:
        """Entry point called by the htmy renderer."""
        return self._render(context)

    @abstractmethod
    def _render(self, context: HueContext) -> Component:
        """Subclasses produce the concrete markup here."""
        ...
