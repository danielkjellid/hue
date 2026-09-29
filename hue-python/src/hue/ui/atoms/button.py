from __future__ import annotations

from typing import Literal

from htmy import Context, html
from typing_extensions import Self

from hue.types.core import Component, ComponentType
from hue.types.html import AriaHasPopup
from hue.ui._styles import FOCUS_RING
from hue.ui.base import Clickable, FormElementMixin
from hue.utils import classnames

type ButtonVariant = Literal[
    "primary",
    "secondary",
    "outline",
    "ghost",
    "link",
    "danger",
    "danger-outline",
]
type ButtonSize = Literal["xs", "sm", "md", "lg"]
type ButtonType = Literal["button", "submit", "reset"]

# Keyed by the Literal so mypy keeps the maps exhaustive when a value is added.
# Hover moves the background and never the foreground: dimming the label on
# hover drops contrast below the resting state, which is a WCAG failure and the
# single most common hover bug.
# Every variant names its own border colour, including the transparent one.
# Two border-color utilities on the same element resolve by stylesheet order
# rather than by the order they are written in, so a shared base
# `border-transparent` silently won over the outline variants' colours.
_VARIANT_CLASSES: dict[ButtonVariant, str] = {
    "primary": (
        "border-transparent bg-accent text-accent-fg "
        "hover:bg-accent-hover active:bg-accent-active"
    ),
    "secondary": (
        "border-transparent bg-fg text-canvas hover:bg-fg-muted active:bg-fg-subtle"
    ),
    "outline": (
        "bg-surface border-border-input text-fg shadow-field "
        "hover:bg-surface-hover hover:border-border-hover active:bg-surface-active"
    ),
    "ghost": (
        "border-transparent text-fg hover:bg-surface-hover active:bg-surface-active"
    ),
    "link": (
        "border-transparent text-accent-text underline underline-offset-[3px] "
        "decoration-current/35 hover:decoration-current"
    ),
    "danger": ("border-transparent bg-danger text-danger-fg hover:bg-danger-hover"),
    "danger-outline": (
        "bg-surface border-danger-border text-danger-text "
        "hover:bg-danger-subtle hover:border-danger"
    ),
}

_FONT_CLASSES: dict[ButtonSize, str] = {
    "xs": "text-xs",
    "sm": "text-sm",
    "md": "text-base",
    "lg": "text-md",
}

_GAP_CLASSES: dict[ButtonSize, str] = {
    "xs": "gap-1",
    "sm": "gap-2",
    "md": "gap-2",
    "lg": "gap-2",
}

_HEIGHT_CLASSES: dict[ButtonSize, str] = {
    "xs": "h-control-xs",
    "sm": "h-control-sm",
    "md": "h-control-md",
    "lg": "h-control-lg",
}

# Square, so an icon-only button lines up with the text buttons beside it.
_WIDTH_CLASSES: dict[ButtonSize, str] = {
    "xs": "w-control-xs",
    "sm": "w-control-sm",
    "md": "w-control-md",
    "lg": "w-control-lg",
}

_PADDING_CLASSES: dict[ButtonSize, str] = {
    "xs": "px-2",
    "sm": "px-2.5",
    "md": "px-3.5",
    "lg": "px-5",
}


class Button(FormElementMixin, Clickable):
    """
    A clickable button.

    variant() picks the role, size() the height, and pill() the corners.
    icon_only() makes it square and names it, fluid() fills the width, and
    loading() marks work in flight. Children become the button's content.

        Button().variant("primary").content(Icon("plus"), "New project")
    """

    category = "Actions"

    @classmethod
    def example(cls) -> Self:
        return cls().content("Button")

    def variant(self, value: ButtonVariant) -> Self:
        self._props["variant"] = value
        return self

    def size(self, value: ButtonSize) -> Self:
        self._props["size"] = value
        return self

    def pill(self, value: bool = True) -> Self:
        """
        Round the ends fully rather than the corners, for a button that
        floats over content rather than sitting in a row of fields.
        """
        self._props["pill"] = value
        return self

    def fluid(self, value: bool = True) -> Self:
        self._props["fluid"] = value
        return self

    def type(self, value: ButtonType) -> Self:
        self._props["type"] = value
        return self

    def disabled(self, value: bool = True) -> Self:
        self._props["disabled"] = value
        return self

    def formaction(self, value: str) -> Self:
        """
        Where this button submits its form to, in place of the form's own
        action, so one form can post to several places.
        """
        self._attrs["formaction"] = value
        return self

    def icon_only(self, label: str) -> Self:
        """
        Drop to a square button holding nothing but an icon.

        The label is required and becomes the accessible name, because an icon
        on its own has none - taking it as an argument is what makes the
        unlabelled version impossible to write rather than merely discouraged.
        """
        self._props["icon_only"] = True
        self._attrs["aria_label"] = label
        return self

    def loading(self, value: bool = True) -> Self:
        """
        Show a spinner and stop the button being pressed again.

        The button keeps its width and its label so neither the layout nor the
        accessible name shifts underneath the user; aria-busy announces the
        state instead.
        """
        self._props["loading"] = value
        return self

    def aria_haspopup(self, value: AriaHasPopup) -> Self:
        self._attrs["aria_haspopup"] = value
        return self

    def _box_classes(self, size: ButtonSize, *, link: bool, icon_only: bool) -> str:
        """
        Height and horizontal padding, which the layout modes disagree about.

        Kept out of the class list rather than overridden in it: two competing
        height utilities resolve by stylesheet order, not by the order they are
        written in, so the loser is whichever Tailwind happened to emit second.
        """
        if link:
            # A link button is text in a sentence; a control height would make
            # it sit oddly on the line.
            return "h-auto px-0"
        if icon_only:
            return classnames(_HEIGHT_CLASSES[size], _WIDTH_CLASSES[size])
        return classnames(_HEIGHT_CLASSES[size], _PADDING_CLASSES[size])

    def _render(self, context: Context) -> Component:
        variant: ButtonVariant = self._get_prop("variant", "primary")
        size: ButtonSize = self._get_prop("size", "md")
        pill: bool = self._get_prop("pill", False)
        fluid: bool = self._get_prop("fluid", False)
        disabled: bool = self._get_prop("disabled", False)
        loading: bool = self._get_prop("loading", False)
        icon_only: bool = self._get_prop("icon_only", False)

        classes = classnames(
            "relative inline-flex items-center justify-center select-none",
            "cursor-pointer whitespace-nowrap border",
            "font-ui font-semibold leading-none transition-colors",
            "[&_svg]:size-4 [&_svg]:shrink-0",
            "disabled:pointer-events-none",
            FOCUS_RING,
            "rounded-full" if pill else "rounded-md",
            _FONT_CLASSES[size],
            _GAP_CLASSES[size],
            _VARIANT_CLASSES[variant],
            self._box_classes(size, link=variant == "link", icon_only=icon_only),
            "w-full" if fluid and not icon_only else "",
            # A loading button is disabled to stop a second submit, but it
            # should not also look greyed out - the spinner already says why it
            # cannot be pressed.
            "disabled:opacity-45" if not loading else "",
            self._get_prop("class_"),
        )

        children: tuple[ComponentType, ...] = self._children
        if loading:
            children = (
                # Still rendered, so both the button's width and its accessible
                # name hold steady. opacity rather than visibility, because
                # visibility:hidden would drop the label out of the a11y tree
                # and leave a screen reader with an unnamed busy button.
                html.span(
                    *self._children,
                    class_=classnames(
                        "inline-flex items-center opacity-0", _GAP_CLASSES[size]
                    ),
                ),
                html.span(
                    class_=classnames(
                        "absolute size-4 rounded-full border-2 border-current",
                        "border-t-transparent animate-spinner",
                    ),
                    aria_hidden="true",
                ),
            )

        return html.button(
            *children,
            class_=classes,
            # A stable hook for the variant, since the classes that express it
            # are indistinguishable from any other. A surface that needs to
            # restyle the quiet buttons on it - an alert tinting its ghosts -
            # has nothing else to select on.
            data_variant=variant,
            type=self._get_prop("type", "button"),
            # Boolean attributes are true by presence, so False must omit it.
            disabled=disabled or loading or None,
            aria_busy="true" if loading else None,
            **self._get_base_html_attrs(),
        )
