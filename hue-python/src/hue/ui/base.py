from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar, Literal

from htmy import Context
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component, ComponentType
from hue.types.html import AriaAtomic, AriaLive, AriaRole
from hue.utils import classnames

type AlpinePlacement = Literal[
    "top",
    "top-start",
    "top-end",
    "right",
    "right-start",
    "right-end",
    "bottom",
    "bottom-start",
    "bottom-end",
    "left",
    "left-start",
    "left-end",
]


class ChainableComponent(ABC):
    """
    Base class for hue's chainable components.

    A subclass builds an HTML subtree declaratively: styling and attributes are
    set through modifier methods that each return self so calls chain, children
    are passed positionally or via content(), and the concrete markup is produced
    by the subclass's _render method.

    This base provides the modifiers shared by every component: class_(), id(),
    the ARIA helpers, and the Alpine.js and Alpine AJAX directives.

        Button().variant("primary").size("lg").content(Text("Click me"))
    """

    # The docs sidebar section a component is grouped under. None marks a
    # composition-only part (a table row, say) that is exported for building
    # with but has no standalone docs page.
    category: ClassVar[str | None] = "Components"

    def __init__(self) -> None:
        self._props: dict[str, Any] = {}
        self._attrs: dict[str, Any] = {}
        self._children: tuple[ComponentType, ...] = ()

    # ------------------------------------------------------------------
    # Children
    # ------------------------------------------------------------------

    def content(self, *children: ComponentType) -> Self:
        """
        Set the component's children.
        """
        self._children = children
        return self

    # ------------------------------------------------------------------
    # Shared modifiers (class, id, ARIA)
    # ------------------------------------------------------------------

    def class_(self, value: str) -> Self:
        """
        Append CSS classes.
        """
        self._props["class_"] = classnames(self._props.get("class_"), value)
        return self

    def id(self, value: str) -> Self:
        self._attrs["id"] = value
        return self

    def aria_label(self, value: str) -> Self:
        self._attrs["aria_label"] = value
        return self

    def aria_hidden(self, value: Literal["true", "false"]) -> Self:
        self._attrs["aria_hidden"] = value
        return self

    def aria_expanded(self, value: Literal["true", "false"]) -> Self:
        self._attrs["aria_expanded"] = value
        return self

    def aria_controls(self, value: str) -> Self:
        self._attrs["aria_controls"] = value
        return self

    def aria_live(self, value: AriaLive) -> Self:
        self._attrs["aria_live"] = value
        return self

    def aria_atomic(self, value: AriaAtomic) -> Self:
        self._attrs["aria_atomic"] = value
        return self

    def aria_describedby(self, value: str) -> Self:
        self._attrs["aria_describedby"] = value
        return self

    def role(self, value: AriaRole) -> Self:
        self._attrs["role"] = value
        return self

    # ------------------------------------------------------------------
    # Alpine core directives (available on all elements)
    # ------------------------------------------------------------------

    def x_data(self, value: dict[str, Any] | str) -> Self:
        """
        Declare an Alpine component scope.
        """
        self._attrs["x-data"] = value
        return self

    def x_init(self, value: str) -> Self:
        """
        Run an expression when the component initialises.
        """
        self._attrs["x-init"] = value
        return self

    def x_show(self, value: str) -> Self:
        """
        Toggle element visibility.
        """
        self._attrs["x-show"] = value
        return self

    def x_text(self, value: str) -> Self:
        """
        Set the element's text content.
        """
        self._attrs["x-text"] = value
        return self

    def x_html(self, value: str) -> Self:
        """
        Set the element's inner HTML.
        """
        self._attrs["x-html"] = value
        return self

    def x_ref(self, value: str) -> Self:
        """
        Register an element reference.
        """
        self._attrs["x-ref"] = value
        return self

    def x_effect(self, value: str) -> Self:
        """
        Run an expression reactively when its dependencies change.
        """
        self._attrs["x-effect"] = value
        return self

    def x_cloak(self) -> Self:
        """
        Hide the element until Alpine initialises.
        """
        self._attrs["x-cloak"] = True
        return self

    def x_ignore(self) -> Self:
        """
        Prevent Alpine from initialising this element tree.
        """
        self._attrs["x-ignore"] = True
        return self

    def x_id(self, value: list[str]) -> Self:
        """
        Scope $id() calls to the given names.
        """
        self._attrs["x-id"] = value
        return self

    def x_on(self, event: str, expression: str) -> Self:
        """
        Listen for a browser event (@event).
        """
        self._attrs[f"@{event}"] = expression
        return self

    def x_bind(self, attr: str, expression: str) -> Self:
        """
        Dynamically bind an HTML attribute (:attr).
        """
        self._attrs[f":{attr}"] = expression
        return self

    # ------------------------------------------------------------------
    # Alpine transitions (pair with x_show)
    # ------------------------------------------------------------------

    def x_transition_enter(self, value: str) -> Self:
        self._attrs["x-transition:enter"] = value
        return self

    def x_transition_enter_start(self, value: str) -> Self:
        self._attrs["x-transition:enter.start"] = value
        return self

    def x_transition_enter_end(self, value: str) -> Self:
        self._attrs["x-transition:enter.end"] = value
        return self

    def x_transition_leave(self, value: str) -> Self:
        self._attrs["x-transition:leave"] = value
        return self

    def x_transition_leave_start(self, value: str) -> Self:
        self._attrs["x-transition:leave.start"] = value
        return self

    def x_transition_leave_end(self, value: str) -> Self:
        self._attrs["x-transition:leave.end"] = value
        return self

    # ------------------------------------------------------------------
    # Alpine plugins (focus, anchor)
    # ------------------------------------------------------------------

    def x_trap(
        self,
        expression: str,
        *,
        inert: bool = False,
        noscroll: bool = False,
        noreturn: bool = False,
    ) -> Self:
        """
        Trap focus inside this element while the expression is truthy.

        Focus moves inside on open and returns to the previously focused
        element on close, so whatever sets the expression must also clear it.
        inert hides the rest of the page from assistive tech, noscroll locks
        background scrolling, and noreturn skips the focus restore.
        """
        modifiers = "".join(
            f".{name}"
            for name, enabled in (
                ("inert", inert),
                ("noscroll", noscroll),
                ("noreturn", noreturn),
            )
            if enabled
        )
        self._attrs[f"x-trap{modifiers}"] = expression
        return self

    def x_anchor(
        self,
        expression: str,
        placement: AlpinePlacement | None = None,
        *,
        offset: int | None = None,
    ) -> Self:
        """
        Position this element against another, given as a reference expression.

        The placement is a preference, not a promise: the plugin flips and
        shifts the panel to keep it inside the viewport.

            Popover().x_anchor("$refs.trigger", "bottom-start", offset=6)
        """
        key = "x-anchor"
        if placement is not None:
            key += f".{placement}"
        if offset is not None:
            key += f".offset.{offset}"
        self._attrs[key] = expression
        return self

    # ------------------------------------------------------------------
    # Alpine AJAX target attributes (any element with an id can be a target)
    # ------------------------------------------------------------------

    def x_merge(
        self,
        value: Literal["before", "replace", "update", "prepend", "append", "after"],
    ) -> Self:
        """
        Set the merge strategy for incoming AJAX content.
        """
        self._attrs["x-merge"] = value
        return self

    def x_autofocus(self, value: bool = True) -> Self:
        """
        Focus this element after an AJAX update.
        """
        # Boolean attributes are true by presence, so False must omit it.
        self._attrs["x-autofocus"] = value or None
        return self

    # ------------------------------------------------------------------
    # Alpine AJAX event handlers (events bubble, so these can sit on any
    # ancestor element)
    # ------------------------------------------------------------------

    def ajax_before(self, value: str) -> Self:
        self._attrs["@ajax:before"] = value
        return self

    def ajax_send(self, value: str) -> Self:
        self._attrs["@ajax:send"] = value
        return self

    def ajax_redirect(self, value: str) -> Self:
        self._attrs["@ajax:redirect"] = value
        return self

    def ajax_success(self, value: str) -> Self:
        self._attrs["@ajax:success"] = value
        return self

    def ajax_error(self, value: str) -> Self:
        self._attrs["@ajax:error"] = value
        return self

    def ajax_sent(self, value: str) -> Self:
        self._attrs["@ajax:sent"] = value
        return self

    def ajax_missing(self, value: str) -> Self:
        self._attrs["@ajax:missing"] = value
        return self

    def ajax_merge(self, value: str) -> Self:
        self._attrs["@ajax:merge"] = value
        return self

    def ajax_merged(self, value: str) -> Self:
        self._attrs["@ajax:merged"] = value
        return self

    def ajax_after(self, value: str) -> Self:
        self._attrs["@ajax:after"] = value
        return self

    # ------------------------------------------------------------------
    # Prop helpers
    # ------------------------------------------------------------------

    def _get_prop(self, key: str, default: Any = None) -> Any:
        """
        Get a prop value, falling back to default.
        """
        return self._props.get(key, default)

    def _get_base_html_attrs(self) -> dict[str, Any]:
        """
        Every attribute set through the modifiers above (id, ARIA, Alpine, and
        anything set via Element.attr), minus None values, ready to splat into an
        html.* call.
        """
        return {k: v for k, v in self._attrs.items() if v is not None}

    # ------------------------------------------------------------------
    # htmy integration
    # ------------------------------------------------------------------

    def htmy(self, context: Context, /) -> Component:
        """
        Entry point called by the htmy renderer.
        """
        return self._render(HueContext.from_context(context))

    @abstractmethod
    def _render(self, context: HueContext) -> Component:
        """
        Subclasses produce the concrete markup here.
        """
        ...


class AlpineModelMixin:
    """
    x-model for form controls. Mixed into the input, select, textarea and
    checkbox components rather than living on the base, since two-way binding
    only makes sense on elements that hold a value.
    """

    _attrs: dict[str, Any]  # provided by ChainableComponent

    def x_model(self, value: str) -> Self:
        """
        Two-way bind this control to Alpine data.
        """
        self._attrs["x-model"] = value
        return self
