"""
A registry for the tests, and a stand-in for a page made with it.
"""

from htmy import Context, Fragment

from hue.js import unsafe
from hue.shortcuts import Shortcut, ShortcutRegistry
from hue.types.core import ComponentType


class Shortcuts(ShortcutRegistry):
    billing = Shortcut("Go to Billing", "g", "b", href="/billing/", group="Navigate")
    duplicate = Shortcut("Duplicate", "mod+d", action=unsafe("duplicate()"))
    archive = Shortcut("Archive invoice", "e", scoped=True)


class OnPage:
    """
    Offers a registry to what is inside it, the way BasePage does.
    """

    def __init__(
        self, *children: ComponentType, registry: type[ShortcutRegistry] = Shortcuts
    ) -> None:
        self.children = children
        self.registry = registry

    def htmy_context(self) -> Context:
        return {ShortcutRegistry: self.registry}

    def htmy(self, context: Context) -> ComponentType:
        return Fragment(*self.children)
