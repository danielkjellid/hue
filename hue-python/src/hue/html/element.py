from __future__ import annotations

from typing import Any, Literal

from htmy.core import Tag, TagWithProps
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component
from hue.ui.base import ChainableComponent


class Element(ChainableComponent):
    """
    A chainable wrapper around any htmy ``Tag``.

    Provides the same modifier methods as other v2 components (``.class_()``,
    ``.id()``, ARIA helpers) plus a generic ``.attr()`` for arbitrary HTML
    attributes.

    Not typically instantiated directly — use the ``hue.html`` module::

        from hue import html

        html.div()
            .class_("container")
            .content(
                html.span("Hello"),
            )
    """

    def __init__(self, tag_class: type[Tag] | type[TagWithProps]) -> None:
        super().__init__()
        self._tag_class = tag_class
        self._attrs: dict[str, Any] = {}

    def attr(self, key: str, value: Any) -> Self:
        """Set an arbitrary HTML attribute."""
        self._attrs[key] = value
        return self

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _render(self, context: HueContext) -> Component:
        all_attrs: dict[str, Any] = {**self._attrs}

        # Merge base html attrs (id, aria-*, Alpine)
        all_attrs.update(self._get_base_html_attrs())

        # Add class if set
        class_ = self._get_prop("class_")
        if class_:
            all_attrs["class_"] = class_

        # TagWithProps (void elements like <input>, <br>) have no children
        if issubclass(self._tag_class, Tag):
            return self._tag_class(*self._children, **all_attrs)

        return self._tag_class(**all_attrs)


# ------------------------------------------------------------------
# Mixins
# ------------------------------------------------------------------


class _AlpineAjaxRequestMixin:
    """
    Alpine AJAX attributes for request-originating elements (``<form>``,
    ``<a>``).  These control *where* an AJAX response is merged and how
    the request is configured.
    """

    _props: dict[str, Any]  # provided by ChainableComponent

    def x_target(self, value: str) -> Self:
        """Target element(s) to update with the AJAX response."""
        self._props["x-target"] = value
        return self  # type: ignore[return-value]

    def x_target_422(self, value: str) -> Self:
        self._props["x-target.422"] = value
        return self  # type: ignore[return-value]

    def x_target_4xx(self, value: str) -> Self:
        self._props["x-target.4xx"] = value
        return self  # type: ignore[return-value]

    def x_target_back(self, value: str) -> Self:
        self._props["x-target.back"] = value
        return self  # type: ignore[return-value]

    def x_target_away(self, value: str) -> Self:
        self._props["x-target.away"] = value
        return self  # type: ignore[return-value]

    def x_target_error(self, value: str) -> Self:
        self._props["x-target.error"] = value
        return self  # type: ignore[return-value]

    def x_target_top(self, value: str) -> Self:
        self._props["x-target.top"] = value
        return self  # type: ignore[return-value]

    def x_target_none(self) -> Self:
        self._props["x-target.none"] = True
        return self  # type: ignore[return-value]

    def x_target_dynamic(self, value: str) -> Self:
        self._props["x-target:dynamic"] = value
        return self  # type: ignore[return-value]

    def x_target_replace(self, value: str) -> Self:
        self._props["x-target.replace"] = value
        return self  # type: ignore[return-value]

    def x_target_push(self, value: str) -> Self:
        self._props["x-target.push"] = value
        return self  # type: ignore[return-value]

    def x_headers(self, value: dict[str, str]) -> Self:
        """Add extra headers to the AJAX request."""
        self._props["x-headers"] = value
        return self  # type: ignore[return-value]

    def x_sync(self, value: bool = True) -> Self:
        self._props["x-sync"] = value
        return self  # type: ignore[return-value]


class _AlpineModelMixin:
    """``x-model`` for form controls (``<input>``, ``<select>``,
    ``<textarea>``)."""

    _props: dict[str, Any]

    def x_model(self, value: str) -> Self:
        """Two-way bind this control to Alpine data."""
        self._props["x-model"] = value
        return self  # type: ignore[return-value]


# ------------------------------------------------------------------
# Specialized elements with typed attribute methods
# ------------------------------------------------------------------


class FormElement(_AlpineAjaxRequestMixin, Element):
    """Chainable ``<form>`` with typed methods for common form attributes."""

    def method(self, value: Literal["GET", "POST"]) -> Self:
        return self.attr("method", value)

    def action(self, value: str) -> Self:
        return self.attr("action", value)

    def enctype(
        self,
        value: Literal[
            "application/x-www-form-urlencoded",
            "multipart/form-data",
            "text/plain",
        ],
    ) -> Self:
        return self.attr("enctype", value)

    def novalidate(self, value: bool = True) -> Self:
        return self.attr("novalidate", value)


class AnchorElement(_AlpineAjaxRequestMixin, Element):
    """Chainable ``<a>`` with typed methods for common anchor attributes."""

    def href(self, value: str) -> Self:
        return self.attr("href", value)

    def target(
        self, value: Literal["_self", "_blank", "_parent", "_top"]
    ) -> Self:
        return self.attr("target", value)

    def rel(self, value: str) -> Self:
        return self.attr("rel", value)


class ImgElement(Element):
    """Chainable ``<img>`` with typed methods for common image attributes."""

    def src(self, value: str) -> Self:
        return self.attr("src", value)

    def alt(self, value: str) -> Self:
        return self.attr("alt", value)

    def width(self, value: int | str) -> Self:
        return self.attr("width", value)

    def height(self, value: int | str) -> Self:
        return self.attr("height", value)

    def loading(self, value: Literal["lazy", "eager"]) -> Self:
        return self.attr("loading", value)


class ButtonElement(Element):
    """Chainable ``<button>`` with typed methods for common button attributes."""

    def type(self, value: Literal["button", "submit", "reset"]) -> Self:  # noqa: A003
        return self.attr("type", value)

    def disabled(self, value: bool = True) -> Self:
        return self.attr("disabled", value)

    def name(self, value: str) -> Self:
        return self.attr("name", value)

    def value(self, value: str) -> Self:
        return self.attr("value", value)

    def formnoajax(self, value: bool = True) -> Self:
        """Disable AJAX for this submit button."""
        self._props["formnoajax"] = value
        return self


class InputElement(_AlpineModelMixin, Element):
    """Chainable ``<input>`` with typed methods for common input attributes."""

    def input_type(self, value: str) -> Self:
        return self.attr("type", value)

    def name(self, value: str) -> Self:
        return self.attr("name", value)

    def placeholder(self, value: str) -> Self:
        return self.attr("placeholder", value)

    def disabled(self, value: bool = True) -> Self:
        return self.attr("disabled", value)

    def required(self, value: bool = True) -> Self:
        return self.attr("required", value)

    def value(self, value: str) -> Self:
        return self.attr("value", value)


class SelectElement(_AlpineModelMixin, Element):
    """Chainable ``<select>`` with typed methods for common select attributes."""

    def name(self, value: str) -> Self:
        return self.attr("name", value)

    def multiple(self, value: bool = True) -> Self:
        return self.attr("multiple", value)

    def disabled(self, value: bool = True) -> Self:
        return self.attr("disabled", value)

    def required(self, value: bool = True) -> Self:
        return self.attr("required", value)


class TextareaElement(_AlpineModelMixin, Element):
    """Chainable ``<textarea>`` with typed methods for common textarea attributes."""

    def name(self, value: str) -> Self:
        return self.attr("name", value)

    def rows(self, value: int) -> Self:
        return self.attr("rows", value)

    def cols(self, value: int) -> Self:
        return self.attr("cols", value)

    def placeholder(self, value: str) -> Self:
        return self.attr("placeholder", value)

    def disabled(self, value: bool = True) -> Self:
        return self.attr("disabled", value)

    def required(self, value: bool = True) -> Self:
        return self.attr("required", value)


class LabelElement(Element):
    """Chainable ``<label>`` with typed methods for common label attributes."""

    def for_(self, value: str) -> Self:
        return self.attr("for_", value)


# Maps htmy tag class names to specialized Element subclasses.
SPECIALIZED_ELEMENTS: dict[str, type[Element]] = {
    "form": FormElement,
    "a": AnchorElement,
    "img": ImgElement,
    "button": ButtonElement,
    "input_": InputElement,
    "select": SelectElement,
    "textarea": TextareaElement,
    "label": LabelElement,
}
