"""
The search dialog: Pagefind's index, behind a combobox the docs draw themselves.

hue's Command filters items the server rendered, and these results arrive from
the index as the reader types, so the docs build their own list on the WAI-ARIA
combobox pattern: focus stays in the input, arrow keys move an active option
named by aria-activedescendant, Enter follows it.
"""

from __future__ import annotations

import json

from htmy import html as h
from hue import html
from hue.js import unsafe
from hue.types.core import ComponentType
from hue.ui import Dialog, Kbd

from hue_docs.icons import Icon
from hue_docs.shortcuts import Shortcuts
from hue_docs.site import url

_LISTBOX = "docs-search-results"
_SHORTCUTS = "docs-search-shortcuts"

_ROW = "flex w-full items-center gap-3 rounded-md px-3 py-2 text-start"


def _result_row() -> ComponentType:
    # One option per result, stamped out by x-for, which hue's template does
    # not have. The link is htmy too, for its tabindex: focus stays in the
    # input, and the option is reached through aria-activedescendant.
    option = (
        html.li(
            h.a(
                html.span()
                .class_("block truncate font-ui text-sm font-semibold text-fg")
                .x_text(unsafe("row.title")),
                html.span()
                .class_(
                    "block truncate text-2xs uppercase tracking-wide text-fg-subtle"
                )
                .x_text(unsafe("row.page"))
                .x_show(unsafe("row.page")),
                # Pagefind encodes the text before it adds <mark>, so the
                # excerpt is safe to set as markup.
                html.span()
                .class_("docs-excerpt mt-1 line-clamp-2 block text-xs text-fg-muted")
                .x_html(unsafe("row.excerpt")),
                **{
                    ":href": "row.url",
                    "tabindex": "-1",
                    "x-on:click": "follow($event, index)",
                },
                class_="block rounded-md px-3 py-2",
            )
        )
        .role("option")
        .class_("cursor-pointer rounded-md")
        .x_bind("id", unsafe("`docs-search-${index}`"))
        .x_bind("aria-selected", unsafe("String(index === active)"))
        .x_bind("class", unsafe("index === active ? 'bg-surface-active' : ''"))
        .x_on("mousemove", unsafe("active = index"))
    )
    return h.template(option, **{"x-for": "(row, index) in results", ":key": "row.url"})


def _option(control: ComponentType, index: int) -> ComponentType:
    # The same marker and pointer as a result row, which is what lets the
    # arrow keys run through the shortcuts while the box is empty.
    return (
        html.li(control)
        .role("option")
        .id(f"docs-shortcut-{index}")
        .class_("cursor-pointer rounded-md")
        .x_bind("aria-selected", unsafe(f"String(active === {index})"))
        .x_bind("class", unsafe(f"active === {index} ? 'bg-surface-active' : ''"))
        .x_on("mousemove", unsafe(f"active = {index}"))
    )


def _shortcut_list() -> ComponentType:
    """
    The site's shortcuts, listed while the box is empty. A row runs its
    shortcut the way the keys would: a link goes, an action closes the
    dialog first and then runs.
    """
    rows = []
    for index, shortcut in enumerate(Shortcuts.shortcuts):
        inner = (
            shortcut.icon or "",
            html.span(shortcut.label).class_("min-w-0 flex-1 truncate text-sm text-fg"),
            html.span(*[Kbd(*step) for step in shortcut.steps]).class_(
                "inline-flex flex-none gap-1"
            ),
        )
        href = shortcut.href
        # The docs' hrefs are URLs; one built per request would need the request.
        assert not callable(href)
        control = (
            h.a(*inner, href=href, tabindex="-1", class_=_ROW)
            if href is not None
            else h.button(
                *inner,
                type="button",
                tabindex="-1",
                class_=f"{_ROW} cursor-pointer",
                **{"x-on:click": f"open = false; {shortcut.action}"},
            )
        )
        rows.append(_option(control, index))
    return (
        html.ul(*rows)
        .id(_SHORTCUTS)
        .role("listbox")
        .aria_label("Shortcuts")
        .class_("p-2 [&_svg]:size-4 [&_svg]:flex-none [&_svg]:text-fg-subtle")
        .x_show(unsafe("!query.trim()"))
    )


def search_dialog() -> ComponentType:
    # htmy for the attributes a combobox needs that hue's input has no
    # modifier for: aria-autocomplete, aria-activedescendant, spellcheck.
    box = h.input_(
        type="search",
        placeholder="Search components and guides",
        autocomplete="off",
        spellcheck="false",
        # The dialog's trap focuses this after it notes where focus goes back
        # to on close.
        autofocus="",
        class_=(
            "h-11 min-w-0 flex-1 bg-transparent text-md text-fg outline-none "
            "placeholder:text-fg-subtle"
        ),
        **{
            "role": "combobox",
            "aria-label": "Search the docs",
            "aria-autocomplete": "list",
            ":aria-controls": f"query.trim() ? '{_LISTBOX}' : '{_SHORTCUTS}'",
            ":aria-expanded": "String(!query.trim() || results.length > 0)",
            ":aria-activedescendant": "active >= 0 ? optionId(active) : null",
            "x-model": "query",
            "x-on:input": "search()",
            "x-on:keydown.arrow-down.prevent": "move(1)",
            "x-on:keydown.arrow-up.prevent": "move(-1)",
            "x-on:keydown.enter.prevent": "go()",
        },
    )
    field = html.div(
        Icon("search").class_("size-4 flex-none text-fg-subtle"), box
    ).class_("flex items-center gap-3 border-b border-border px-4")
    listbox = (
        html.ul(_result_row())
        .id(_LISTBOX)
        .role("listbox")
        .aria_label("Results")
        .class_("max-h-[min(60vh,28rem)] overflow-y-auto p-2")
        .x_show(unsafe("results.length > 0"))
    )
    empty = (
        html.p()
        .class_("px-4 py-8 text-center text-sm text-fg-muted")
        .x_show(unsafe("searched && !results.length && query.trim()"))
        .x_text(unsafe('`Nothing matches "${query.trim()}".`'))
        .x_cloak()
    )
    footer = html.div(
        html.span(Kbd("up"), Kbd("down"), " to move").class_(
            "inline-flex items-center gap-1"
        ),
        html.span(Kbd("enter"), " to open").class_("inline-flex items-center gap-1"),
        html.span(Kbd("esc"), " to close").class_("inline-flex items-center gap-1"),
    ).class_(
        "flex gap-4 border-t border-border px-4 py-2 text-2xs text-fg-subtle "
        "max-sm:hidden"
    )
    return (
        Dialog()
        .title("Search the docs")
        .size("lg")
        .x_on("docs-search.window", unsafe("open = true"))
        .content(
            html.div(
                field,
                _shortcut_list(),
                listbox,
                empty,
                html.p().class_("sr-only").aria_live("polite").x_text(unsafe("status")),
                footer,
            )
            .class_("-mx-5 -mb-5 flex flex-col")
            .x_data(f"docsSearch({json.dumps(url('/'))})")
            # Reset when it opens, so the reader starts from an empty box.
            # -mx-5 -mb-5 and open lean on Dialog's body padding and its
            # state's name.
            .x_effect(unsafe("if (open) reset()"))
        )
    )
