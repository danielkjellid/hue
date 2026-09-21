from __future__ import annotations

from dataclasses import dataclass

from htmy import Context

__all__ = ["CurrentPage"]


@dataclass(frozen=True, slots=True)
class CurrentPage:
    """
    The page a set of links was told it is on, offered to all of them.

    A link reads it and marks itself rather than being marked from above,
    which is the difference between a component that knows a thing and a
    component that was reached into - and the only way a link built
    inside somebody else's component hears about it at all.

    Shared by Sidebar and Tabs, which are the same question asked twice:
    of these links, which one leads here?
    """

    path: str | None

    def marks(self, href: str | None, *, exact: bool = False) -> bool:
        """
        Whether a link to href is the page you are on.

        A section is still where you are when you are inside it, so
        /events marks /events/2050 as well as itself - the row you
        followed to get here should not go dark when you arrive. The
        root is everybody's prefix, so it marks only itself; exact says
        the same about a link whose own subpaths have links of their own.
        """
        if href is None or self.path is None:
            return False
        # Compared without their trailing slashes, because whether a URL
        # has one is a routing convention and not a different page.
        here = self.path.rstrip("/") or "/"
        to = href.rstrip("/") or "/"
        if to == here:
            return True
        if exact or to == "/":
            return False
        return here.startswith(f"{to}/")

    @classmethod
    def from_context(cls, context: Context) -> CurrentPage:
        found = context.get(cls)
        return found if isinstance(found, cls) else cls(None)
