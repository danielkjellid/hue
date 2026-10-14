from __future__ import annotations

from dataclasses import dataclass

from htmy import Context
from typing_extensions import Self

from hue.ui.base import ChainableComponent

__all__ = ["SYNC", "CurrentPage", "SwapsTarget", "swap"]

#: An element Alpine AJAX refreshes from any response that carries it, and
#: leaves alone when one does not. Its id is how a response is matched to it.
SYNC = {"x-sync": ""}


def swap(target: str | None) -> dict[str, str]:
    """
    The attributes on a link or form that swaps target for what it leads to,
    or none, which leaves it a plain navigation.

    push, so the place it leads is in the address bar, to reload, to send to
    somebody and to come back to.
    """
    return {"x-target.push": target} if target else {}


class SwapsTarget(ChainableComponent):
    """
    A component whose links swap a region of the page rather than load a new
    one, such as Tabs or Pagination.

    It sits outside the region it swaps, so it keeps itself current with
    SYNC: a response that carries it refreshes it, which moves the mark to
    the link you followed, and one that does not leaves it alone. That needs
    an id, so a target() without one is refused.
    """

    def target(self, value: str) -> Self:
        """
        The id of the element a link's page lands in. Without one, every link
        is a plain navigation.
        """
        self._props["target"] = value
        return self

    def _swap_attrs(self) -> dict[str, str]:
        """
        What each of its links carries.
        """
        return swap(self._get_prop("target"))

    def _sync_attrs(self) -> dict[str, str]:
        """
        What its root carries.
        """
        if self._get_prop("target") is None:
            return {}
        if "id" not in self._attrs:
            raise ValueError(
                f"{type(self).__name__} with a target() needs an id() of its "
                "own, which is how a response that carries it refreshes it."
            )
        return SYNC


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
