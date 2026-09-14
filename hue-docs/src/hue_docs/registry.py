"""
Turn a discovered component into showcase data, fully automatically.

The preview content comes from the component's example() classmethod, the
variant grids from its introspected Literal axes, and the usage snippet from the
source of example(). There are no per-component files to maintain.
"""

from __future__ import annotations

import ast
import inspect
import textwrap
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from hue.types.core import ComponentType

from hue_docs.discovery import Axis, ComponentDoc

Layout = Literal["row", "grid", "stack"]

# Enum axes with more values than this are passthrough-ish attributes (an
# input's autocomplete, say) rather than primary visual variants: trim their
# grid and sink them to the bottom of the playground so the useful props win.
_BIG_ENUM_THRESHOLD = 12

# Props worth keeping first when the playground has to be capped.
_AUTO_PROP_PRIORITY = (
    "variant",
    "size",
    "shape",
    "direction",
    "spacing",
    "align",
    "justify_content",
    "align_items",
)


@dataclass(frozen=True)
class Variant:
    """
    A single rendered example and the source that produced it.
    """

    label: str
    build: Callable[[], ComponentType]
    code: str


@dataclass(frozen=True)
class Showcase:
    title: str
    variants: list[Variant]
    description: str | None = None
    layout: Layout = "grid"


def format_call(axis: Axis, value: Any, *, omit_default: bool = True) -> str:
    """
    The modifier call that sets axis to value. By default nothing is emitted when
    value is already the component's default, so snippets stay minimal.
    """
    if omit_default and value == axis.default:
        return ""
    if isinstance(value, bool):
        return f".{axis.method}()" if value else f".{axis.method}(False)"
    if isinstance(value, str):
        return f'.{axis.method}("{value}")'
    return f".{axis.method}({value!r})"


def example_instance(doc: ComponentDoc) -> ComponentType:
    """
    A fresh representative instance from the component's example().
    """
    return doc.cls.example()  # type: ignore[attr-defined]


def example_body(doc: ComponentDoc) -> ast.expr | None:
    """
    The single returned expression of example(), or None when the body is not
    exactly one return statement (which the test suite enforces, since anything
    else cannot be shown as a self-contained snippet).
    """
    factory = getattr(doc.cls, "example", None)
    if factory is None:
        return None
    try:
        source = textwrap.dedent(inspect.getsource(factory))
        tree = ast.parse(source)
    except (OSError, TypeError, SyntaxError):
        return None

    function = tree.body[0]
    if not isinstance(function, ast.FunctionDef):
        return None
    body = function.body
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
    ):
        body = body[1:]  # docstring
    if len(body) == 1 and isinstance(body[0], ast.Return) and body[0].value is not None:
        return body[0].value
    return None


def example_code(doc: ComponentDoc) -> str | None:
    """
    The body of example() as a usage snippet, e.g. Button().content("Save").

    None when example() does not build the component through cls(...), such as
    Icon, whose example binds an icon source first.
    """
    factory = getattr(doc.cls, "example", None)
    expr = example_body(doc)
    if factory is None or expr is None:
        return None
    source = textwrap.dedent(inspect.getsource(factory))
    segment = ast.get_source_segment(source, expr)
    if segment is None or "cls(" not in segment:
        return None
    # Chains are often wrapped in parentheses across lines; keep the chain itself.
    code = textwrap.dedent(segment).strip()
    if code.startswith("(") and code.endswith(")"):
        code = textwrap.dedent(code[1:-1]).strip()
    return code.replace("cls(", f"{doc.name}(")


def playground_axes(doc: ComponentDoc) -> list[Axis]:
    """
    Discovered axes ordered so the most useful survive the playground's cap.
    """

    def rank(axis: Axis) -> tuple[bool, bool, int, str]:
        big = axis.kind == "enum" and len(axis.values) > _BIG_ENUM_THRESHOLD
        try:
            named = _AUTO_PROP_PRIORITY.index(axis.method)
        except ValueError:
            named = len(_AUTO_PROP_PRIORITY)
        # Small named enums, then other small enums, then bools, then big enums.
        return (big, axis.kind == "bool", named, axis.method)

    return sorted(doc.axes, key=rank)


def auto_showcases(doc: ComponentDoc) -> list[Showcase]:
    """
    One grid per enum axis (bool toggles are covered by the playground).
    """
    showcases: list[Showcase] = []
    for axis in doc.axes:
        if axis.kind != "enum":
            continue

        values = list(axis.values)
        description: str | None = None
        if len(values) > _BIG_ENUM_THRESHOLD:
            description = f"Showing {_BIG_ENUM_THRESHOLD} of {len(values)} values."
            values = values[:_BIG_ENUM_THRESHOLD]

        variants: list[Variant] = []
        for value in values:

            def make(value: Any = value, method: str = axis.method) -> ComponentType:
                instance = example_instance(doc)
                getattr(instance, method)(value)
                return instance

            code = f"{doc.name}(){format_call(axis, value, omit_default=False)}"
            variants.append(Variant(label=str(value), build=make, code=code))

        showcases.append(
            Showcase(
                title=axis.method.replace("_", " ").title(),
                variants=variants,
                description=description,
                layout="stack",
            )
        )
    return showcases
