"""
A component's own modifiers, read off the class rather than written down.

Everything ChainableComponent and its mixins give every component (class_,
the aria and Alpine helpers, x_model, on_click) is left out, so each table
holds only what is particular to its component.
"""

from __future__ import annotations

import ast
import inspect
import textwrap
import typing
from dataclasses import dataclass
from typing import Any, Literal

from hue.ui.base import (
    AlpineModelMixin,
    ChainableComponent,
    Clickable,
    FormElementMixin,
)

# Public methods that are htmy's hooks rather than modifiers a reader calls.
_HOOKS = frozenset({"htmy", "htmy_context"})
_SKIPPED_CLASSES = (ChainableComponent, AlpineModelMixin, FormElementMixin, Clickable)
_SHARED = frozenset(name for base in _SKIPPED_CLASSES for name in vars(base))
_SHOWN_VALUES = 8


@dataclass(frozen=True)
class Prop:
    name: str
    signature: str
    default: str | None
    doc: str


def _type(annotation: Any, raw: str) -> str:
    """
    A parameter's type as a reader wants it: the values of a Literal alias
    spelled out, anything else as the source wrote it.
    """
    resolved = annotation
    while isinstance(resolved, typing.TypeAliasType):
        resolved = resolved.__value__
    if typing.get_origin(resolved) is Literal:
        values = [repr(value) for value in typing.get_args(resolved)]
        if len(values) > _SHOWN_VALUES:
            # Autocomplete's forty-odd tokens would bury the table.
            more = len(values) - _SHOWN_VALUES
            values = [*values[:_SHOWN_VALUES], f"... {more} more"]
        return " | ".join(values)
    return raw


def _signature(func: Any) -> str:
    raw = inspect.signature(func)
    try:
        resolved = inspect.signature(func, eval_str=True)
    except (NameError, TypeError):
        resolved = raw
    parts = []
    keyword_only = False
    for name, param in list(raw.parameters.items())[1:]:
        if param.kind is param.KEYWORD_ONLY and not keyword_only:
            parts.append("*")
            keyword_only = True
        text = name
        if param.kind is param.VAR_POSITIONAL:
            text = f"*{name}"
        if param.annotation is not param.empty:
            annotation = resolved.parameters[name].annotation
            text += f": {_type(annotation, str(param.annotation))}"
        if param.default is not param.empty:
            text += f" = {param.default!r}"
        parts.append(text)
    return f"{func.__name__}({', '.join(parts)})"


def _defaults(cls: type[ChainableComponent]) -> dict[str, Any]:
    """
    Read from the literal default of every _get_prop("name", literal) in
    _render, then whatever the constructor sets, which is how EmailInput gets
    its autocomplete. Every _render in the class's bases is read too, base
    first, since an override such as PasswordInput's hands the rest to super().
    """
    defaults: dict[str, Any] = {}
    for base in reversed(cls.__mro__):
        render = vars(base).get("_render")
        if render is None:
            continue
        try:
            source = textwrap.dedent(inspect.getsource(render))
        except (OSError, TypeError):
            continue
        for node in ast.walk(ast.parse(source)):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "_get_prop"
                and len(node.args) == 2
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[1], ast.Constant)
            ):
                defaults[str(node.args[0].value)] = node.args[1].value
    try:
        defaults.update(cls()._props)
    except TypeError:
        pass
    return defaults


def _first_paragraph(func: Any) -> str:
    doc = inspect.getdoc(func) or ""
    return " ".join(doc.split("\n\n")[0].split())


def props_of(cls: type[ChainableComponent]) -> list[Prop]:
    """
    Every public modifier the component and its own bases define, nearest
    class first, each once.
    """
    defaults = _defaults(cls)
    seen: set[str] = set()
    props = []
    for klass in cls.__mro__:
        if klass in _SKIPPED_CLASSES or not issubclass(klass, ChainableComponent):
            continue
        for name, member in vars(klass).items():
            if (
                name.startswith("_")
                or name in seen
                or name in _SHARED
                or name in _HOOKS
                or name == "example"
                or not inspect.isfunction(member)
            ):
                continue
            seen.add(name)
            default = defaults.get(name)
            props.append(
                Prop(
                    name=name,
                    signature=_signature(member),
                    default=None if default is None else repr(default),
                    doc=_first_paragraph(member),
                )
            )
    return props
