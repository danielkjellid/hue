from typing import TypedDict

from htmy import Context

from hue.types.core import Component, ComponentType


class HueContextArgs[T_Request](TypedDict):
    request: T_Request
    csrf_token: str


class HueContext[T_Request]:
    def __init__(
        self, *children: ComponentType, **kwargs: HueContextArgs[T_Request]
    ) -> None:
        self._children = children
        self.request = kwargs["request"]
        self.csrf_token = kwargs["csrf_token"]

    def htmy_context(self) -> Context:
        return {HueContext: self}

    def htmy(self, context: Context) -> Component:
        return self._children

    @classmethod
    def from_context(cls, context: Context) -> "HueContext":
        hue_context = context[cls]
        if isinstance(hue_context, HueContext):
            return hue_context

        raise TypeError("Invalid hue context.")
