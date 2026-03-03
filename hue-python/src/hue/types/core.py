from dataclasses import dataclass
from typing import Any, ClassVar, Literal, Protocol

from htmy import Component as HTMYComponent
from htmy import ComponentType as HTMYComponentType


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
    x_on__click: str | None = None
    x_on__click__outside: str | None = None
    x_transition__enter: str | None = None
    x_transition__enter_start: str | None = None
    x_transition__enter_end: str | None = None
    x_transition__leave: str | None = None
    x_transition__leave_start: str | None = None
    x_transition__leave_end: str | None = None

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

    formnoajax: bool | None = None

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

    x_autofocus: bool | None = None
    x_sync: bool | None = None

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

    identifier: ClassVar[str] = "x_"

    # Directives where __ becomes : (e.g., x_bind__class → x-bind:class)
    _colon_directives: ClassVar[tuple[str, ...]] = ("x_bind", "x_on", "x_transition")

    @staticmethod
    def to_html(name: str) -> str:
        mapping = {
            "x_show": "x-show",
            "x_data": "x-data",
            "x_init": "x-init",
            "x_bind": "x-bind",
            "x_model": "x-model",
            "x_text": "x-text",
            "x_html": "x-html",
            "x_ref": "x-ref",
            "x_effect": "x-effect",
            "x_cloak": "x-cloak",
            "x_ignore": "x-ignore",
            "x_id": "x-id",
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

        # Check static mapping first
        if name in mapping:
            return mapping[name]

        # Handle dynamic directive patterns (x_bind__class → x-bind:class)
        for directive in AlpineAjaxProps._colon_directives:
            prefix = f"{directive}__"
            if name.startswith(prefix):
                base = directive.replace("_", "-")  # x_bind → x-bind
                rest = name[len(prefix) :]
                # Split remaining parts: first __ after directive is :, rest are .
                parts = rest.split("__")
                prop = parts[0].replace("_", "-")
                if len(parts) > 1:
                    modifiers = ".".join(p.replace("_", "-") for p in parts[1:])
                    return f"{base}:{prop}.{modifiers}"
                return f"{base}:{prop}"

        raise KeyError(f"Unknown Alpine/AJAX property: {name}")
