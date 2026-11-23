from __future__ import annotations

from typing import ClassVar

from htmy import Context

from hue.base import ChainableComponent
from hue.types.core import ComponentType
from hue.utils import classnames


class Part(ChainableComponent):
    """
    One element of a widget built from a root and its parts.

    The root offers a frozen state object through htmy_context, and each part
    asks for it with _state, which raises outside the root. A part draws its
    element with _wired, which is where the caller's attributes and the part's
    own meet. Its classes are default_class, empty here and filled in by a
    styled subclass, followed by whatever class_() added.
    """

    category: ClassVar[str | None] = None

    default_class: ClassVar[str] = ""

    def _state[State](self, context: Context, state: type[State]) -> State:
        """
        The state the root around this part offers. Ids are built from it, so
        a part with no root has nothing to be wired to.
        """
        found = context.get(state)
        if isinstance(found, state):
            return found
        raise ValueError(
            f"{type(self).__name__} is one part of a widget and only means "
            f"something inside the root that offers it a {state.__name__}."
        )

    def _content(self) -> tuple[ComponentType, ...]:
        """
        What the element holds. A subclass that draws more than the children
        it was given says so here.
        """
        return self._children

    def _wired(self, **wiring: object) -> dict[str, object]:
        """
        The caller's attributes with the part's wiring on top, so a caller can
        add to a part and never unwire it.

        Wiring spells its listeners and bindings x-on: and x-bind:. The public
        modifiers write @ and :, so a caller's handler lands beside the part's
        rather than in its place.
        """
        merged = {
            **self._get_base_html_attrs(),
            **wiring,
            "class_": classnames(self.default_class, self._get_prop("class_")) or None,
        }
        return {key: value for key, value in merged.items() if value is not None}
