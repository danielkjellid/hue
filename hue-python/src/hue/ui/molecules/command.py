from __future__ import annotations

from typing import ClassVar

from htmy import Context, html
from typing_extensions import Self

from hue.js import Expression, call, expect
from hue.types.core import Component, ComponentType
from hue.ui.atoms.button import Button
from hue.ui.atoms.icon import HueIcon
from hue.ui.atoms.kbd import Kbd
from hue.ui.base import ChainableComponent
from hue.ui.molecules import _overlay
from hue.ui.molecules.select import _GROUP_LABEL
from hue.utils import classnames, render_if

_PANEL = (
    "flex w-[min(560px,calc(100vw-2rem))] flex-col overflow-hidden rounded-xl "
    "border border-border bg-surface-raised shadow-overlay "
    "animate-dialog-in group-[.leaving]:animate-dialog-out"
)

# Active and hovered are one state: the pointer moves the marker the arrow
# keys move, so there is only ever one lit row to read.
_ITEM = (
    "flex w-full cursor-pointer select-none items-center gap-3 rounded-md "
    "px-[9px] py-2 text-base text-fg no-underline "
    "[&>svg]:size-4 [&>svg]:flex-none [&>svg]:text-fg-subtle "
    "data-active:bg-accent-subtle data-active:text-accent-text "
    "data-active:[&>svg]:text-accent-text "
    "aria-disabled:cursor-not-allowed aria-disabled:text-fg-disabled "
    "aria-disabled:data-active:bg-transparent"
)


class Command(ChainableComponent):
    """
    A command palette: a search field over a list of things to go to or do,
    opened from anywhere with a keyboard shortcut.

    The field keeps focus while the arrow keys move through the matching
    items and Enter runs one. hotkey() takes keys the way Kbd does, so
    hotkey("mod", "k") is Command-K on a Mac and Control-K elsewhere, and
    trigger() adds a control that opens it as well. Items are CommandItem,
    optionally in a CommandGroup.
    """

    category = "Overlays"

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .hotkey("mod", "k")
            .trigger(Button().variant("outline").content("Open command palette"))
            .content(
                CommandGroup()
                .label("Navigate")
                .content(
                    CommandItem().label("Go to Billing").href("#billing"),
                    CommandItem().label("Go to Members").href("#members"),
                ),
                CommandGroup()
                .label("Actions")
                .content(
                    CommandItem().label("Create invoice"),
                    CommandItem().label("Invite teammate"),
                ),
            )
        )

    def placeholder(self, value: str) -> Self:
        self._props["placeholder"] = value
        return self

    def label(self, value: str) -> Self:
        """
        What the palette is called to a screen reader, "Command palette"
        unless told otherwise.
        """
        self._props["label"] = value
        return self

    def hotkey(self, *keys: str) -> Self:
        """
        The keys that open it from anywhere on the page, named as Kbd names
        them: "mod" is Command on Apple platforms and Control elsewhere.
        """
        self._props["hotkey"] = keys
        return self

    def empty_message(self, value: str) -> Self:
        """
        What the list says when nothing matches what was typed.
        """
        self._props["empty_message"] = value
        return self

    def trigger(self, value: ChainableComponent) -> Self:
        """
        A control that opens it, besides the hotkey.
        """
        self._props["trigger"] = value
        return self

    def open(self, value: bool = True) -> Self:
        """
        Start it open.
        """
        self._props["open"] = value
        return self

    def _render(self, context: Context) -> Component:
        label: str = self._get_prop("label", "Command palette")
        hotkey: tuple[str, ...] = self._get_prop("hotkey", ())
        trigger: ChainableComponent | None = self._get_prop("trigger")
        if trigger is not None:
            _overlay.open_on_click(trigger)

        search = html.div(
            HueIcon("search").class_("size-4 flex-none text-fg-subtle"),
            html.input_(
                type="text",
                role="combobox",
                autocomplete="off",
                autofocus=True,
                aria_label=label,
                aria_autocomplete="list",
                aria_expanded="true",
                placeholder=self._get_prop("placeholder", "Type a command or search…"),
                class_=(
                    "min-w-0 flex-1 border-none bg-transparent font-body text-md "
                    "text-fg outline-none placeholder:text-fg-subtle"
                ),
                **{
                    "x-ref": "input",
                    "x-model": "query",
                    ":aria-activedescendant": "active",
                    "x-on:input": "search()",
                    "x-on:keydown": "key($event)",
                },
            ),
            Kbd("esc").class_("max-sm:hidden"),
            class_="flex h-13 flex-none items-center gap-3 border-b border-border px-4",
        )
        listbox = html.div(
            *self._children,
            role="listbox",
            aria_label=label,
            class_="flex max-h-[min(340px,55vh)] flex-col overflow-y-auto p-2",
            **{"x-ref": "listbox"},
        )
        # The words sit in a region that is always on the page and empty while
        # something matches, since a live region only speaks when its text
        # changes. The icon is shown with them and is not part of what is said.
        status = html.div(
            HueIcon("search").class_("mx-auto mb-2 size-6 text-fg-disabled"),
            html.p(role="status", **{"x-text": "empty ? emptyMessage : ''"}),
            class_="px-2 py-7 text-center text-base text-fg-subtle",
            **{"x-show": "empty"},
        )
        hints = html.div(
            html.span(Kbd("up"), Kbd("down"), " navigate", class_=_HINT),
            html.span(Kbd("enter"), " select", class_=_HINT),
            html.span(Kbd("esc"), " close", class_=_HINT),
            class_=(
                "flex flex-none items-center justify-between gap-4 border-t "
                "border-border bg-surface-sunken px-4 py-[9px] text-xs "
                "text-fg-subtle max-sm:hidden"
            ),
        )
        panel = html.div(
            search,
            listbox,
            status,
            hints,
            role="dialog",
            aria_modal="true",
            aria_label=label,
            class_=_PANEL,
            **{"x-trap.inert.noscroll": "open"},
        )
        return html.div(
            render_if(trigger, lambda control: control),
            html.div(
                panel,
                # High on the page rather than centred, so the list grows down
                # from a field that stays where it opened.
                class_=classnames(
                    _overlay.SCRIM, "items-start justify-center px-4 pt-[14vh]"
                ),
                **{
                    "x-show": "open",
                    "x-cloak": True,
                    "x-transition:enter": "transition-opacity duration-[180ms]",
                    "x-transition:enter-start": "opacity-0",
                    "x-transition:leave": _overlay.LEAVING,
                    "x-transition:leave-end": "opacity-0",
                    "x-on:click.self": "close()",
                },
            ),
            class_=self._get_prop("class_"),
            **{
                "x-data": call(
                    "hueCommand",
                    self._get_prop("open", False),
                    [key.lower() for key in hotkey],
                    self._get_prop("empty_message", "No matching commands."),
                ),
                "x-on:keydown.window": "hotkey($event)",
                "x-on:keydown.escape.window": "close()",
                **self._get_base_html_attrs(),
            },
        )


_HINT = "inline-flex items-center gap-1"


class CommandGroup(ChainableComponent):
    """
    A labelled run of items inside a Command. Hidden while nothing in it
    matches what was typed.
    """

    category: ClassVar[str | None] = None

    def label(self, value: str) -> Self:
        self._props["label"] = value
        return self

    def _render(self, context: Context) -> Component:
        return html.div(
            html.div(
                self._get_prop("label", ""),
                class_=_GROUP_LABEL,
                **{":id": "$id('hue-command-group')"},
            ),
            *self._children,
            role="group",
            class_="flex flex-col [&+&]:mt-2",
            **{
                "x-id": "['hue-command-group']",
                ":aria-labelledby": "$id('hue-command-group')",
                **self._get_base_html_attrs(),
            },
        )


class CommandItem(ChainableComponent):
    """
    One thing a Command can do: go somewhere with href(), or run an Alpine
    expression with action(). keywords() are searched as well as the label,
    for an item people look for by another name.
    """

    category: ClassVar[str | None] = None

    def label(self, value: str) -> Self:
        self._props["label"] = value
        return self

    def icon(self, value: ComponentType) -> Self:
        self._props["icon"] = value
        return self

    def description(self, value: str) -> Self:
        """
        A line under the label, for what the label alone does not say.
        """
        self._props["description"] = value
        return self

    def meta(self, value: str) -> Self:
        """
        A short note at the end of the row, such as an amount or a date.
        """
        self._props["meta"] = value
        return self

    def href(self, value: str) -> Self:
        """
        Where it goes. Drawn as a link, so it can be opened in a new tab too.
        """
        self._props["href"] = value
        return self

    def action(self, value: Expression) -> Self:
        """
        What it runs, as an Alpine expression. The palette closes first.
        """
        self._props["action"] = expect(value, modifier="action()")
        return self

    def keywords(self, *values: str) -> Self:
        self._props["keywords"] = values
        return self

    def disabled(self, value: bool = True) -> Self:
        self._props["disabled"] = value
        return self

    def _render(self, context: Context) -> Component:
        label: str = self._get_prop("label", "")
        href: str | None = self._get_prop("href")
        action: Expression | None = self._get_prop("action")
        disabled: bool = self._get_prop("disabled", False)
        keywords: tuple[str, ...] = self._get_prop("keywords", ())

        attrs: dict[str, object] = {
            "role": "option",
            "aria_selected": "false",
            # Never focused, links included: focus stays in the search field
            # and the marker shows where Enter goes.
            "tabindex": "-1",
            "aria_disabled": "true" if disabled else None,
            "class_": classnames(_ITEM, self._get_prop("class_")),
            "data-label": label,
            "data-keywords": " ".join(keywords) or None,
            # The active item is the selected one, as the combobox pattern has
            # it: aria-selected follows the marker, not a choice.
            ":aria-selected": "$el.id === active",
            ":data-active": "$el.id === active || null",
            "x-on:mousemove": "activate($el)",
            "x-on:click": "run($el, $event)",
            # How run() reaches the expression: it dispatches this event on the
            # item, so Alpine evaluates the action in the item's own scope.
            **({"x-on:command.stop": action} if action else {}),
            **self._get_base_html_attrs(),
        }
        children = (
            render_if(self._get_prop("icon"), lambda icon: icon),
            html.span(
                html.span(label, class_="block truncate"),
                render_if(
                    self._get_prop("description"),
                    lambda text: html.span(
                        text,
                        class_="block truncate text-sm text-fg-muted "
                        "in-data-active:text-accent-text/80",
                    ),
                ),
                class_="min-w-0 flex-1",
            ),
            render_if(
                self._get_prop("meta"),
                lambda text: html.span(text, class_="ms-auto text-2xs text-fg-subtle"),
            ),
        )
        if href is not None and not disabled:
            return html.a(*children, href=href, **attrs)
        return html.div(*children, **attrs)
