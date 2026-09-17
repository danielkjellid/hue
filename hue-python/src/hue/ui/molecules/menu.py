from __future__ import annotations

from typing import Literal

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component, ComponentType
from hue.ui._styles import FOCUS_RING_INSET
from hue.ui.atoms.button import Button
from hue.ui.atoms.icon import HueIcon
from hue.ui.base import ChainableComponent
from hue.utils import classes_if, classnames, render_if, render_when

type MenuPlacement = Literal["bottom-start", "bottom-end", "top-start", "top-end"]
type MenuItemVariant = Literal["default", "danger"]

# The same 6px the popover keeps off its trigger.
_OFFSET = 6

_ITEM = (
    "flex w-full cursor-pointer items-center gap-2 rounded-sm px-2 py-[7px] "
    "text-start font-body text-base no-underline "
    "[&_svg]:size-4 [&_svg]:flex-none "
    "aria-disabled:pointer-events-none aria-disabled:cursor-not-allowed "
    "aria-disabled:text-fg-disabled aria-disabled:[&_svg]:text-fg-disabled"
)

_VARIANTS: dict[MenuItemVariant, str] = {
    "default": (
        "text-fg hover:bg-surface-hover "
        "[&_svg]:text-fg-subtle [&:hover_svg]:text-fg-muted"
    ),
    # The only coloured thing in a menu, which is what makes it stand out
    # without a second signal. -text rather than -fg: -fg is what goes on top
    # of a danger fill, and there is no fill here.
    "danger": "text-danger-text hover:bg-danger-subtle [&_svg]:text-danger-text",
}


class DropdownMenu(ChainableComponent):
    """
    A list of actions hanging off a control.

    Arrow keys move between items and wrap, Home and End jump to the ends,
    Escape closes it and puts focus back on the trigger. label() names the
    menu for a screen reader. A list of links is navigation rather than a
    menu, and belongs in a plain list.
    """

    category = "Overlays"

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .label("Project actions")
            .trigger(Button().variant("outline").content("Project actions"))
            .content(
                MenuItem().icon(HueIcon("copy")).content("Duplicate"),
                MenuItem().icon(HueIcon("file-text")).content("Export as CSV"),
                MenuSeparator(),
                MenuItem()
                .variant("danger")
                .icon(HueIcon("trash-2"))
                .content("Delete project"),
            )
        )

    def label(self, value: str) -> Self:
        """
        What the menu is called. The trigger's own name is read first, so this
        is the group the items belong to rather than a repeat of it.
        """
        self._props["label"] = value
        return self

    def placement(self, value: MenuPlacement) -> Self:
        """
        Which corner of the trigger it hangs off. A preference rather than a
        promise: the menu flips and shifts to stay inside the viewport.
        """
        self._props["placement"] = value
        return self

    def trigger(self, value: ChainableComponent) -> Self:
        """
        The control that opens it.

        A hue component rather than any markup, because the menu wires the
        click, the expanded state and the anchor onto the control itself.
        """
        self._props["trigger"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        placement: MenuPlacement = self._get_prop("placement", "bottom-start")
        trigger: ChainableComponent | None = self._get_prop("trigger")

        if trigger is not None:
            (
                trigger.x_ref("trigger")
                .x_on("click", "open = !open")
                # Down opens it as well as clicking, which is how a menu
                # button is expected to behave from the keyboard.
                .x_on("keydown.down.prevent", "open = true")
                .x_bind("aria-expanded", "open")
            )
            trigger._attrs.setdefault("aria_haspopup", "menu")

        menu = html.div(
            *self._children,
            role="menu",
            aria_label=self._get_prop("label"),
            class_=classnames(
                "z-70 min-w-50 max-w-[calc(100vw-2rem)] rounded-lg border",
                "border-border bg-surface-raised p-1 shadow-raised",
            ),
            **{
                "x-show": "open",
                "x-cloak": True,
                "x-transition.opacity": "",
                # Focus lands on the first item when the menu opens, which is
                # what makes the arrow keys work without a roving tabindex.
                "x-effect": "open && $nextTick(() => $focus.first())",
                "x-on:keydown.down.prevent": "$focus.wrap().next()",
                "x-on:keydown.up.prevent": "$focus.wrap().previous()",
                "x-on:keydown.home.prevent": "$focus.first()",
                "x-on:keydown.end.prevent": "$focus.last()",
                f"x-anchor.{placement}.offset.{_OFFSET}": "$refs.trigger",
            },
        )

        return html.span(
            render_if(trigger, lambda control: control),
            menu,
            class_=classnames("inline-flex", self._get_prop("class_")),
            **{
                "x-data": "{ open: false, "
                "close() { this.open = false; this.$refs.trigger?.focus() } }",
                "x-on:keydown.escape.window": "if (open) close()",
                # Tab leaves the menu rather than walking it. The items are
                # out of the tab order, so the browser's own Tab already goes
                # to whatever follows the trigger - but only if the panel is
                # still there when it looks: closing in the same event pulls
                # the focused item out from under it and drops focus on the
                # body. On the wrapper, because the trigger holds focus too
                # and a keydown there never reaches the panel beside it.
                "x-on:keydown.tab": "$nextTick(() => open = false)",
                "x-on:click.outside": "open = false",
                **self._get_base_html_attrs(),
            },
        )


class MenuItem(ChainableComponent):
    """
    One action in a menu, rendered as a button or, given href, a link.

    Picking it closes the menu. A checkable item toggles instead and leaves
    the menu open, since the point of one is usually to set more than one.
    """

    category = None

    def icon(self, value: ComponentType) -> Self:
        self._props["icon"] = value
        return self

    def shortcut(self, value: ComponentType) -> Self:
        """
        The keystroke this item answers to, at the end of the row. Pass a Kbd,
        which gives each modifier a spoken name.
        """
        self._props["shortcut"] = value
        return self

    def variant(self, value: MenuItemVariant) -> Self:
        self._props["variant"] = value
        return self

    def href(self, value: str) -> Self:
        self._props["href"] = value
        return self

    def checkable(self, value: bool = True) -> Self:
        """
        Make it a switch rather than an action: a tick appears in the gutter
        and the item announces itself as checked or not.
        """
        self._props["checkable"] = value
        return self

    def checked(self, value: bool = True) -> Self:
        self._props["checked"] = value
        return self

    def disabled(self, value: bool = True) -> Self:
        """
        Dim it and take it out of reach, but leave it in the menu and in the
        tab order: an action that disappears when it cannot be used leaves
        nothing to explain why.
        """
        self._props["disabled"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        variant: MenuItemVariant = self._get_prop("variant", "default")
        checkable: bool = self._get_prop("checkable", False)
        checked: bool = self._get_prop("checked", False)
        disabled: bool = self._get_prop("disabled", False)
        href: str | None = self._get_prop("href")

        children = (
            render_if(self._get_prop("icon"), lambda icon: icon),
            render_when(
                checkable,
                html.span(
                    aria_hidden="true",
                    class_="checkmark absolute start-[9px] top-1/2 -mt-[5px] "
                    "size-[10px] bg-accent-text",
                    **{"x-show": "checked"},
                ),
            ),
            *self._children,
            render_if(
                self._get_prop("shortcut"),
                lambda keys: html.span(keys, class_="ms-auto inline-flex gap-[3px]"),
            ),
        )

        attrs: dict[str, object] = {
            "role": "menuitemcheckbox" if checkable else "menuitem",
            # Out of the tab order, because a menu is walked with the arrow
            # keys: focus is moved here rather than tabbed to, and Tab means
            # "leave", which the browser then does for us. Roving focus is
            # what the menu role tells a screen reader to expect.
            "tabindex": "-1",
            # Hovering moves focus, so the pointer and the arrow keys share
            # one active item instead of lighting two rows at once. The ring
            # is focus-visible, so it stays out of the way until the keyboard
            # asks for it. preventScroll, because a menu that jumps under the
            # pointer is a menu you cannot aim at.
            "x-on:mouseenter": "$el.focus({ preventScroll: true })",
            "aria_disabled": "true" if disabled else None,
            "class_": classnames(
                _ITEM,
                _VARIANTS[variant],
                FOCUS_RING_INSET,
                # The gutter the tick sits in, so the labels of a group of
                # checkable items line up whether or not they are ticked.
                classes_if(checkable, ["relative", "ps-7"]),
            ),
            # Its own state, so the tick answers the click without a round
            # trip; x_model or an AJAX action can take it over.
            **(
                {
                    "x-data": f"{{ checked: {str(checked).lower()} }}",
                    ":aria-checked": "checked",
                    "x-on:click": "checked = !checked",
                }
                if checkable
                else {"x-on:click": "close()"}
            ),
            **self._get_base_html_attrs(),
        }

        if href is not None:
            return html.a(*children, href=href, **attrs)
        return html.button(*children, type="button", **attrs)


class MenuLabel(ChainableComponent):
    """
    A heading over a run of items.
    """

    category = None

    def _render(self, context: HueContext) -> Component:
        return html.div(
            *self._children,
            class_=classnames(
                "px-2 pt-[7px] pb-[5px] font-ui text-2xs font-bold uppercase",
                "tracking-[0.04em] text-fg-subtle",
                self._get_prop("class_"),
            ),
            **self._get_base_html_attrs(),
        )


class MenuSeparator(ChainableComponent):
    """
    A rule between two runs of items.
    """

    category = None

    def _render(self, context: HueContext) -> Component:
        return html.hr(
            class_=classnames(
                "my-1 h-px border-0 bg-border",
                self._get_prop("class_"),
            ),
            **self._get_base_html_attrs(),
        )
