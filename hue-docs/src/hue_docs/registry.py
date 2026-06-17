"""Turn a discovered component into showcase data — fully automatically.

Everything here is derived from the component itself:

* the preview content comes from the component's ``example()`` classmethod
  (falling back to a bare ``Cls()``),
* the variant grids come from its introspected ``Literal`` axes, and
* the usage snippet comes from the source of ``example()``.

There are no per-component files to maintain — a new component is documented the
moment it exists.
"""

from __future__ import annotations

import ast
import inspect
import textwrap
from dataclasses import dataclass
from typing import Any, Callable, Literal

from hue.types.core import ComponentType

from hue_docs.discovery import Axis, ComponentDoc

Layout = Literal["row", "grid", "stack"]

# Enum axes with more values than this are passthrough-ish attributes (e.g. an
# input's ``autocomplete``) rather than primary visual variants: trim their grid
# and sink them to the bottom of the playground so the useful props win.
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
    """A single rendered example and the source that produced it."""

    label: str
    build: Callable[[], ComponentType]
    code: str


@dataclass(frozen=True)
class Showcase:
    title: str
    variants: list[Variant]
    description: str | None = None
    layout: Layout = "grid"


def _format_call(method: str, value: Any) -> str:
    if isinstance(value, bool):
        return f".{method}()" if value else ""
    if isinstance(value, str):
        return f'.{method}("{value}")'
    return f".{method}({value!r})"


def example_instance(doc: ComponentDoc) -> ComponentType:
    """A fresh representative instance: ``Cls.example()`` if defined, else ``Cls()``."""
    factory = getattr(doc.cls, "example", None)
    if callable(factory):
        return factory()
    return doc.cls()


def example_code(doc: ComponentDoc) -> str | None:
    """The body of ``example()`` as a one-line snippet, e.g. ``Button().content("…")``.

    Returns ``None`` when there is no ``example()`` or it isn't a simple
    ``return cls()...`` chain we can render as the canonical usage.
    """
    factory = getattr(doc.cls, "example", None)
    if factory is None:
        return None
    try:
        source = textwrap.dedent(inspect.getsource(factory))
        tree = ast.parse(source)
    except (OSError, TypeError, SyntaxError):
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.Return) and node.value is not None:
            expr = ast.unparse(node.value)
            if "cls(" not in expr:
                return None
            return expr.replace("cls(", f"{doc.name}(")
    return None


def playground_axes(doc: ComponentDoc) -> list[Axis]:
    """Discovered axes ordered so the most useful survive the playground's cap."""

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
    """One grid per enum axis (bool toggles are covered by the playground)."""
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

            code = f"{doc.name}(){_format_call(axis.method, value)}"
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
