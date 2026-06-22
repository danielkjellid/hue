from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, ClassVar, Literal

from htmy import Context
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component, ComponentType
from hue.types.html import AriaAtomic, AriaLive, AriaRole
from hue.utils import classnames


class ChainableComponent(ABC):
    """
    Base class for hue's chainable components.

    A subclass builds an HTML subtree declaratively: styling and attributes
    are set through modifier methods that each return ``self`` (so calls
    chain), children are passed positionally or via ``.content()``, and the
    concrete markup is produced by the subclass's ``_render`` method.

    This base provides the modifiers shared by every component — ``.class_()``,
    ``.id()``, the ARIA helpers, and the Alpine.js / Alpine AJAX directives.

    Example::

        Button()
            .variant("primary")
            .size("lg")
            .content(Text("Click me"))
    """

    #: Documentation category — the sidebar section a component is grouped under
    #: on the docs site. Override per component; the docs decide section order.
    category: ClassVar[str] = "Components"

    def __init__(self) -> None:
        self._props: dict[str, Any] = {}
        self._attrs: dict[str, Any] = {}
        self._children: tuple[ComponentType, ...] = ()
        self._skeleton_override: Component | Callable[[], Component] | None = None

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
        self._attrs["id"] = value
        return self

    def aria_label(self, value: str) -> Self:
        self._attrs["aria_label"] = value
        return self

    def aria_hidden(self, value: Literal["true", "false"]) -> Self:
        self._attrs["aria_hidden"] = value
        return self

    def aria_expanded(self, value: str) -> Self:
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
    # Alpine — core directives (available on all elements)
    # ------------------------------------------------------------------

    def x_data(self, value: dict[str, Any] | str) -> Self:
        """Declare an Alpine component scope."""
        self._attrs["x-data"] = value
        return self

    def x_init(self, value: str) -> Self:
        """Run an expression when the component initialises."""
        self._attrs["x-init"] = value
        return self

    def x_show(self, value: str) -> Self:
        """Toggle element visibility."""
        self._attrs["x-show"] = value
        return self

    def x_text(self, value: str) -> Self:
        """Set the element's text content."""
        self._attrs["x-text"] = value
        return self

    def x_html(self, value: str) -> Self:
        """Set the element's inner HTML."""
        self._attrs["x-html"] = value
        return self

    def x_ref(self, value: str) -> Self:
        """Register an element reference."""
        self._attrs["x-ref"] = value
        return self

    def x_effect(self, value: str) -> Self:
        """Run an expression reactively when dependencies change."""
        self._attrs["x-effect"] = value
        return self

    def x_cloak(self) -> Self:
        """Hide the element until Alpine initialises."""
        self._attrs["x-cloak"] = True
        return self

    def x_ignore(self) -> Self:
        """Prevent Alpine from initialising this element tree."""
        self._attrs["x-ignore"] = True
        return self

    def x_id(self, value: list[str]) -> Self:
        """Scope ``$id()`` calls to the given names."""
        self._attrs["x-id"] = value
        return self

    def x_on(self, event: str, expression: str) -> Self:
        """Listen for a browser event (``@<event>``)."""
        self._attrs[f"@{event}"] = expression
        return self

    def x_bind(self, attr: str, expression: str) -> Self:
        """Dynamically bind an HTML attribute (``:attr``)."""
        self._attrs[f":{attr}"] = expression
        return self

    # ------------------------------------------------------------------
    # Alpine — transitions (pair with x_show)
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
    # Alpine AJAX — target element attributes (any element with an id
    # can be an AJAX target)
    # ------------------------------------------------------------------

    def x_merge(
        self,
        value: Literal["before", "replace", "update", "prepend", "append", "after"],
    ) -> Self:
        """Set the merge strategy for incoming AJAX content."""
        self._attrs["x-merge"] = value
        return self

    def x_autofocus(self, value: bool = True) -> Self:
        """Focus this element after an AJAX update."""
        self._attrs["x-autofocus"] = value
        return self

    # ------------------------------------------------------------------
    # Alpine AJAX — event handlers (events bubble, so these can be
    # placed on any ancestor element)
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
        """Get a prop value, falling back to *default*."""
        return self._props.get(key, default)

    def _get_base_html_attrs(self) -> dict[str, Any]:
        """
        Collect id, ARIA, and Alpine attributes that have been set,
        suitable for splatting into an ``html.*`` call.
        """
        return {k: v for k, v in self._attrs.items() if v is not None}

    # ------------------------------------------------------------------
    # htmy integration
    # ------------------------------------------------------------------

    def htmy(self, context: Context, /) -> Component:
        """Entry point called by the htmy renderer."""
        return self._render(HueContext.from_context(context))

    @abstractmethod
    def _render(self, context: HueContext) -> Component:
        """Subclasses produce the concrete markup here."""
        ...

    # ------------------------------------------------------------------
    # Skeleton
    # ------------------------------------------------------------------

    def skeleton_as(self, value: Component | Callable[[], Component]) -> Self:
        """
        Override the loading placeholder for this instance.

        The escape hatch for content the per-class default can't predict — a
        comment body that should load as three lines, a list whose length is
        unknown. Pass a component, or a zero-arg factory to defer building it.
        Honored by to_skeleton ahead of any class default or container recursion.

            Text(comment.body).skeleton_as(Skeleton().lines(3))
        """
        self._skeleton_override = value
        return self

    def skeleton(self) -> Component:
        """
        Return this component's loading placeholder.

        Resolves an instance override set via skeleton_as first; otherwise
        delegates to _skeleton_impl. Components customise the placeholder by
        overriding _skeleton_impl, not this method, so the override always wins.
        """
        if self._skeleton_override is not None:
            override = self._skeleton_override
            return override() if callable(override) else override
        return self._skeleton_impl()

    def _skeleton_impl(self) -> Component:
        """
        The per-class default placeholder shape.

        The base default is a single line, which is why the skeleton mapper
        (to_skeleton) recurses through layout containers rather than trusting
        this fallback. Override it on a leaf component to give an accurate
        placeholder — a rect for a button, a circle for an avatar, and so on.
        """
        # Local import: the Skeleton atom subclasses this base, so a top-level
        # import here would be circular.
        from hue.ui.atoms.skeleton import Skeleton  # noqa: PLC0415

        return Skeleton()
