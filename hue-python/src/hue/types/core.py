from abc import ABC, abstractmethod
from dataclasses import dataclass, fields
from typing import TYPE_CHECKING, Any, Literal, Protocol

from htmy import Component as HTMYComponent
from htmy import ComponentType as HTMYComponentType

from hue.types.html import AriaAtomic, AriaLive, AriaRole

if TYPE_CHECKING:
    from hue.context import HueContext


class Undefined(Protocol):
    """
    Use Undefined to indicate that a component is not supposed to be rendered.
    """

    def htmy(self, *args, **kwargs) -> "Component":
        return ""


type Component = HTMYComponent | Undefined
type ComponentType = HTMYComponentType | Undefined


@dataclass(slots=True, frozen=True, kw_only=True)
class BaseProps:
    # HTMX props
    hx_get: str | None = None
    hx_post: str | None = None
    hx_swap: str | None = None
    hx_target: str | None = None
    hx_trigger: str | None = None
    hx_on: str | None = None
    hx_push_url: str | None = None
    hx_select: str | None = None
    hx_vals: str | None = None
    hx_confirm: str | None = None
    hx_indicator: str | None = None
    hx_include: str | None = None

    # Aria props
    aria_label: str | None = None
    aria_hidden: Literal["true", "false"] | None = None
    aria_expanded: str | None = None
    aria_controls: str | None = None
    aria_live: AriaLive = None
    aria_atomic: AriaAtomic = None
    aria_describedby: str | None = None
    role: AriaRole = None

    # Alpine props
    x_show: str | None = None
    x_data: dict[str, Any] | None = None
    x_init: str | None = None
    x_bind: str | None = None
    x_on_click: str | None = None
    x_on_click__outside: str | None = None
    x_transition_enter: str | None = None
    x_transition_enter_start: str | None = None
    x_transition_enter_end: str | None = None
    x_transition_leave: str | None = None
    x_transition_leave_start: str | None = None
    x_transition_leave_end: str | None = None


@dataclass(slots=True, frozen=True, kw_only=True)
class BaseComponent(ABC, BaseProps):
    class_: str | None = None

    @abstractmethod
    def htmy(self, context: "HueContext", **kwargs: Any) -> Component: ...

    @property
    def base_props(self) -> dict[str, Any]:
        """
        Get the base props of the component. Note: The `class_` field is not included.
        because it is a special field that is handled by the `combine_classes` util.
        """
        return {
            field.name: getattr(self, field.name)
            for field in fields(BaseComponent)
            if hasattr(self, field.name) and not field.name == "class_"
        }

    @staticmethod
    def ensure_iterable_children(
        value: ComponentType | tuple[ComponentType, ...],
    ) -> tuple[ComponentType, ...]:
        """
        Ensure that the value is converted to an iterable
        """

        return (value,) if not isinstance(value, tuple) else value
