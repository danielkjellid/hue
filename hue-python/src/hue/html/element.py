from __future__ import annotations

from typing import Any, Literal

from htmy.core import Tag, TagWithProps
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component, ComponentType
from hue.ui.base import AlpineModelMixin, ChainableComponent


class Element(ChainableComponent):
    """
    A chainable wrapper around any htmy Tag.

    Provides the shared modifiers (class_, id, ARIA, Alpine) plus attr() for
    arbitrary HTML attributes. Not usually instantiated directly; use the
    factories on the hue.html module.
    """

    def __init__(self, tag_class: type[Tag] | type[TagWithProps]) -> None:
        super().__init__()
        self._tag_class = tag_class

    @property
    def _is_void(self) -> bool:
        # htmy models void elements (input, br, img, ...) as TagWithProps.
        return not issubclass(self._tag_class, Tag)

    def attr(self, key: str, value: Any) -> Self:
        """
        Set an arbitrary HTML attribute.
        """
        self._attrs[key] = value
        return self

    def content(self, *children: ComponentType) -> Self:
        if children and self._is_void:
            tag = self._tag_class.__name__.rstrip("_")
            raise TypeError(f"<{tag}> is a void element and cannot have children.")
        return super().content(*children)

    def _render(self, context: HueContext) -> Component:
        attrs: dict[str, Any] = self._get_base_html_attrs()

        if class_ := self._get_prop("class_"):
            attrs["class_"] = class_

        if self._is_void:
            return self._tag_class(**attrs)
        return self._tag_class(*self._children, **attrs)


# ------------------------------------------------------------------
# Mixins
# ------------------------------------------------------------------


class _AlpineAjaxRequestMixin:
    """
    Alpine AJAX attributes for request-originating elements (form, a). These
    control where an AJAX response is merged and how the request is configured.
    """

    _attrs: dict[str, Any]  # provided by ChainableComponent

    def x_target(self, value: str) -> Self:
        """
        Target element(s) to update with the AJAX response.
        """
        self._attrs["x-target"] = value
        return self

    def x_target_422(self, value: str) -> Self:
        self._attrs["x-target.422"] = value
        return self

    def x_target_4xx(self, value: str) -> Self:
        self._attrs["x-target.4xx"] = value
        return self

    def x_target_back(self, value: str) -> Self:
        self._attrs["x-target.back"] = value
        return self

    def x_target_away(self, value: str) -> Self:
        self._attrs["x-target.away"] = value
        return self

    def x_target_error(self, value: str) -> Self:
        self._attrs["x-target.error"] = value
        return self

    def x_target_top(self, value: str) -> Self:
        self._attrs["x-target.top"] = value
        return self

    def x_target_none(self) -> Self:
        self._attrs["x-target.none"] = True
        return self

    def x_target_dynamic(self, value: str) -> Self:
        self._attrs["x-target:dynamic"] = value
        return self

    def x_target_replace(self, value: str) -> Self:
        self._attrs["x-target.replace"] = value
        return self

    def x_target_push(self, value: str) -> Self:
        self._attrs["x-target.push"] = value
        return self

    def x_headers(self, value: dict[str, str]) -> Self:
        """
        Add extra headers to the AJAX request.
        """
        self._attrs["x-headers"] = value
        return self

    def x_sync(self, value: bool = True) -> Self:
        self._attrs["x-sync"] = value or None
        return self


class _FormControlElement(AlpineModelMixin, Element):
    """
    Attributes every native form control shares (input, select, textarea).
    """

    def name(self, value: str) -> Self:
        return self.attr("name", value)

    def disabled(self, value: bool = True) -> Self:
        return self.attr("disabled", value or None)

    def required(self, value: bool = True) -> Self:
        return self.attr("required", value or None)


# ------------------------------------------------------------------
# Specialised elements with typed attribute methods
# ------------------------------------------------------------------


class FormElement(_AlpineAjaxRequestMixin, Element):
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
        return self.attr("novalidate", value or None)


class AnchorElement(_AlpineAjaxRequestMixin, Element):
    def href(self, value: str) -> Self:
        return self.attr("href", value)

    def target(self, value: Literal["_self", "_blank", "_parent", "_top"]) -> Self:
        return self.attr("target", value)

    def rel(self, value: str) -> Self:
        return self.attr("rel", value)


class ImgElement(Element):
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
    def type(self, value: Literal["button", "submit", "reset"]) -> Self:
        return self.attr("type", value)

    def disabled(self, value: bool = True) -> Self:
        return self.attr("disabled", value or None)

    def name(self, value: str) -> Self:
        return self.attr("name", value)

    def value(self, value: str) -> Self:
        return self.attr("value", value)

    def formnoajax(self, value: bool = True) -> Self:
        """
        Disable AJAX for this submit button.
        """
        return self.attr("formnoajax", value or None)


class InputElement(_FormControlElement):
    def input_type(self, value: str) -> Self:
        return self.attr("type", value)

    def placeholder(self, value: str) -> Self:
        return self.attr("placeholder", value)

    def value(self, value: str) -> Self:
        return self.attr("value", value)


class SelectElement(_FormControlElement):
    def multiple(self, value: bool = True) -> Self:
        return self.attr("multiple", value or None)


class TextareaElement(_FormControlElement):
    def rows(self, value: int) -> Self:
        return self.attr("rows", value)

    def cols(self, value: int) -> Self:
        return self.attr("cols", value)

    def placeholder(self, value: str) -> Self:
        return self.attr("placeholder", value)


class LabelElement(Element):
    def for_(self, value: str) -> Self:
        return self.attr("for_", value)


# Maps htmy tag names to the specialised Element subclass.
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
