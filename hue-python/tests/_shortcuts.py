"""
A registry for the tests to put in the render context.
"""

from hue.js import unsafe
from hue.shortcuts import Shortcut, ShortcutRegistry


class Shortcuts(ShortcutRegistry):
    billing = Shortcut("Go to Billing", "g", "b", href="/billing/", group="Navigate")
    duplicate = Shortcut("Duplicate", "mod+d", action=unsafe("duplicate()"))
    archive = Shortcut("Archive invoice", "e", scoped=True)
