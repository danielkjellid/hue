"""
The docs site's own keyboard shortcuts.

Real ones, bound on every page through configure_hue in app.py, which gives
the search dialog its key and the Keyboard shortcuts guide a registry to show.
"""

from __future__ import annotations

from hue import toast
from hue.js import unsafe
from hue.shortcuts import Shortcut, ShortcutRegistry

from hue_docs_v2.icons import Icon
from hue_docs_v2.site import url


class Shortcuts(ShortcutRegistry):
    search = Shortcut(
        "Search the docs",
        "mod+k",
        # The search dialog listens for it, so the key and the palette's
        # entry open the same thing.
        action=unsafe("$dispatch('docs-search')"),
        group="Docs",
        icon=Icon("search"),
        keywords=("find",),
    )
    home = Shortcut(
        "Go to the introduction",
        "g",
        "h",
        href=url("/"),
        group="Docs",
        icon=Icon("house"),
    )
    guide = Shortcut(
        "Go to Keyboard shortcuts",
        "g",
        "k",
        href=url("/keyboard-shortcuts/"),
        group="Docs",
        icon=Icon("file-text"),
    )
    copy_link = Shortcut(
        "Copy link to this page",
        "alt+c",
        action=unsafe(
            "navigator.clipboard.writeText(location.href); "
            + toast.js.success("Link copied")
        ),
        icon=Icon("copy"),
        keywords=("share", "url"),
    )
