from typing import NotRequired, TypedDict, Unpack

from htmy import Context, Formatter

from hue.exceptions import MissingHueContextError
from hue.formats import Formats
from hue.shortcuts import ShortcutRegistry
from hue.types.core import Component, ComponentType

_hue_formatter = Formatter()


class HueContextArgs[T_Request](TypedDict):
    request: T_Request
    csrf_token: str
    # How dates and the like are written out. ISO 8601 when not given.
    formats: NotRequired[Formats]
    # The app's keyboard shortcuts, bound on every page and shown by the
    # palettes and menus that list them. None for an app without any.
    shortcuts: NotRequired[type[ShortcutRegistry] | None]


class HueContext[T_Request]:
    def __init__(
        self, *children: ComponentType, **kwargs: Unpack[HueContextArgs[T_Request]]
    ) -> None:
        self._children = children
        self.request = kwargs["request"]
        self.csrf_token = kwargs["csrf_token"]
        self.formats = kwargs.get("formats", Formats())
        self.shortcuts = kwargs.get("shortcuts")

    def htmy_context(self) -> Context:
        return {HueContext: self, Formatter: _hue_formatter, Formats: self.formats}

    def htmy(self, context: Context) -> Component:
        return self._children

    @classmethod
    def from_context(cls, context: Context) -> "HueContext":
        hue_context = context.get(cls)
        if isinstance(hue_context, HueContext):
            return hue_context

        raise MissingHueContextError
