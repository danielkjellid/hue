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
from hue.ui.base import ChainableComponent
from hue.ui.form import FormControl

from hue_docs.discovery import Axis, ComponentDoc

Layout = Literal["row", "grid", "stack"]

# Enum axes with more values than this are passthrough attributes (an input's
# autocomplete, say) rather than primary visual variants: they get no grid at
# all, and sink to the bottom of the playground so the useful props win.
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


def _make_unique(component: ComponentType, token: str) -> None:
    """
    Give one preview an identity of its own.

    Every variant and every playground combination is in the document at the
    same time, so a component that names its own id from a prop collides with
    its own copies - and a label points at the first match in the document,
    not the nearest one. A form control's name is what its id and its grouping
    are both built from, so that is the thing to vary.
    """
    if isinstance(component, FormControl):
        component.name(token)
    elif isinstance(component, ChainableComponent):
        component.id(token)


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
    # Chains are often wrapped in parentheses across lines; keep the chain
    # itself.
    code = textwrap.dedent(segment).strip()
    if code.startswith("(") and code.endswith(")"):
        code = textwrap.dedent(code[1:-1]).strip()

    # A wrapped chain comes back with its first line at column zero and the
    # rest still carrying the indentation they had inside the method, which
    # dedent cannot see as common. Measure the continuation on its own and put
    # it back one step in, which is how the chain was written.
    first, _, rest = code.partition("\n")
    if rest:
        code = first + "\n" + textwrap.indent(textwrap.dedent(rest).rstrip(), "    ")
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

    Passthrough attributes get none. An autocomplete grid is a row of inputs
    that all look identical under a heading of values most of them should
    never be given - PasswordInput().autocomplete("address-line2") is not an
    example of anything. The playground keeps them, at the bottom, where the
    full list is one dropdown rather than twelve cards.
    """
    showcases: list[Showcase] = []
    for axis in doc.axes:
        if axis.kind != "enum" or len(axis.values) > _BIG_ENUM_THRESHOLD:
            continue

        values = list(axis.values)

        variants: list[Variant] = []
        for value in values:

            def make(
                value: Any = value,
                method: str = axis.method,
                index: int = len(variants),
            ) -> ComponentType:
                instance = example_instance(doc)
                getattr(instance, method)(value)
                # Every card is on the page at once, so a shared id would
                # point every label at the first one.
                _make_unique(instance, f"{doc.slug}-{method}-{index}")
                return instance

            code = f"{doc.name}(){format_call(axis, value, omit_default=False)}"
            variants.append(Variant(label=str(value), build=make, code=code))

        showcases.append(
            Showcase(
                title=axis.method.replace("_", " ").title(),
                variants=variants,
                layout="stack",
            )
        )
    return showcases
