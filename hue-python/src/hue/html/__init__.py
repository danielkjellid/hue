"""
Chainable HTML elements — a drop-in companion to ``htmy.html``.

Every HTML tag available in htmy is accessible as a factory function on this
module via ``__getattr__``.  Calling the factory returns a chainable
:class:`~hue.html.element.Element` (or a specialized subclass for tags like
``form``, ``a``, ``img``, etc.)::

    from hue import html

    html.div()
        .class_("container")
        .content(
            html.p("Hello world"),
        )

    html.form()
        .method("POST")
        .action("/login/")
        .content(...)

For raw htmy tags (non-chainable) import ``htmy.html`` directly.
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

    # Typed factories so editors/type-checkers resolve the correct subclass.
    def form() -> FormElement: ...
    def a() -> AnchorElement: ...
    def img() -> ImgElement: ...
    def button() -> ButtonElement: ...
    def input_() -> InputElement: ...
    def select() -> SelectElement: ...
    def textarea() -> TextareaElement: ...
    def label() -> LabelElement: ...

__all__ = ["Element"]

# Cache factories so repeated access (e.g. html.div, html.div) returns the
# same callable without repeated getattr lookups.
_factories: dict[str, Callable[..., Element]] = {}


def __getattr__(name: str) -> Callable[..., Element]:
    """Dynamically create chainable Element factories for any htmy tag."""
    if name in _factories:
        return _factories[name]

    tag_class: Any = getattr(_htmy_html, name, None)

    if tag_class is None or not (
        isinstance(tag_class, type) and issubclass(tag_class, (Tag, TagWithProps))
    ):
        raise AttributeError(f"module 'hue.html' has no attribute {name!r}")

    # Use a specialized Element subclass when available
    element_class = SPECIALIZED_ELEMENTS.get(name, Element)

    def _factory() -> Element:
        return element_class(tag_class)

    _factory.__name__ = name
    _factory.__qualname__ = f"html.{name}"
    _factories[name] = _factory
    return _factory
