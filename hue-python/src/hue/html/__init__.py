"""
Chainable HTML elements, a drop-in companion to htmy.html.

Every HTML tag htmy knows is available as a factory on this module, returning a
chainable Element (or a specialised subclass for tags such as form, a and img):

    from hue import html

    html.form().method("POST").action("/login/").content(
        html.a("Click me").href("/about").target("_blank"),
    )

Positional arguments are children, like htmy.html, so the simple case reads
naturally. Void elements (input, br, img, ...) raise if given children.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from htmy import html as _htmy_html
from htmy.core import Tag, TagWithProps

from hue.html.element import SPECIALIZED_ELEMENTS, Element

if TYPE_CHECKING:
    from collections.abc import Callable

    from hue.html.element import (
        AnchorElement,
        ButtonElement,
        FormElement,
        ImgElement,
        InputElement,
        LabelElement,
        SelectElement,
        TextareaElement,
    )
    from hue.types.core import ComponentType

    # Typed factories so editors and type-checkers resolve the specialised class.
    def form(*children: ComponentType) -> FormElement: ...
    def a(*children: ComponentType) -> AnchorElement: ...
    def img(*children: ComponentType) -> ImgElement: ...
    def button(*children: ComponentType) -> ButtonElement: ...
    def input_(*children: ComponentType) -> InputElement: ...
    def select(*children: ComponentType) -> SelectElement: ...
    def textarea(*children: ComponentType) -> TextareaElement: ...
    def label(*children: ComponentType) -> LabelElement: ...


__all__ = ["Element"]

# Factories are cached so repeated html.div lookups return the same callable.
_factories: dict[str, Callable[..., Element]] = {}


def __getattr__(name: str) -> Callable[..., Element]:
    if name in _factories:
        return _factories[name]

    tag_class: Any = getattr(_htmy_html, name, None)

    if not (isinstance(tag_class, type) and issubclass(tag_class, (Tag, TagWithProps))):
        raise AttributeError(f"module 'hue.html' has no attribute {name!r}")

    element_class = SPECIALIZED_ELEMENTS.get(name, Element)

    def _factory(*children: Any) -> Element:
        element = element_class(tag_class)
        if children:
            element.content(*children)
        return element

    _factory.__name__ = name
    _factory.__qualname__ = f"html.{name}"
    _factories[name] = _factory
    return _factory
