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
class AlpineAjaxProps:
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

    # Alpine AJAX props
    x_target: str | None = None
    x_target__422: str | None = None
    x_target__4xx: str | None = None
    x_target__back: str | None = None
    x_target__away: str | None = None
    x_target__error: str | None = None
    x_target__top: str | None = None
    x_target__none: str | None = None
    x_target__dynamic: str | None = None
    x_target__replace: str | None = None
    x_target__push: str | None = None

    formnoajax: bool = False

    x_headers: dict[str, str] | None = None
    x_merge: (
        Literal[
            "before",
            "replace",
            "update",
            "prepend",
            "append",
            "after",
        ]
        | None
    ) = None

    x_autofocus: bool = False
    x_sync: bool = False

    ajax__before: str | None = None
    ajax__send: str | None = None
    ajax__redirect: str | None = None
    ajax__success: str | None = None
    ajax__error: str | None = None
    ajax__sent: str | None = None
    ajax__missing: str | None = None
    ajax__merge: str | None = None
    ajax__merged: str | None = None
    ajax__after: str | None = None

    @property
    def identifier(self) -> str:
        return "x_"

    @staticmethod
    def to_html(modifier: str) -> str:
        mapping = {
            "x_show": "x-show",
            "x_data": "x-data",
            "x_init": "x-init",
            "x_bind": "x-bind",
            "x_on__click": "x-on:click",
            "x_on__click__outside": "x-on:click.outside",
            "x_transition__enter": "x-transition:enter",
            "x_transition__enter_start": "x-transition:enter.start",
            "x_transition__enter_end": "x-transition:enter.end",
            "x_transition__leave": "x-transition:leave",
            "x_transition__leave_start": "x-transition:leave.start",
            "x_transition__leave_end": "x-transition:leave.end",
            "x_target": "x-target",
            "x_target__422": "x-target.422",
            "x_target__4xx": "x-target.4xx",
            "x_target__back": "x-target.back",
            "x_target__away": "x-target.away",
            "x_target__error": "x-target.error",
            "x_target__top": "x-target.top",
            "x_target__none": "x-target.none",
            "x_target__dynamic": "x-target.dynamic",
            "x_target__replace": "x-target.replace",
            "x_target__push": "x-target.push",
            "formnoajax": "formnoajax",
            "x_headers": "x-headers",
            "x_merge": "x-merge",
            "x_autofocus": "x-autofocus",
            "x_sync": "x-sync",
            "ajax__before": "@ajax.before",
            "ajax__send": "@ajax.send",
            "ajax__redirect": "@ajax.redirect",
            "ajax__success": "@ajax.success",
            "ajax__error": "@ajax.error",
            "ajax__sent": "@ajax.sent",
            "ajax__missing": "@ajax.missing",
            "ajax__merge": "@ajax.merge",
            "ajax__merged": "@ajax.merged",
            "ajax__after": "@ajax.after",
        }
        return mapping[modifier]


@dataclass(slots=True, frozen=True, kw_only=True)
class BaseProps(AlpineAjaxProps):
    # Aria props
    aria_label: str | None = None
    aria_hidden: Literal["true", "false"] | None = None
    aria_expanded: str | None = None
    aria_controls: str | None = None
    aria_live: AriaLive = None
    aria_atomic: AriaAtomic = None
    aria_describedby: str | None = None
    role: AriaRole = None


@dataclass(slots=True, frozen=True, kw_only=True)
class BaseComponent(ABC, BaseProps):
    class_: str | None = None

    @abstractmethod
    def htmy(self, context: "HueContext", **kwargs: Any) -> Component: ...

    @property
    def base_props(self) -> dict[str, Any]:
        """
        Get the base props of the component. Note: The `class_` field is not included as
        its often handled on a component basis.
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
