"""
The docs site's own keyboard shortcuts.

Real ones, put in the render context by render.py and so bound on every
page, which gives the Command and DropdownMenu showcases and the Keyboard
shortcuts guide a registry to show, with keys that work.
"""

from __future__ import annotations

from hue import toast
from hue.js import unsafe
from hue.shortcuts import Shortcut, ShortcutRegistry
from hue.ui.atoms.icon import HueIcon

from hue_docs.site import url


class Shortcuts(ShortcutRegistry):
    home = Shortcut(
        "Go to the introduction",
        "g",
        "h",
        href=url("/"),
        group="Docs",
        icon=HueIcon("house"),
    )
    guide = Shortcut(
        "Go to Keyboard shortcuts",
        "g",
        "k",
        href=url("/keyboard-shortcuts/"),
        group="Docs",
        icon=HueIcon("file-text"),
    )
    command = Shortcut(
        "Go to Command",
        "g",
        "c",
        href=url("/components/command/"),
        group="Docs",
        icon=HueIcon("file-text"),
    )
    copy_link = Shortcut(
        "Copy link to this page",
        "alt+c",
        action=unsafe(
            "navigator.clipboard.writeText(location.href); "
            + toast.js.success("Link copied")
        ),
        icon=HueIcon("copy"),
        keywords=("share", "url"),
    )
